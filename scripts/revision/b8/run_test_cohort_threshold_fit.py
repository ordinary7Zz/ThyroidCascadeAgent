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
    apply_abstention,
    fit_thresholds_quantile,
    risk_coverage_curve,
    save_thresholds,
    summarize_abstention_by_group,
)
from pipeline.revision.b8.calibration import calibration_from_results
from pipeline.revision.b8.plot_calibration import plot_reliability_diagram

COHORT_RESULTS: dict[str, str] = {
    "tn3k": "output/TN3K/pipeline_run/results.json",
    "tn5k": "output/TN5K/pipeline_run/results.json",
    "thyroidxl": "output/ThyroidXL/pipeline_run/results.json",
    "zjh8k": "output/ZJH-8K/pipeline_run/results.json",
    "ddti_cls": "output/DDTI_cls/pipeline_run/results.json",
}


def run_one(
    cohort: str,
    results_path: Path,
    out_dir: Path,
    quantile: float,
) -> dict:
    data = json.loads(results_path.read_text(encoding="utf-8"))
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
    payload = {
        "calibration": cal,
        "risk_coverage": curve,
        "by_center": by_center,
        "n_flagged": n_flagged,
        "n_total": len(flagged),
        "threshold_fitted_on": f"test_same_cohort_{cohort}",
        "quantile": quantile,
    }
    (out_dir / "abstention_eval.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "calibration_test.json").write_text(
        json.dumps(cal, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    label = cohort.upper() if cohort != "ddti_cls" else "DDTI"
    plot_reliability_diagram(
        cal.get("bins", []),
        out_dir / "reliability_test.png",
        title=f"{label}: test calibration (thresholds fit on this test cohort, q={quantile})",
    )
    return {
        "cohort": cohort,
        "n": len(flagged),
        "n_flagged": n_flagged,
        "ece": cal.get("ece"),
        "brier": cal.get("brier"),
        "flagged_pct": 100.0 * n_flagged / len(flagged) if flagged else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Per-test-cohort B8 threshold fit + eval")
    parser.add_argument(
        "--cohort",
        choices=list(COHORT_RESULTS.keys()),
        help="单队列；省略则跑全部 BM 五队列",
    )
    parser.add_argument("--quantile", type=float, default=0.95)
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
        print(f">>> {c}: {path}")
        s = run_one(c, path, args.out_root / c, args.quantile)
        summaries.append(s)
        print(
            f"    n={s['n']} flagged={s['n_flagged']} ({s['flagged_pct']:.1f}%) "
            f"ECE={s['ece']:.4f} Brier={s['brier']:.4f}"
        )
    print("✓ done:", args.out_root)


if __name__ == "__main__":
    main()
