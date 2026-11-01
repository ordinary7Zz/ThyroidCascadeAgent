#!/usr/bin/env python3
"""Build ZJH exclude list: images with dHash H=0 to TN3K train (tab_dhash / R1 row)."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


def _bootstrap() -> None:
    p = Path(__file__).resolve()
    for d in [p.parent, *p.parents]:
        if d.name == "revision" and (d / "_path_setup.py").is_file():
            spec = importlib.util.spec_from_file_location("_rev_path_setup", d / "_path_setup.py")
            mod = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(mod)
            mod.bootstrap(__file__)
            return
    raise RuntimeError("revision _path_setup.py not found")


_bootstrap()

import numpy as np

_audit_path = Path(__file__).resolve().parent / "audit_near_duplicates.py"
_spec = importlib.util.spec_from_file_location("audit_near_duplicates", _audit_path)
_audit = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_audit)
dhash64 = _audit.dhash64
iter_images = _audit.iter_images


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test"),
    )
    parser.add_argument(
        "--out-manifest",
        type=Path,
        default=Path("docs/revision/b1/tables/zjh_excl_tn3k_train_dhash0_manifest.json"),
    )
    args = parser.parse_args()

    tn3k_train = args.data_root / "TN3K/train/images"
    zjh = args.data_root / "ZJH-8K/images"
    tpaths = iter_images(tn3k_train)
    th = np.array([dhash64(p) for p in tpaths], dtype=np.uint64)
    zpaths = iter_images(zjh)
    names: list[str] = []
    for p in zpaths:
        h = dhash64(p)
        if np.any(th == h):
            names.append(p.name)
    names = sorted(set(names))

    manifest = {
        "source": "TN3K train vs ZJH-8K images, dHash H=0 (matches tab_dhash TN3K train row)",
        "data_root": str(args.data_root.resolve()),
        "hamming_max": 0,
        "n_images": len(names),
        "images": names,
    }
    args.out_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.out_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(names)} exclude names -> {args.out_manifest}")


if __name__ == "__main__":
    main()
