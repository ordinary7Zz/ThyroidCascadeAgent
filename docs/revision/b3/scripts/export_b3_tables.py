#!/usr/bin/env python3
"""从 output/ablation/b3 导出波次 1 三队列 CSV 到 docs/revision/b3/tables/."""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
B3_ROOT = REPO / "output" / "ablation" / "b3"
OUT = REPO / "docs" / "revision" / "b3" / "tables"

COHORTS = ("tn3k", "tn5k", "thyroidxl")
MODES = (
    "soft_voting",
    "majority",
    "max_confidence",
    "static_rule",
    "best_single",
    "oracle",
)


def main() -> None:
    rows_seg: list[dict] = []
    rows_cls: list[dict] = []
    rows_pathb: list[dict] = []
    rows_meta: list[dict] = []

    for cohort in COHORTS:
        for mode in MODES:
            metrics_path = B3_ROOT / cohort / mode / "b3_metrics.json"
            d = json.loads(metrics_path.read_text())
            rows_meta.append(
                {
                    "cohort": cohort.upper(),
                    "routing_mode": mode,
                    "n_total": d["n_total"],
                    "n_consensus": d.get("n_consensus"),
                    "n_path_b": d.get("n_disagreement"),
                }
            )
            seg = d.get("segmentation", {})
            cls = d.get("classification", {})
            pb = d.get("metrics_path_b_only") or d.get("classification_path_b") or {}
            rows_seg.append(
                {
                    "cohort": cohort.upper(),
                    "routing_mode": mode,
                    **{k: seg.get(k) for k in (
                        "dice_mean", "dice_ci_lower", "dice_ci_upper",
                        "hd95_mean", "hd95_ci_lower", "hd95_ci_upper",
                    )},
                }
            )
            rows_cls.append(
                {
                    "cohort": cohort.upper(),
                    "routing_mode": mode,
                    "n": cls.get("n", d["n_total"]),
                    "accuracy": cls.get("accuracy"),
                    "auroc": cls.get("auroc"),
                    "auroc_ci_lower": cls.get("auroc_ci_lower"),
                    "auroc_ci_upper": cls.get("auroc_ci_upper"),
                    "auprc": cls.get("auprc"),
                    "auprc_ci_lower": cls.get("auprc_ci_lower"),
                    "auprc_ci_upper": cls.get("auprc_ci_upper"),
                }
            )
            if pb.get("n"):
                rows_pathb.append(
                    {
                        "cohort": cohort.upper(),
                        "routing_mode": mode,
                        "n_path_b": pb["n"],
                        "accuracy": pb.get("accuracy"),
                        "auroc": pb.get("auroc"),
                        "auroc_ci_lower": pb.get("auroc_ci_lower"),
                        "auroc_ci_upper": pb.get("auroc_ci_upper"),
                        "auprc": pb.get("auprc"),
                    }
                )

    OUT.mkdir(parents=True, exist_ok=True)

    def write(name: str, rows: list[dict]) -> None:
        if not rows:
            return
        path = OUT / name
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print("wrote", path)

    write("b3_wave1_segmentation.csv", rows_seg)
    write("b3_wave1_classification_full.csv", rows_cls)
    write("b3_wave1_classification_path_b.csv", rows_pathb)
    write("b3_wave1_cohort_meta.csv", rows_meta)


if __name__ == "__main__":
    main()
