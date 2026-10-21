#!/usr/bin/env python3
"""B7：从 labels.json（+ 可选 G3 CSV）生成中心描述表。"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import repo_path

repo_path.install()

from shared.center_manifest import summarize_centers_from_labels
from shared.revision_paths import B7_DESCRIPTIVE_OUT, NHC_REVISION_CONFIG, load_pipeline_data_paths


def _merge_g3_csv(summary: dict, g3_path: Path) -> dict:
    if not g3_path.is_file():
        return summary
    with open(g3_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row.get("center_id") or row.get("centre_id")
            if not cid:
                continue
            block = summary["centers"].setdefault(cid, {"n_images": 0})
            for k in ("scanner", "scanner_vendor", "hospital", "province"):
                if row.get(k):
                    block[k] = row[k]
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="NHC 中心描述表")
    parser.add_argument("--label-file", type=Path, default=None)
    parser.add_argument("--g3-csv", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=B7_DESCRIPTIVE_OUT)
    args = parser.parse_args()

    if args.label_file is None:
        _, lab = load_pipeline_data_paths(NHC_REVISION_CONFIG)
        if not lab:
            raise SystemExit("未指定 --label-file，且 revision config 中无 label_file")
        args.label_file = Path(lab)

    summary = summarize_centers_from_labels(args.label_file)
    if args.g3_csv:
        summary = _merge_g3_csv(summary, args.g3_csv)

    args.out.mkdir(parents=True, exist_ok=True)
    out_json = args.out / "nhc_center_descriptive.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    out_csv = args.out / "nhc_center_descriptive.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["center_id", "n_images", "n_labeled", "n_malignant", "malignant_ratio"])
        for cid, c in sorted(summary.get("centers", {}).items()):
            writer.writerow([
                cid,
                c.get("n_images", 0),
                c.get("n_labeled", 0),
                c.get("n_malignant", 0),
                c.get("malignant_ratio"),
            ])
    print(f"✓ {out_json}")
    print(f"✓ {out_csv} ({summary.get('n_centers', 0)} 中心)")


if __name__ == "__main__":
    main()
