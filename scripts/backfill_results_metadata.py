#!/usr/bin/env python3
"""为已有 pipeline 输出补写 uncertainty / center_id。"""

from __future__ import annotations

import argparse
from pathlib import Path

import repo_path

repo_path.install()

from pipeline.backfill_uncertainty import backfill_results_metadata
from shared.revision_paths import NHC_PRIMARY_OUTPUT_DIR, NHC_REVISION_CONFIG, load_pipeline_data_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill uncertainty + center_id")
    parser.add_argument("--output-dir", type=Path, default=NHC_PRIMARY_OUTPUT_DIR)
    parser.add_argument("--config", type=Path, default=NHC_REVISION_CONFIG)
    parser.add_argument("--center-manifest", type=Path, default=None)
    parser.add_argument("--label-file", type=Path, default=None)
    parser.add_argument("--no-in-place", action="store_true", help="写入 results_with_uncertainty.json")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    if args.label_file is None:
        _, lab = load_pipeline_data_paths(args.config)
        if lab:
            args.label_file = Path(lab)

    updated = backfill_results_metadata(
        args.output_dir,
        args.config,
        center_manifest=str(args.center_manifest) if args.center_manifest else None,
        label_file=str(args.label_file) if args.label_file else None,
        in_place=not args.no_in_place,
        out_path=args.out,
    )
    print(f"✓ 已更新 {len(updated)} 条记录")


if __name__ == "__main__":
    main()
