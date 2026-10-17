#!/usr/bin/env python3
"""汇总 output/ablation/b5 下各 metadata_mode 的 b3_metrics.json。"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from shared.metadata_prompt import METADATA_MODES


def _read_metrics(run_dir: Path) -> dict | None:
    p = run_dir / "b3_metrics.json"
    if not p.is_file():
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def collect_b5_root(root: Path) -> list[dict]:
    rows: list[dict] = []
    if not root.is_dir():
        return rows
    for cohort_dir in sorted(root.iterdir()):
        if not cohort_dir.is_dir():
            continue
        for mode in sorted(METADATA_MODES):
            mdir = cohort_dir / mode
            m = _read_metrics(mdir)
            if not m:
                continue
            seg = m.get("segmentation") or {}
            cls = m.get("classification") or {}
            rows.append({
                "dataset_id": cohort_dir.name,
                "metadata_mode": mode,
                "dice_mean": seg.get("dice_mean"),
                "dice_ci_lower": seg.get("dice_ci_lower"),
                "dice_ci_upper": seg.get("dice_ci_upper"),
                "auroc": cls.get("auroc"),
                "auroc_ci_lower": cls.get("auroc_ci_lower"),
                "auroc_ci_upper": cls.get("auroc_ci_upper"),
                "n_total": m.get("n_total"),
            })
    return rows


def add_deltas(rows: list[dict]) -> list[dict]:
    by_ds: dict[str, dict[str, dict]] = {}
    for r in rows:
        by_ds.setdefault(r["dataset_id"], {})[r["metadata_mode"]] = r
    extras: list[dict] = []
    for ds, modes in by_ds.items():
        full = modes.get("full")
        qo = modes.get("quality_only")
        if full and qo:
            extras.append({
                "dataset_id": ds,
                "metadata_mode": "delta_full_to_quality_only",
                "dice_mean": _delta(full.get("dice_mean"), qo.get("dice_mean")),
                "auroc": _delta(full.get("auroc"), qo.get("auroc")),
            })
    return rows + extras


def _delta(a, b):
    if a is None or b is None:
        return None
    return float(a) - float(b)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("output/ablation/b5"))
    parser.add_argument("--out-json", type=Path, default=Path("artifacts/b5_summary.json"))
    parser.add_argument("--out-csv", type=Path, default=Path("artifacts/b5_summary.csv"))
    args = parser.parse_args()

    rows = add_deltas(collect_b5_root(args.root))
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    if rows:
        with open(args.out_csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    print(f"wrote {len(rows)} rows -> {args.out_json} {args.out_csv}")


if __name__ == "__main__":
    main()
