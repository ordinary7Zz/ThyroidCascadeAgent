#!/usr/bin/env python3
"""从 output/ablation/b3/<cohort>/learned/b3_metrics.json 导出策略 6 CSV 到 docs/revision/b3/tables/."""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
B3_ROOT = REPO / "output" / "ablation" / "b3"
OUT = REPO / "docs" / "revision" / "b3" / "tables"

SEG_COHORTS = (
    "tn3k",
    "tn5k",
    "thyroidxl",
    "pktn",
    "ddti_seg",
    "zjh8k",
    "rjh7k",
)
CLS_COHORTS = (
    "tn3k",
    "tn5k",
    "thyroidxl",
    "ddti_cls",
    "zjh8k",
)


def _load(cohort: str) -> dict | None:
    p = B3_ROOT / cohort / "learned" / "b3_metrics.json"
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> None:
    rows_seg: list[dict] = []
    rows_cls: list[dict] = []
    rows_pathb: list[dict] = []
    rows_meta: list[dict] = []

    for cohort in SEG_COHORTS:
        d = _load(cohort)
        if d is None:
            continue
        seg = d.get("segmentation") or {}
        if not seg.get("dice_mean") and seg.get("dice_mean") != 0:
            continue
        rows_meta.append(
            {
                "cohort": cohort,
                "routing_mode": "learned",
                "n_total": d["n_total"],
                "n_consensus": d.get("n_consensus"),
                "n_path_b": d.get("n_disagreement"),
            }
        )
        rows_seg.append(
            {
                "cohort": cohort,
                "routing_mode": "learned",
                **{k: seg.get(k) for k in (
                    "dice_mean", "dice_ci_lower", "dice_ci_upper",
                    "hd95_mean", "hd95_ci_lower", "hd95_ci_upper",
                )},
            }
        )

    for cohort in CLS_COHORTS:
        d = _load(cohort)
        if d is None:
            continue
        cls = d.get("classification") or {}
        pb = d.get("classification_path_b") or d.get("metrics_path_b_only") or {}
        rows_meta.append(
            {
                "cohort": cohort,
                "routing_mode": "learned",
                "n_total": d["n_total"],
                "n_consensus": d.get("n_consensus"),
                "n_path_b": d.get("n_disagreement"),
            }
        )
        rows_cls.append(
            {
                "cohort": cohort,
                "routing_mode": "learned",
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
                    "cohort": cohort,
                    "routing_mode": "learned",
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
            print("skip (empty)", name)
            return
        path = OUT / name
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print("wrote", path)

    write("b3_learned_segmentation.csv", rows_seg)
    write("b3_learned_classification_full.csv", rows_cls)
    write("b3_learned_classification_path_b.csv", rows_pathb)
    write("b3_learned_cohort_meta.csv", rows_meta)


if __name__ == "__main__":
    main()
