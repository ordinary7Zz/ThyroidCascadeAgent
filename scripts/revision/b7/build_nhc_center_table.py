#!/usr/bin/env python3
"""B7：从 labels.json（+ 可选 G3 CSV）生成中心描述表。"""

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
import csv
import json
from pathlib import Path

import repo_path

repo_path.install()

from shared.center_manifest import summarize_centers_from_labels
from shared.revision_paths import B7_DESCRIPTIVE_OUT, NHC_REVISION_CONFIG, load_pipeline_data_paths


def _merge_center_stats(summary: dict, stats_path: Path) -> dict:
    """合并 run_nhc_prepare 产出的 center_stats.json（含 n_patients）。"""
    if not stats_path.is_file():
        return summary
    with open(stats_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for cid, block in (data.get("centers") or {}).items():
        c = summary["centers"].setdefault(cid, {"n_images": 0})
        if "n_patients" in block:
            c["n_patients"] = block["n_patients"]
    if data.get("n_patients_total") is not None:
        summary["n_patients_total"] = data["n_patients_total"]
    return summary


def _merge_patients_from_labels(summary: dict, label_file: Path) -> dict:
    """若 labels 含 patient_id，按 center_id 去重计数（与 center_stats 对账）。"""
    if not label_file.is_file():
        return summary
    with open(label_file, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, list):
        return summary
    by_center: dict[str, set[str]] = {}
    for row in raw:
        if not isinstance(row, dict):
            continue
        cid = row.get("center_id")
        pid = row.get("patient_id")
        if cid and pid:
            by_center.setdefault(str(cid), set()).add(str(pid))
    for cid, pids in by_center.items():
        c = summary["centers"].setdefault(cid, {"n_images": 0})
        c.setdefault("n_patients", len(pids))
    return summary


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
            for k in (
                "n_patients",
                "n_nodules",
                "scanner",
                "scanner_vendor",
                "hospital",
                "province",
                "seg_label",
                "bm_label",
                "gland_label",
            ):
                if row.get(k) not in (None, ""):
                    block[k] = row[k]
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="NHC 中心描述表")
    parser.add_argument("--label-file", type=Path, default=None)
    parser.add_argument("--g3-csv", type=Path, default=None)
    parser.add_argument(
        "--center-stats",
        type=Path,
        default=None,
        help="run_nhc_prepare 的 center_stats.json（默认与 label-file 同目录）",
    )
    parser.add_argument("--out", type=Path, default=B7_DESCRIPTIVE_OUT)
    args = parser.parse_args()

    if args.label_file is None:
        _, lab = load_pipeline_data_paths(NHC_REVISION_CONFIG)
        if not lab:
            raise SystemExit("未指定 --label-file，且 revision config 中无 label_file")
        args.label_file = Path(lab)

    summary = summarize_centers_from_labels(args.label_file)
    stats_path = args.center_stats
    if stats_path is None and args.label_file is not None:
        candidate = args.label_file.parent / "center_stats.json"
        if candidate.is_file():
            stats_path = candidate
    if stats_path:
        summary = _merge_center_stats(summary, stats_path)
    summary = _merge_patients_from_labels(summary, args.label_file)
    if args.g3_csv:
        summary = _merge_g3_csv(summary, args.g3_csv)

    args.out.mkdir(parents=True, exist_ok=True)
    out_json = args.out / "nhc_center_descriptive.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    out_csv = args.out / "nhc_center_descriptive.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "center_id",
            "n_patients",
            "n_images",
            "n_labeled",
            "n_malignant",
            "malignant_ratio",
        ])
        for cid, c in sorted(summary.get("centers", {}).items()):
            writer.writerow([
                cid,
                c.get("n_patients"),
                c.get("n_images", 0),
                c.get("n_labeled", 0),
                c.get("n_malignant", 0),
                c.get("malignant_ratio"),
            ])
    print(f"✓ {out_json}")
    print(f"✓ {out_csv} ({summary.get('n_centers', 0)} 中心)")


if __name__ == "__main__":
    main()

