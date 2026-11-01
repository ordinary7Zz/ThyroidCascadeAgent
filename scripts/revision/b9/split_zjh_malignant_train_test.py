#!/usr/bin/env python3
"""Patient-level ZJH malignant hold-out split after TN3K dHash exclusion (tab_dhash / R1).

1. Start from zjh_all_labeled.json (4756 images).
2. Drop rows whose zjh_bm_filename matches TN3K train dHash H=0 to ZJH-8K (1151-name list).
3. Stratify patients on (LNM_CN01, FTCPTC); hold out test_fraction -> zjh_test.
4. Write train/dev manifests for LNM + FTCPTC packs (FangDai external test unchanged).

Default: 20% patients -> test, seed=42.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from sklearn.model_selection import train_test_split

REPO = Path(__file__).resolve().parents[3]
LNM_PACK = Path(
    "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/Classifaction_Data/LNM_ZJH8K_LymphUs_C1C2_packed"
)
FTC_PACK = Path(
    "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/Classifaction_Data/FTCPTC_ZJH8K_FangDai_packed"
)
BM_LABELS = Path(
    "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/ZJH-8K/ZJH-8K_BM_labels.json"
)
DEFAULT_EXCL = REPO / "docs/revision/b1/tables/zjh_excl_tn3k_train_dhash0_manifest.json"
SPLIT_REGISTRY = REPO / "docs/revision/b9/zjh_malignant_patient_split.json"


def _bm_filename(row: dict) -> str:
    return row.get("zjh_bm_filename") or Path(row["filename"]).name


def _load_exclude_names(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "images" in data:
        return set(data["images"])
    raise ValueError(f"Unexpected exclude manifest: {path}")


def _load_bm_lookup() -> dict[str, dict]:
    rows = json.loads(BM_LABELS.read_text(encoding="utf-8"))
    return {r["filename"]: r for r in rows}


def _filter_post_tn3k_exclusion(lnm_rows: list[dict], exclude: set[str]) -> list[dict]:
    kept: list[dict] = []
    for r in lnm_rows:
        if _bm_filename(r) in exclude:
            continue
        kept.append(r)
    return kept


def _patient_labels(rows: list[dict], bm: dict[str, dict]) -> dict[str, tuple[int, int]]:
    by_patient: dict[str, tuple[int, int]] = {}
    for r in rows:
        pid = r["patient_id"]
        name = _bm_filename(r)
        b = bm.get(name, {})
        lnm = r["LNM_CN01"]
        ftc = b.get("FTCPTC", r.get("FTCPTC"))
        if ftc not in (0, 1):
            raise ValueError(f"Missing FTCPTC for {name} (patient {pid})")
        if pid in by_patient and by_patient[pid] != (lnm, ftc):
            raise ValueError(f"Inconsistent labels for patient {pid}")
        by_patient[pid] = (lnm, int(ftc))
    return by_patient


def _split_patients(
    patient_labels: dict[str, tuple[int, int]],
    test_fraction: float,
    seed: int,
) -> tuple[list[str], list[str]]:
    patients = sorted(patient_labels.keys())
    y = [patient_labels[p][0] * 2 + patient_labels[p][1] for p in patients]
    if len(set(y)) < 2:
        raise ValueError("Need at least two strata for stratified split")
    train_p, test_p, _, _ = train_test_split(
        patients,
        patients,
        test_size=test_fraction,
        random_state=seed,
        stratify=y,
    )
    return sorted(train_p), sorted(test_p)


def _lnm_record(r: dict, split: str, ftc: int) -> dict:
    out = {k: v for k, v in r.items() if k != "split"}
    out["split"] = split
    out["FTCPTC"] = ftc
    if "modality" not in out:
        out["modality"] = "primary_tumor_ultrasound"
    return out


def _ftc_record(r: dict, split: str, ftc: int) -> dict:
    rel = r["filename"]
    return {
        "filename": f"images/zjh/{rel}",
        "FTCPTC": ftc,
        "malignancy": 1,
        "patient_id": r["patient_id"],
        "source": "zjh8k_malignant",
        "split": split,
        "zjh_bm_filename": _bm_filename(r),
        "image_root_key": "zjh",
        "LNM_CN01": r["LNM_CN01"],
    }


def _write_json(path: Path, data: list | dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test-fraction", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--exclude-manifest", type=Path, default=DEFAULT_EXCL)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.exclude_manifest.is_file():
        raise SystemExit(
            f"Missing {args.exclude_manifest}. Run:\n"
            "  python scripts/revision/b1/export_zjh_excl_tn3k_train_dhash0.py"
        )

    exclude = _load_exclude_names(args.exclude_manifest)
    lnm_all = json.loads((LNM_PACK / "manifests/zjh_all_labeled.json").read_text(encoding="utf-8"))
    bm = _load_bm_lookup()
    filtered = _filter_post_tn3k_exclusion(lnm_all, exclude)
    patient_labels = _patient_labels(filtered, bm)

    train_patients, test_patients = _split_patients(
        patient_labels, args.test_fraction, args.seed
    )
    train_set, test_set = set(train_patients), set(test_patients)

    lnm_train, lnm_test, lnm_dev = [], [], []
    ftc_train, ftc_test, ftc_dev = [], [], []
    for r in filtered:
        pid = r["patient_id"]
        ftc = patient_labels[pid][1]
        if pid in test_set:
            lnm_test.append(_lnm_record(r, "test", ftc))
            ftc_test.append(_ftc_record(r, "test", ftc))
        elif pid in train_set:
            lnm_train.append(_lnm_record(r, "train", ftc))
            ftc_train.append(_ftc_record(r, "train", ftc))
            lnm_dev.append(_lnm_record(r, "train", ftc))
            ftc_dev.append(_ftc_record(r, "train", ftc))
        else:
            raise RuntimeError(f"Patient {pid} missing from split")

    def summarize(rows: list, label_key: str) -> dict:
        return {
            "images": len(rows),
            "patients": len({r["patient_id"] for r in rows}),
            label_key: dict(sorted(Counter(r[label_key] for r in rows).items())),
        }

    registry = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "script": "scripts/revision/b9/split_zjh_malignant_train_test.py",
        "seed": args.seed,
        "test_fraction": args.test_fraction,
        "exclude_manifest": str(args.exclude_manifest.resolve()),
        "pool_before_exclusion": {"images": len(lnm_all), "patients": len({r['patient_id'] for r in lnm_all})},
        "pool_after_tn3k_h0_exclusion": {
            "images": len(filtered),
            "patients": len(patient_labels),
            "excluded_images": len(lnm_all) - len(filtered),
        },
        "tab_dhash_note": (
            "Letter cites 3865 ZJH images after TN3K-row exclusion; "
            "recomputed malignant pool with zjh_bm_filename vs 1151-name list = "
            f"{len(filtered)} images — reconcile Methods/tab note if needed."
        ),
        "train_patient_ids": train_patients,
        "test_patient_ids": test_patients,
        "counts": {
            "lnm_train": summarize(lnm_train, "LNM_CN01"),
            "lnm_test": summarize(lnm_test, "LNM_CN01"),
            "ftc_train": summarize(ftc_train, "FTCPTC"),
            "ftc_test": summarize(ftc_test, "FTCPTC"),
        },
        "notes": [
            "Shared patient IDs for LNM and FTC/PTC after TN3K dHash H=0 exclusion.",
            "zjh_dev_all.json = train only (5-fold OOF). zjh_test.json = held-out patients.",
            "FangDai external test unchanged.",
            "LymphUs not included in train_combined manifests.",
        ],
    }

    print(json.dumps(registry["pool_after_tn3k_h0_exclusion"], indent=2))
    print(json.dumps(registry["counts"], indent=2, ensure_ascii=False))

    if args.dry_run:
        return

    lnm_m = LNM_PACK / "manifests"
    _write_json(lnm_m / "zjh_train.json", lnm_train)
    _write_json(lnm_m / "zjh_test.json", lnm_test)
    _write_json(lnm_m / "zjh_dev_all.json", lnm_dev)
    _write_json(lnm_m / "train_combined_zjh_only.json", lnm_train)
    _write_json(lnm_m / "train_combined_zjh_plus_lymphus_c1.json", lnm_train)

    ftc_m = FTC_PACK / "manifests"
    _write_json(ftc_m / "zjh_train.json", ftc_train)
    _write_json(ftc_m / "zjh_test.json", ftc_test)
    _write_json(ftc_m / "zjh_dev_all.json", ftc_dev)

    _write_json(SPLIT_REGISTRY, registry)
    print(f"Wrote split registry: {SPLIT_REGISTRY}")


if __name__ == "__main__":
    main()
