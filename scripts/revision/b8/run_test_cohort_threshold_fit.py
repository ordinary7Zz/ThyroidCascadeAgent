#!/usr/bin/env python3
"""B8：在每个外测队列自身上 q 分位定阈，并在同一 test 上评估（写入 cohorts_test_fit/）。"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def __revision_bootstrap() -> None:
    p = Path(__file__).resolve()
    for d in [p.parent, *p.parents]:
        if d.name == "revision" and (d / "_path_setup.py").is_file():
            spec = importlib.util.spec_from_file_location("_rev_path_setup", d / "_path_setup.py")
            mod = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(mod)
            mod.bootstrap(__file__)
            return
    raise RuntimeError(f"revision _path_setup.py not found above {__file__}")


__revision_bootstrap()

import argparse
import json

import repo_path

repo_path.install()

from pipeline.evaluate import _label_to_binary
from pipeline.revision.b8.abstention import (
    AbstentionThresholds,
    apply_abstention,
    fit_thresholds_quantile,
    fit_thresholds_split_quantile,
    flag_for_review,
    risk_coverage_curve,
    save_thresholds,
    summarize_abstention_by_group,
    _accuracy_on_retained,
)
from pipeline.revision.b8.calibration import calibration_from_results
from pipeline.revision.b8.plot_calibration import plot_reliability_diagram

COHORT_RESULTS: dict[str, str] = {
    "tn3k": "output/TN3K/pipeline_run/results.json",
    "tn5k": "output/TN5K/pipeline_run/results.json",
    "thyroidxl": "output/ThyroidXL/pipeline_run/results.json",
    "zjh8k": "output/ZJH-8K/pipeline_run/results.json",
    "ddti_cls": "output/DDTI_cls/pipeline_run/results.json",
    "ddti_seg": "output/DDTI_seg/pipeline_run/results.json",
    "pktn": "output/PKTN/pipeline_run/results.json",
    "rjh7k": "output/RJH-7K/pipeline_run/results.json",
}

# 送复核比例目标（约 5%–15% 带内，各队列略有差异）
DEFAULT_TARGET_FLAG_RATE: dict[str, float] = {
    "tn3k": 0.15,
    "tn5k": 0.125,
    "thyroidxl": 0.10,
    "zjh8k": 0.075,
    "ddti_cls": 0.05,
    "ddti_seg": 0.05,
    "pktn": 0.12,
    "rjh7k": 0.143,
}


def _accuracy_all(results: list[dict]) -> float | None:
    ok = n = 0
    for r in results:
        tb = _label_to_binary(r.get("true_label"))
        pb = _label_to_binary(r.get("final_label"))
        if tb is None or pb is None:
            continue
        n += 1
        if int(tb) == int(pb):
            ok += 1
    return ok / n if n else None


def _flag_rate_thresholds(data: list[dict], th: AbstentionThresholds) -> float:
    if not data:
        return 0.0
    n = sum(1 for r in data if flag_for_review(r, th))
    return n / len(data)


def _flag_rate_unified(data: list[dict], quantile: float) -> float:
    th = fit_thresholds_quantile(
        data,
        rule_subset="nhc",
        quantile=quantile,
        fitted_on="search",
    )
    return _flag_rate_thresholds(data, th)


def quantiles_for_target_flag_rate(
    data: list[dict],
    target_rate: float,
    *,
    n_grid: int = 72,
) -> tuple[float, float]:
    """二维网格：q_gt（熵）与 q_lt（margin/IoU 低尾）使送复核率最接近 target。"""
    target_rate = max(0.0, min(1.0, target_rate))
    best_q_gt, best_q_lt = 0.95, 0.05
    best_err = 1.0
    for i in range(n_grid + 1):
        q_gt = 0.50 + 0.49 * i / n_grid
        for j in range(n_grid + 1):
            q_lt = 0.01 + 0.49 * j / n_grid
            th = fit_thresholds_split_quantile(
                data,
                rule_subset="nhc",
                q_gt=q_gt,
                q_lt=q_lt,
                fitted_on="search",
            )
            rate = _flag_rate_thresholds(data, th)
            err = abs(rate - target_rate)
            if err < best_err:
                best_err = err
                best_q_gt, best_q_lt = q_gt, q_lt
    return best_q_gt, best_q_lt


def run_one(
    cohort: str,
    results_path: Path,
    out_dir: Path,
    quantile: float | None,
    target_flag_rate: float | None,
    n_grid: int = 72,
    *,
    abstention_eval_name: str = "abstention_eval.json",
    calibration_test_name: str = "calibration_test.json",
    results_flagged_name: str = "results_flagged.json",
    reliability_png_name: str = "reliability_test.png",
) -> dict:
    data = json.loads(results_path.read_text(encoding="utf-8"))
    q_gt: float | None = None
    q_lt: float | None = None
    if target_flag_rate is not None:
        q_gt, q_lt = quantiles_for_target_flag_rate(
            data, target_flag_rate, n_grid=n_grid
        )
        th = fit_thresholds_split_quantile(
            data,
            rule_subset="nhc",
            q_gt=q_gt,
            q_lt=q_lt,
            fitted_on=f"test_{cohort}",
        )
        quantile = None
    else:
        if quantile is None:
            quantile = 0.95
        th = fit_thresholds_quantile(
            data,
            rule_subset="nhc",
            quantile=quantile,
            fitted_on=f"test_{cohort}",
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    save_thresholds(out_dir / "abstention_thresholds.json", th)
    flagged = apply_abstention(data, th)
    cal = calibration_from_results(flagged, label_to_binary=_label_to_binary)
    curve = risk_coverage_curve(flagged)
    by_center = summarize_abstention_by_group(flagged, group_key="center_id")
    n_flagged = sum(1 for r in flagged if r.get("flagged_for_review"))
    acc_all = _accuracy_all(flagged)
    acc_retained = _accuracy_on_retained(flagged)
    payload = {
        "calibration": cal,
        "risk_coverage": curve,
        "by_center": by_center,
        "n_flagged": n_flagged,
        "n_total": len(flagged),
        "threshold_fitted_on": f"test_same_cohort_{cohort}",
        "quantile": quantile,
        "quantile_gt": q_gt,
        "quantile_lt": q_lt,
        "target_flag_rate": target_flag_rate,
    }
    (out_dir / abstention_eval_name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / calibration_test_name).write_text(
        json.dumps(cal, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / results_flagged_name).write_text(
        json.dumps(flagged, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    label = cohort.upper() if cohort != "ddti_cls" else "DDTI"
    plot_reliability_diagram(
        cal.get("bins", []),
        out_dir / reliability_png_name,
        title=f"{label}: Test calibration (per-cohort thresholds)",
    )
    pct = 100.0 * n_flagged / len(flagged) if flagged else 0.0
    return {
        "cohort": cohort,
        "n": len(flagged),
        "n_flagged": n_flagged,
        "ece": cal.get("ece"),
        "brier": cal.get("brier"),
        "flagged_pct": pct,
        "flagged_pct_1dp": round(pct, 1),
        "acc_all": acc_all,
        "acc_retained": acc_retained,
        "quantile": quantile,
        "quantile_gt": q_gt,
        "quantile_lt": q_lt,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Per-test-cohort B8 threshold fit + eval")
    parser.add_argument(
        "--cohort",
        choices=list(COHORT_RESULTS.keys()),
        help="单队列；省略则跑全部 BM 五队列",
    )
    parser.add_argument(
        "--quantile",
        type=float,
        default=None,
        help="固定分位阈；与 --target-flag-rate 互斥",
    )
    parser.add_argument(
        "--target-flag-rate",
        type=float,
        default=None,
        help="目标送复核比例（0–1）；对单队列生效",
    )
    parser.add_argument(
        "--use-default-targets",
        action="store_true",
        help="使用内置 per-cohort 目标（约 5%%–15%%）",
    )
    parser.add_argument(
        "--n-grid",
        type=int,
        default=72,
        help="目标送复核率搜索网格边长（越大越慢）",
    )
    parser.add_argument(
        "--out-root",
        type=Path,
        default=Path("output/b8/cohorts_test_fit"),
    )
    args = parser.parse_args()
    cohorts = [args.cohort] if args.cohort else list(COHORT_RESULTS.keys())
    summaries = []
    for c in cohorts:
        rel = COHORT_RESULTS[c]
        path = Path(rel)
        if not path.is_file():
            raise FileNotFoundError(path)
        tfr: float | None = None
        q: float | None = args.quantile
        if args.use_default_targets:
            tfr = DEFAULT_TARGET_FLAG_RATE[c]
            q = None
        elif args.target_flag_rate is not None:
            tfr = args.target_flag_rate
            q = None
        elif q is None:
            tfr = DEFAULT_TARGET_FLAG_RATE[c]
        print(f">>> {c}: {path}" + (f" target_flag={tfr:.1%}" if tfr else f" q={q}"))
        s = run_one(c, path, args.out_root / c, q, tfr, n_grid=args.n_grid)
        summaries.append(s)
        q_info = (
            f"q_gt={s['quantile_gt']:.4f} q_lt={s['quantile_lt']:.4f}"
            if s.get("quantile_gt") is not None
            else f"q={s['quantile']:.4f}"
        )
        ece_s = "---" if s["ece"] is None else f"{s['ece']:.4f}"
        brier_s = "---" if s["brier"] is None else f"{s['brier']:.4f}"
        print(
            f"    n={s['n']} flagged={s['n_flagged']} ({s['flagged_pct_1dp']:.1f}%) "
            f"{q_info} ECE={ece_s} Brier={brier_s}"
        )
    print("✓ done:", args.out_root)


if __name__ == "__main__":
    main()
