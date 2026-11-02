#!/usr/bin/env python3
"""Build B9 manifests + image_roots aligned with pyradiomics binary_class/my_run.md."""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT_MANIFESTS = REPO / "docs/revision/b9/manifests"
OUT_DATA = REPO / "docs/revision/b9/data"

LYMPHUS_ROOT = Path(
    "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/Classifaction_Data/Lymph_Node_Metastasis_fake"
)
LYMPHUS_TRAIN_LABELS = LYMPHUS_ROOT / "LymphUs_train_labels.json"
LYMPHUS_TEST_LABELS = LYMPHUS_ROOT / "LymphUs_test_labels.json"

MAL_CROPPED = Path(
    "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/Classifaction_Data/Malignant_ultrasound_images_cropped"
)
FTC_TRAIN_LABELS = Path(
    "/mnt/wangbd8/workspace/ThyroidAgent/dino_unet_multitask/my_json/train_labels_filtered_by_csv.json"
)
FTC_TEST_LABELS = Path(
    "/mnt/wangbd8/workspace/ThyroidAgent/dino_unet_multitask/my_json/test_labels_filtered_by_csv.json"
)
FTC_MASK_ROOT = Path(
    "/mnt/wangbd8/workspace/DataSets/ThyroidAgent/Classifaction_Data/Malignant_ultrasound_images_cropped_predictions"
)


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _enrich_lymphus(rows: list[dict]) -> list[dict]:
    out: list[dict] = []
    for row in rows:
        fn = str(row["filename"]).replace("\\", "/")
        out.append(
            {
                "filename": fn,
                "LNM_CN01": int(row["LNM_CN01"]),
                "image_root_key": "lymphus",
                "source": "lymphus_predmask",
            }
        )
    return out


def _enrich_ftc(rows: list[dict]) -> list[dict]:
    out: list[dict] = []
    for row in rows:
        fn = str(row["filename"]).replace("\\", "/")
        ftc = row.get("FTCPTC", -1)
        try:
            ftc = int(ftc)
        except (TypeError, ValueError):
            ftc = -1
        if ftc not in (0, 1):
            continue
        out.append(
            {
                "filename": fn,
                "FTCPTC": ftc,
                "malignancy": 1,
                "image_root_key": "malignant",
                "source": "ftcptc_malignant_filtered",
            }
        )
    return out


def main() -> None:
    lnm_train = _enrich_lymphus(json.loads(LYMPHUS_TRAIN_LABELS.read_text(encoding="utf-8")))
    lnm_test = _enrich_lymphus(json.loads(LYMPHUS_TEST_LABELS.read_text(encoding="utf-8")))
    ftc_train = _enrich_ftc(json.loads(FTC_TRAIN_LABELS.read_text(encoding="utf-8")))
    ftc_test = _enrich_ftc(json.loads(FTC_TEST_LABELS.read_text(encoding="utf-8")))

    _write_json(OUT_MANIFESTS / "lnm_lymphus_predmask_train.json", lnm_train)
    _write_json(OUT_MANIFESTS / "lnm_lymphus_predmask_test.json", lnm_test)
    _write_json(OUT_MANIFESTS / "ftcptc_filtered_train.json", ftc_train)
    _write_json(OUT_MANIFESTS / "ftcptc_filtered_test.json", ftc_test)

    _write_json(
        OUT_DATA / "lnm_lymphus_predmask_image_roots.json",
        {"lymphus": str(LYMPHUS_ROOT / "images")},
    )
    _write_json(
        OUT_DATA / "ftcptc_filtered_image_roots.json",
        {"malignant": str(MAL_CROPPED)},
    )

    meta = {
        "source_doc": "dino_unet_multitask/pyradiomics_train/binary_class/my_run.md",
        "lnm_train_n": len(lnm_train),
        "lnm_test_n": len(lnm_test),
        "ftc_train_n": len(ftc_train),
        "ftc_test_n": len(ftc_test),
    }
    _write_json(OUT_DATA / "my_run_manifest_meta.json", meta)
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
