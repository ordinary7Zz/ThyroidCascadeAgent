#!/usr/bin/env python3
"""B7：从 pipeline 输出目录生成按中心聚合指标。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import repo_path

repo_path.install()

from pipeline.evaluate import evaluate_pipeline
from pipeline.meta_regression import heterogeneity_i2_tau2
from pipeline.nhc_heterogeneity import (
    _load_jsonl,
    dice_values_by_center,
    load_center_metrics_from_output_dir,
)
from shared.image_io import ImageIO
from shared.revision_paths import (
    B7_DEFAULT_OUT,
    NHC_PRIMARY_OUTPUT_DIR,
    NHC_REVISION_CONFIG,
    load_pipeline_data_paths,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="B7 NHC 中心级异质性汇总")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=NHC_PRIMARY_OUTPUT_DIR,
        help=f"含 results.json 的 pipeline 输出（默认 {NHC_PRIMARY_OUTPUT_DIR}）",
    )
    parser.add_argument("--gt-mask-dir", type=Path, default=None)
    parser.add_argument("--label-file", type=Path, default=None)
    parser.add_argument("--re-evaluate", action="store_true", help="先跑 evaluate 生成 per_image_*.jsonl")
    parser.add_argument("--out", type=Path, default=B7_DEFAULT_OUT)
    args = parser.parse_args()

    if args.gt_mask_dir is None or args.label_file is None:
        gt, lab = load_pipeline_data_paths(NHC_REVISION_CONFIG)
        if args.gt_mask_dir is None and gt:
            args.gt_mask_dir = Path(gt)
        if args.label_file is None and lab:
            args.label_file = Path(lab)

    args.out.mkdir(parents=True, exist_ok=True)
    results_path = args.output_dir / "results.json"
    if not results_path.is_file():
        raise SystemExit(f"缺少 {results_path}")

    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    if args.re_evaluate:
        evaluate_pipeline(
            results,
            str(args.output_dir),
            image_io=ImageIO(),
            gt_mask_dir=str(args.gt_mask_dir) if args.gt_mask_dir else None,
        )

    summary = load_center_metrics_from_output_dir(args.output_dir)
    per_seg = _load_jsonl(args.output_dir / "per_image_seg_metrics.jsonl")
    i2_block = heterogeneity_i2_tau2(dice_values_by_center(per_seg, results))
    summary["heterogeneity_dice"] = i2_block

    out_path = args.out / "center_metrics.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"✓ 中心汇总: {out_path} ({summary['n_centers']} 个中心)")
    if i2_block.get("i2_percent") is not None:
        print(f"  Dice I² ≈ {i2_block['i2_percent']:.1f}%, τ² ≈ {i2_block.get('tau2')}")


if __name__ == "__main__":
    main()
