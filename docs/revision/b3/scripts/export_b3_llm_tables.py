#!/usr/bin/env python3
"""从 manuscript_llm_metrics.yaml 导出策略 7（稿面 ThyroidXAgent）CSV。"""

from __future__ import annotations

import csv
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[4]
YAML_PATH = REPO / "docs" / "revision" / "b3" / "manuscript_llm_metrics.yaml"
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


def main() -> None:
    data = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    cohorts = data.get("cohorts") or {}

    rows_seg: list[dict] = []
    rows_cls: list[dict] = []
    rows_meta: list[dict] = []

    for cid in SEG_COHORTS:
        c = cohorts.get(cid) or {}
        seg = c.get("segmentation") or {}
        if not seg:
            continue
        rows_meta.append(
            {
                "cohort": cid,
                "routing_mode": "llm",
                "n_total": c.get("n_test"),
                "source": "manuscript_table_s3",
            }
        )
        rows_seg.append(
            {
                "cohort": cid,
                "routing_mode": "llm",
                **{k: seg.get(k) for k in (
                    "dice_mean", "dice_ci_lower", "dice_ci_upper",
                    "hd95_mean", "hd95_ci_lower", "hd95_ci_upper",
                )},
            }
        )

    for cid in CLS_COHORTS:
        c = cohorts.get(cid) or {}
        cls = c.get("classification") or {}
        if not cls:
            continue
        rows_meta.append(
            {
                "cohort": cid,
                "routing_mode": "llm",
                "n_total": c.get("n_test"),
                "source": "manuscript_table_s4",
            }
        )
        rows_cls.append(
            {
                "cohort": cid,
                "routing_mode": "llm",
                "n": c.get("n_test"),
                "auroc": cls.get("auroc"),
                "auroc_ci_lower": cls.get("auroc_ci_lower"),
                "auroc_ci_upper": cls.get("auroc_ci_upper"),
                "auprc": cls.get("auprc"),
                "auprc_ci_lower": cls.get("auprc_ci_lower"),
                "auprc_ci_upper": cls.get("auprc_ci_upper"),
            }
        )

    OUT.mkdir(parents=True, exist_ok=True)

    def write(name: str, rows: list[dict]) -> None:
        if not rows:
            return
        path = OUT / name
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print("wrote", path)

    write("b3_llm_segmentation.csv", rows_seg)
    write("b3_llm_classification_full.csv", rows_cls)
    write("b3_llm_cohort_meta.csv", rows_meta)


if __name__ == "__main__":
    main()
