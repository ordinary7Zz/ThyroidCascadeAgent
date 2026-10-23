#!/usr/bin/env python3
"""Build image → cluster_id maps for B2 patient-level bootstrap (ZJH-8K, ThyroidXL)."""

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


def thyroidxl_patient_id(filename: str) -> str:
    stem = Path(filename).stem
    prefix = "ThyroidXL_test_"
    if stem.startswith(prefix):
        stem = stem[len(prefix) :]
    parts = stem.split("_")
    if not parts:
        return stem
    return parts[0]


def zjh_patient_id(filename: str, name_to_pid: dict[str, str] | None) -> str:
    stem = Path(filename).stem
    parts = stem.split("_")
    head = parts[0]
    if head.startswith("P") and len(head) >= 2 and head[1:].isdigit():
        return head
    if name_to_pid and head in name_to_pid:
        return name_to_pid[head]
    return head


def load_labels_list(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return list(data.values())
    raise TypeError(f"Unsupported label JSON type: {type(data)}")


def build_thyroidxl_map(label_file: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in load_labels_list(label_file):
        fn = row["filename"]
        out[fn] = thyroidxl_patient_id(fn)
    return out


def build_zjh_map(label_file: Path, patient_map_file: Path) -> dict[str, str]:
    name_to_pid = json.loads(patient_map_file.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for row in load_labels_list(label_file):
        fn = row.get("filename") or row.get("image") or ""
        if not fn:
            continue
        out[fn] = zjh_patient_id(fn, name_to_pid)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Build B2 cluster maps (patient_id per image).")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("/mnt/wangbd8/workspace/DataSets/ThyroidAgent"),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("docs/revision/b2/cluster_maps"),
    )
    args = parser.parse_args()
    root = args.data_root
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    txl_labels = root / "train_val_test/ThyroidXL/test/ThyroidXL_test_label.json"
    txl_map = build_thyroidxl_map(txl_labels)
    txl_path = out_dir / "thyroidxl_test.json"
    txl_path.write_text(json.dumps(txl_map, indent=2, ensure_ascii=False), encoding="utf-8")

    zjh_labels = root / "train_val_test/ZJH-8K/ZJH-8K_BM_labels.json"
    zjh_pmap = root / "train_val_test/ZJH-8K/ZJH-8K_labels.json.patient_map.json"
    zjh_map = build_zjh_map(zjh_labels, zjh_pmap)
    zjh_path = out_dir / "zjh8k.json"
    zjh_path.write_text(json.dumps(zjh_map, indent=2, ensure_ascii=False), encoding="utf-8")

    txl_patients = len(set(txl_map.values()))
    zjh_patients = len(set(zjh_map.values()))
    print(f"Wrote {txl_path} ({len(txl_map)} images, {txl_patients} patients)")
    print(f"Wrote {zjh_path} ({len(zjh_map)} images, {zjh_patients} patients)")


if __name__ == "__main__":
    main()

import importlib.util
from pathlib import Path


