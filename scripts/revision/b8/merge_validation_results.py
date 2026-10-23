#!/usr/bin/env python3
"""合并四队列 validation pipeline 的 results.json 与标签列表。"""

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

import importlib.util
from pathlib import Path

import argparse
import json
from pathlib import Path

import repo_path

repo_path.install()

DEFAULT_PARTS: list[tuple[str, Path, Path]] = [
    (
        "tn3k",
        Path("output/validation/_parts/tn3k/results.json"),
        Path(
            "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/"
            "TN3K/valid/TN3K_valid_label.json"
        ),
    ),
    (
        "tn5k",
        Path("output/validation/_parts/tn5k/results.json"),
        Path(
            "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/"
            "TN5K/valid_copy/TN5K_valid_label.json"
        ),
    ),
    (
        "thyroidxl",
        Path("output/validation/_parts/thyroidxl/results.json"),
        Path(
            "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/"
            "ThyroidXL/valid/ThyroidXL_valid_label.json"
        ),
    ),
    (
        "pktn",
        Path("output/validation/_parts/pktn/results.json"),
        Path(
            "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/"
            "PKTN/valid/PKTN_valid_label.json"
        ),
    ),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="合并 OpenThyroidDB validation 结果")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("output/validation/no_llm_primary"),
    )
    args = parser.parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    merged_results: list[dict] = []
    merged_labels: list[dict] = []
    manifest: list[dict] = []

    for cohort, results_path, label_path in DEFAULT_PARTS:
        if not results_path.is_file():
            raise FileNotFoundError(f"缺少 {cohort} results: {results_path}")
        if not label_path.is_file():
            raise FileNotFoundError(f"缺少 {cohort} labels: {label_path}")
        rows = json.loads(results_path.read_text(encoding="utf-8"))
        labels = json.loads(label_path.read_text(encoding="utf-8"))
        for r in rows:
            row = dict(r)
            row["validation_cohort"] = cohort
            merged_results.append(row)
        for lab in labels:
            merged_labels.append({**lab, "validation_cohort": cohort})
        manifest.append(
            {
                "cohort": cohort,
                "n_results": len(rows),
                "n_labels": len(labels),
                "results_path": str(results_path),
                "label_path": str(label_path),
            }
        )

    results_out = out_dir / "results.json"
    labels_out = out_dir / "labels_merged.json"
    manifest_out = out_dir / "merge_manifest.json"

    results_out.write_text(
        json.dumps(merged_results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    labels_out.write_text(
        json.dumps(merged_labels, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    manifest_out.write_text(
        json.dumps(
            {"n_total": len(merged_results), "parts": manifest},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"n_total": len(merged_results), "out": str(results_out)}, indent=2))


if __name__ == "__main__":
    main()

import importlib.util
from pathlib import Path


