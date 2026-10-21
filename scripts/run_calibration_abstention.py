#!/usr/bin/env python3
"""B8：验证集定阈 + 测试集校准/拒答评估。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import repo_path

repo_path.install()

from pipeline.abstention import (
    apply_abstention,
    fit_thresholds_quantile,
    load_thresholds,
    risk_coverage_curve,
    save_thresholds,
    summarize_abstention_by_group,
)
from pipeline.calibration import calibration_from_results
from pipeline.evaluate import _label_to_binary
from pipeline.plot_calibration import plot_reliability_diagram
from shared.revision_paths import (
    B8_FIT_OUT,
    B8_NHC_EVAL_OUT,
    NHC_PRIMARY_OUTPUT_DIR,
    VALIDATION_NO_LLM_RESULTS,
)


def _load_results(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    parser = argparse.ArgumentParser(description="B8 校准与拒答")
    parser.add_argument("--fit", action="store_true", help="在验证集上拟合阈值")
    parser.add_argument("--eval", action="store_true", help="在测试集上评估")
    parser.add_argument("--val-results", type=Path, help="验证集 results.json")
    parser.add_argument("--test-results", type=Path, help="测试集 results.json")
    parser.add_argument("--thresholds", type=Path, help="已有阈值 JSON（仅 --eval）")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="--fit 默认 output/b8/fit；--eval 默认 output/b8/nhc",
    )
    parser.add_argument("--rule-subset", choices=["full", "nhc"], default="nhc")
    parser.add_argument("--quantile", type=float, default=0.9)
    args = parser.parse_args()

    if not args.fit and not args.eval:
        parser.error("至少指定 --fit 或 --eval")

    if args.out is None:
        args.out = B8_FIT_OUT if args.fit and not args.eval else B8_NHC_EVAL_OUT
    if args.eval and not args.test_results:
        args.test_results = NHC_PRIMARY_OUTPUT_DIR / "results.json"
    if args.fit and not args.val_results:
        args.val_results = VALIDATION_NO_LLM_RESULTS

    args.out.mkdir(parents=True, exist_ok=True)
    thresholds_path = args.out / "abstention_thresholds.json"

    if args.fit:
        if not args.val_results:
            parser.error("--fit 需要 --val-results")
        val_results = _load_results(args.val_results)
        subset = args.rule_subset if args.rule_subset == "nhc" else None
        th = fit_thresholds_quantile(
            val_results,
            rule_subset=subset,
            quantile=args.quantile,
        )
        save_thresholds(thresholds_path, th)
        cal = calibration_from_results(val_results, label_to_binary=_label_to_binary)
        with open(args.out / "calibration_val.json", "w", encoding="utf-8") as f:
            json.dump(cal, f, ensure_ascii=False, indent=2)
        fig = plot_reliability_diagram(
            cal.get("bins", []),
            args.out / "reliability_val.png",
            title="Validation calibration",
        )
        if fig:
            print(f"✓ 可靠性图: {fig}")
        print(f"✓ 阈值已保存: {thresholds_path}")

    if args.eval:
        if not args.test_results:
            parser.error("--eval 需要 --test-results")
        th_path = args.thresholds or thresholds_path
        if not th_path.is_file():
            parser.error(f"缺少阈值文件: {th_path}")
        th = load_thresholds(th_path)
        test_results = _load_results(args.test_results)
        flagged = apply_abstention(test_results, th)
        cal = calibration_from_results(flagged, label_to_binary=_label_to_binary)
        curve = risk_coverage_curve(flagged)
        by_center = summarize_abstention_by_group(flagged, group_key="center_id")
        payload = {
            "calibration": cal,
            "risk_coverage": curve,
            "by_center": by_center,
            "n_flagged": sum(1 for r in flagged if r.get("flagged_for_review")),
            "n_total": len(flagged),
        }
        with open(args.out / "abstention_eval.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        with open(args.out / "calibration_test.json", "w", encoding="utf-8") as f:
            json.dump(cal, f, ensure_ascii=False, indent=2)
        with open(args.out / "results_flagged.json", "w", encoding="utf-8") as f:
            json.dump(flagged, f, ensure_ascii=False, indent=2)
        fig = plot_reliability_diagram(
            cal.get("bins", []),
            args.out / "reliability_test.png",
            title="Test calibration",
        )
        if fig:
            print(f"✓ 可靠性图: {fig}")
        print(f"✓ 评估已保存: {args.out / 'abstention_eval.json'}")


if __name__ == "__main__":
    main()
