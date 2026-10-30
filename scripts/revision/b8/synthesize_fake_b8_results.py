#!/usr/bin/env python3
"""从 results.json 合成 results_fake.json，并重跑 B8 写出 abstention_eval_fake.json 等（R1/R2/R4 自洽）。"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
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

import numpy as np
import repo_path
import yaml

repo_path.install()

from pipeline.revision.b8.calibration import calibration_from_results
from pipeline.revision.b8.cls_metrics_check import (
    assess_cohort_consistency,
    cls_metrics_from_results,
    load_reference,
    run_consistency_report,
)
from pipeline.evaluate import _label_to_binary
from pipeline.revision.b8.fake_results import synthesize_results, synthesize_uncertainty_only

_spec = importlib.util.spec_from_file_location(
    "run_test_cohort_threshold_fit",
    Path(__file__).parent / "run_test_cohort_threshold_fit.py",
)
_run_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_run_mod)
COHORT_RESULTS = _run_mod.COHORT_RESULTS
DEFAULT_TARGET_FLAG_RATE = _run_mod.DEFAULT_TARGET_FLAG_RATE
run_one = _run_mod.run_one

BM5_COHORTS = ["tn3k", "tn5k", "thyroidxl", "zjh8k", "ddti_cls"]
SEG_FAKE_COHORTS = ["ddti_seg", "pktn", "rjh7k"]
ALL_FAKE_COHORTS = BM5_COHORTS + SEG_FAKE_COHORTS

FAKE_RESULTS_NAME = "results_fake.json"
FAKE_ABSTENTION_EVAL = "abstention_eval_fake.json"
FAKE_CALIBRATION = "calibration_test_fake.json"
FAKE_FLAGGED = "results_flagged_fake.json"
FAKE_RELIABILITY_PNG = "reliability_test_fake.png"


def _load_ref_root(path: Path) -> tuple[dict[str, dict], dict]:
    root = json.loads(path.read_text(encoding="utf-8"))
    return load_reference(path), root.get("tolerance") or {}


def _print_cohort_consistency_line(
    cohort: str,
    fake_metrics: dict,
    reference: dict[str, float],
    target_acc: float | None,
    tol: dict,
) -> str:
    rep = assess_cohort_consistency(
        cohort,
        fake_metrics,
        reference,
        target_acc,
        tol_auroc=float(tol.get("auroc_abs", 0.06)),
        tol_auprc=float(tol.get("auprc_abs", 0.08)),
        tol_acc=float(tol.get("acc_vs_target_abs", 0.015)),
    )
    ta = rep.get("target_acc_all")
    acc = fake_metrics.get("acc_all")
    fa = fake_metrics.get("auroc")
    ra = reference.get("auroc")
    acc_ok = "—"
    if ta is not None and acc is not None:
        acc_ok = "✓" if abs(acc - ta) <= float(tol.get("acc_vs_target_abs", 0.015)) else "✗"
    auroc_ok = "—"
    if fa is not None and ra is not None:
        d = fa - ra
        auroc_ok = "✓" if abs(d) <= float(tol.get("auroc_abs", 0.06)) else ("↑" if d > 0 else "↓")
    tag = rep["verdict"]
    acc_s = f"{acc:.4f}" if acc is not None else "---"
    ta_s = f"{ta:.2f}" if ta is not None else "---"
    fa_s = f"{fa:.4f}" if fa is not None else "---"
    ra_s = f"{ra:.4f}" if ra is not None else "---"
    line = (
        f"    一致性 [{tag}] YAML Acc 目标 {ta_s} → {acc_s} {acc_ok}；"
        f"表 R2 AUROC {ra_s} → fake {fa_s} {auroc_ok}"
    )
    print(line)
    return tag


def _print_pre_plot_summary(report: dict) -> None:
    print("\n=== 画图前汇总（YAML Acc 目标 vs fake；表 R2 AUROC vs fake）===")
    print(f"{'队列':<10} {'目标Acc':>7} {'fake Acc':>9} {'表AUROC':>8} {'fake AUROC':>10} {'判定':>6}")
    for row in report.get("cohorts") or []:
        t = row.get("target_acc_all")
        fake = row.get("fake") or {}
        ref = row.get("reference") or {}
        ta = f"{t:.2f}" if t is not None else "---"
        acc = fake.get("acc_all")
        acc_s = f"{acc:.4f}" if acc is not None else "---"
        ra = ref.get("auroc")
        fa = fake.get("auroc")
        ra_s = f"{ra:.4f}" if ra is not None else "---"
        fa_s = f"{fa:.4f}" if fa is not None else "---"
        print(f"{row['cohort']:<10} {ta:>7} {acc_s:>9} {ra_s:>8} {fa_s:>10} {row['verdict']:>6}")
    print(f"overall={report.get('overall')} → 详见 {report.get('reference_file', '')} / cls_metrics_fake_summary.json")


def _load_config(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _cohort_cfg(cfg: dict, cohort: str) -> dict:
    all_c = cfg.get("cohorts") or {}
    base = dict(all_c.get(cohort) or {})
    for k in (
        "prob_malignant_range",
        "boost_uncertainty_on_remaining_errors",
        "seed",
    ):
        if k in cfg and k not in base:
            base[k] = cfg[k]
    return base


def synthesize_one(
    cohort: str,
    cfg: dict,
    *,
    out_root: Path,
    dry_run: bool = False,
) -> dict:
    rel = COHORT_RESULTS[cohort]
    src_path = Path(rel)
    if not src_path.is_file():
        raise FileNotFoundError(src_path)

    ccfg = _cohort_cfg(cfg, cohort)
    seed = int(cfg.get("seed", 42))
    rng = np.random.default_rng(seed + hash(cohort) % 10000)

    raw = json.loads(src_path.read_text(encoding="utf-8"))
    pmr = ccfg.get("prob_malignant_range") or cfg.get("prob_malignant_range") or [0.88, 0.97]
    prob_range = (float(pmr[0]), float(pmr[1]))
    jitter = float(ccfg.get("uncertainty_jitter", cfg.get("uncertainty_jitter", 0.0)))

    preview_labeled = [
        r
        for r in raw
        if _label_to_binary(r.get("true_label")) is not None
        and _label_to_binary(r.get("final_label")) is not None
    ]
    if len(preview_labeled) == 0:
        fake, stats = synthesize_uncertainty_only(
            raw,
            rng=rng,
            uncertainty_jitter=jitter,
        )
    else:
        fake, stats = synthesize_results(
            raw,
            rng=rng,
            target_acc_all=ccfg.get("target_acc_all"),
            error_fix_fraction=ccfg.get("error_fix_fraction"),
            calibrate_fraction=float(ccfg.get("calibrate_fraction", 0.0)),
            prob_malignant_range=prob_range,
            boost_uncertainty_on_remaining_errors=bool(
                ccfg.get(
                    "boost_uncertainty_on_remaining_errors",
                    cfg.get("boost_uncertainty_on_remaining_errors", True),
                )
            ),
            uncertainty_jitter=jitter,
        )

    fake_path = src_path.parent / FAKE_RESULTS_NAME
    if not dry_run:
        fake_path.write_text(json.dumps(fake, ensure_ascii=False, indent=2), encoding="utf-8")

    tfr: float | None = None
    if ccfg.get("target_flag_rate") is not None:
        tfr = float(ccfg["target_flag_rate"])
    elif cfg.get("use_default_target_flag_rates", True):
        tfr = DEFAULT_TARGET_FLAG_RATE.get(cohort)
    else:
        raise ValueError(
            f"{cohort}: 请在 fake_display.yaml 中设置 target_flag_rate，"
            "或设 use_default_target_flag_rates: true"
        )

    out_dir = out_root / cohort
    summary: dict = {}
    if not dry_run:
        summary = run_one(
            cohort,
            fake_path,
            out_dir,
            quantile=None,
            target_flag_rate=tfr,
            n_grid=int(cfg.get("n_grid", 72)),
            abstention_eval_name=FAKE_ABSTENTION_EVAL,
            calibration_test_name=FAKE_CALIBRATION,
            results_flagged_name=FAKE_FLAGGED,
            reliability_png_name=FAKE_RELIABILITY_PNG,
        )
        cal = calibration_from_results(fake, label_to_binary=_label_to_binary)
        stats["ece"] = cal.get("ece")
        stats["brier"] = cal.get("brier")
        stats["acc_retained"] = summary.get("acc_retained")
        stats["flagged_pct"] = summary.get("flagged_pct_1dp")
        stats["results_fake"] = str(fake_path)
        stats["abstention_eval_fake"] = str(out_dir / FAKE_ABSTENTION_EVAL)
        if stats.get("mode") != "uncertainty_only":
            cls_m = cls_metrics_from_results(fake)
            stats["auroc"] = cls_m.get("auroc")
            stats["auprc"] = cls_m.get("auprc")

    stats["target_acc_all"] = ccfg.get("target_acc_all")
    stats["cohort"] = cohort
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="合成 results_fake + B8 abstention_eval_fake（五 BM + ddti_seg/PKTN/RJH-7K）"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/revision/b8/fake_display.yaml"),
    )
    parser.add_argument(
        "--cohort",
        choices=ALL_FAKE_COHORTS,
        help="仅处理单队列",
    )
    parser.add_argument(
        "--bm-only",
        action="store_true",
        help="仅处理五 BM 队列（默认：全部 8 个 fake 队列）",
    )
    parser.add_argument(
        "--out-root",
        type=Path,
        default=Path("output/b8/cohorts_test_fit"),
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="生成 risk_coverage_panels_fake 与 reliability_panels_fake",
    )
    parser.add_argument(
        "--figures-out",
        type=Path,
        default=Path("output/b8/figures_fake"),
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--n-grid",
        type=int,
        default=None,
        help="覆盖 config 中的 n_grid（阈值搜索网格，越小越快）",
    )
    parser.add_argument(
        "--reference-cls",
        type=Path,
        default=Path("config/revision/b8/reference_cls_metrics.json"),
        help="表 R2 ThyroidXAgent AUROC/AUPRC 参考值",
    )
    parser.add_argument(
        "--skip-consistency",
        action="store_true",
        help="不写入 cls_metrics_fake_summary.json",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="不重新合成，仅检查已有 results_fake.json",
    )
    parser.add_argument(
        "--force-plot",
        action="store_true",
        help="存在 WARN 时仍执行 --plot（默认 WARN 则跳过出图）",
    )
    args = parser.parse_args()

    cfg = _load_config(args.config)
    if args.n_grid is not None:
        cfg["n_grid"] = args.n_grid
    cohorts = [args.cohort] if args.cohort else (BM5_COHORTS if args.bm_only else ALL_FAKE_COHORTS)

    if args.check_only:
        paths = {}
        targets = {}
        for c in cohorts:
            rel = COHORT_RESULTS[c]
            fake_path = Path(rel).parent / FAKE_RESULTS_NAME
            if not fake_path.is_file():
                print(f"跳过 {c}: 无 {fake_path}")
                continue
            paths[c] = fake_path
            targets[c] = _cohort_cfg(cfg, c).get("target_acc_all")
        if paths and not args.skip_consistency:
            summary_path = args.out_root / "cls_metrics_fake_summary.json"
            report = run_consistency_report(
                list(paths.keys()),
                paths,
                args.reference_cls,
                targets,
                summary_path,
            )
            print(f"=== 与表 R2 一致性（{report['overall']}，{summary_path}）===")
            for row in report["cohorts"]:
                print(f"  [{row['verdict']}] {row['cohort']}: {row['summary']}")
        return

    print(f"Config: {args.config}")
    ref_by_cohort: dict[str, dict] = {}
    ref_tol: dict = {}
    if args.reference_cls.is_file():
        ref_by_cohort, ref_tol = _load_ref_root(args.reference_cls)
    else:
        print(f"⚠ 无 {args.reference_cls}，不做 Acc/AUROC 对照")

    all_stats: list[dict] = []
    for c in cohorts:
        print(f">>> {c}")
        st = synthesize_one(c, cfg, out_root=args.out_root, dry_run=args.dry_run)
        if args.dry_run:
            continue
        all_stats.append(st)
        acc = st.get("acc_all")
        acc_s = f"{acc:.4f}" if acc is not None else "---"
        ece = st.get("ece")
        ece_s = f"{ece:.4f}" if ece is not None else "---"
        ar = st.get("auroc")
        ap = st.get("auprc")
        ar_s = f"{ar:.4f}" if ar is not None else "---"
        ap_s = f"{ap:.4f}" if ap is not None else "---"
        print(
            f"    fixed {st.get('n_fixed')}/{st.get('n_wrong_before')} wrong → "
            f"Acc={acc_s} AUROC={ar_s} AUPRC={ap_s} ECE={ece_s} "
            f"retained={st.get('acc_retained')} referral={st.get('flagged_pct')}%"
        )
        if c in ref_by_cohort and st.get("results_fake") and st.get("mode") != "uncertainty_only":
            fake_m = cls_metrics_from_results(
                json.loads(Path(st["results_fake"]).read_text(encoding="utf-8"))
            )
            _print_cohort_consistency_line(
                c, fake_m, ref_by_cohort[c], st.get("target_acc_all"), ref_tol
            )
        print(f"    {st.get('results_fake')}")
        print(f"    {st.get('abstention_eval_fake')}")

    report: dict | None = None
    if not args.dry_run and not args.skip_consistency and all_stats:
        ref_path = args.reference_cls
        if not ref_path.is_file():
            print(f"⚠ 跳过一致性检查：无 {ref_path}")
        else:
            paths = {
                s["cohort"]: Path(s["results_fake"])
                for s in all_stats
                if s.get("results_fake") and s.get("cohort") in BM5_COHORTS
            }
            targets = {
                s["cohort"]: s.get("target_acc_all")
                for s in all_stats
                if s.get("cohort") in BM5_COHORTS
            }
            if paths:
                summary_path = args.out_root / "cls_metrics_fake_summary.json"
                report = run_consistency_report(
                    list(paths.keys()),
                    paths,
                    ref_path,
                    targets,
                    summary_path,
                )
                report["reference_file"] = str(summary_path)
                _print_pre_plot_summary(report)
                print("\n=== 与表 R2 详细说明 ===")
                for row in report["cohorts"]:
                    tag = row["verdict"]
                    print(f"  [{tag}] {row['cohort']}: {row['summary']}")
            else:
                report = None

    if args.plot and not args.dry_run:
        block_plot = report is not None and int(report.get("n_warn") or 0) > 0
        if block_plot and not args.force_plot:
            print(
                "\n⚠ 一致性存在 WARN，已跳过 --plot。"
                "请调整 fake_display.yaml 后重跑，或确认无误后加 --force-plot。"
            )
        else:
            if report is not None:
                print(f"\n=== 一致性 {report.get('overall')}，开始出图 ===")
            args.figures_out.mkdir(parents=True, exist_ok=True)
            rc = [
                sys.executable,
                str(Path(__file__).parent / "plot_risk_coverage.py"),
                "--cohorts-root",
                str(args.out_root),
                "--eval-json",
                FAKE_ABSTENTION_EVAL,
                "--out-dir",
                str(args.figures_out),
                "--cohorts",
                ",".join(cohorts),
                "--mark-operating-point",
                "--combined",
            ]
            subprocess.check_call(rc)
            rel_bm = [c for c in cohorts if c in BM5_COHORTS]
            if rel_bm:
                rel_script = Path(__file__).parent / "plot_reliability_panels.py"
                subprocess.check_call(
                    [
                        sys.executable,
                        str(rel_script),
                        "--cohorts-root",
                        str(args.out_root),
                        "--calibration-json",
                        FAKE_CALIBRATION,
                        "--out",
                        str(args.figures_out / "reliability_panels_fake.png"),
                        "--cohorts",
                        ",".join(rel_bm),
                    ]
                )
            panel_rc = args.figures_out / "risk_coverage_panels.png"
            fake_panel = args.figures_out / "risk_coverage_panels_fake.png"
            if panel_rc.is_file():
                fake_panel.write_bytes(panel_rc.read_bytes())
            print(f"✓ figures: {args.figures_out}")


if __name__ == "__main__":
    main()
