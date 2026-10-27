#!/usr/bin/env python3
"""B7：从 b7_report.json 导出 CSV（回信/修订稿制表用）。"""

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
import csv
import json

import repo_path

repo_path.install()

from shared.revision_paths import B7_DEFAULT_OUT


def main() -> None:
    parser = argparse.ArgumentParser(description="导出 B7 CSV 表")
    parser.add_argument("--report", type=Path, default=B7_DEFAULT_OUT / "b7_report.json")
    parser.add_argument("--out-dir", type=Path, default=B7_DEFAULT_OUT)
    args = parser.parse_args()

    if not args.report.is_file():
        raise SystemExit(f"缺少 {args.report}，请先运行 run_b7_analysis.py")

    with open(args.report, "r", encoding="utf-8") as f:
        report = json.load(f)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    perf = report.get("center_performance", {}).get("centers", {})
    gland = (report.get("gland_center_performance") or {}).get("centers", {})
    within_nodule = (report.get("within_center") or {}).get("nodule_dice", {})
    desc_centers = (report.get("center_descriptive") or {}).get("centers", {})

    perf_path = args.out_dir / "nhc_center_performance.csv"
    with open(perf_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "center_id",
            "n_images_seg",
            "nodule_dice_mean",
            "nodule_hd95_mean",
            "n_cls",
            "auroc",
            "auprc",
            "auroc_estimable",
            "gland_dice_mean",
            "gland_n_images",
            "nodule_dice_std_within",
            "nodule_dice_cv_percent",
        ])
        all_ids = sorted(set(perf) | set(gland) | set(within_nodule))
        for cid in all_ids:
            p = perf.get(cid, {})
            g = gland.get(cid, {})
            wn = within_nodule.get(cid, {})
            w.writerow([
                cid,
                p.get("n_images_seg"),
                p.get("dice_mean"),
                p.get("hd95_mean"),
                p.get("n_cls"),
                p.get("auroc"),
                p.get("auprc"),
                p.get("auroc_estimable"),
                g.get("dice_mean"),
                g.get("n_images"),
                wn.get("std"),
                wn.get("cv_percent"),
            ])
    print(f"✓ {perf_path}")

    hetero_path = args.out_dir / "nhc_heterogeneity_summary.csv"
    hetero = report.get("heterogeneity") or {}
    with open(hetero_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task_metric", "i2_percent", "tau2", "n_groups", "q", "df"])
        for name, block in hetero.items():
            if not block:
                continue
            w.writerow([
                name,
                block.get("i2_percent"),
                block.get("tau2"),
                block.get("n_groups"),
                block.get("q"),
                block.get("df"),
            ])
    print(f"✓ {hetero_path}")

    if desc_centers:
        desc_path = args.out_dir / "nhc_center_descriptive_merged.csv"
        keys = sorted({k for c in desc_centers.values() for k in c})
        with open(desc_path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["center_id"] + keys, extrasaction="ignore")
            w.writeheader()
            for cid, block in sorted(desc_centers.items()):
                row = {"center_id": cid, **block}
                w.writerow(row)
        print(f"✓ {desc_path}")


if __name__ == "__main__":
    main()
