#!/usr/bin/env python3
"""B1: check filename overlap between stacked train sets and external test sets."""

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


def stems_from_dir(images_dir: Path) -> set[str]:
    if not images_dir.exists():
        return set()
    return {p.stem for p in images_dir.iterdir() if p.is_file()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("/mnt/wangbd8/workspace/DataSets/ThyroidAgent"),
    )
    parser.add_argument("--out", type=Path, default=Path("docs/revision/b1/tables/train_test_overlap.json"))
    args = parser.parse_args()
    root = args.data_root

    stacks = {
        "dataset_3_train_images": root / "train_val_test/Superimposed_multitask/dataset_3/train/images",
        "dataset_4_train_images": root / "train_val_test/Superimposed_experiment/dataset_4/train/images",
    }
    tests = {
        "TN3K_test": root / "train_val_test/TN3K/test/images",
        "TN5K_test": root / "train_val_test/TN5K/test/images",
        "ThyroidXL_test": root / "train_val_test/ThyroidXL/test/images",
        "ZJH-8K_images": root / "train_val_test/ZJH-8K/images",
        "DDTI_test": root / "train_val_test/DDTI/test/images",
        "PKTN_test": root / "train_val_test/PKTN/test/images",
    }

    stack_stems = {k: stems_from_dir(p) for k, p in stacks.items()}
    test_stems = {k: stems_from_dir(p) for k, p in tests.items()}

    report: dict = {"stacks": {k: len(v) for k, v in stack_stems.items()}, "tests": {k: len(v) for k, v in test_stems.items()}, "overlap": {}}

    for tname, tst in test_stems.items():
        report["overlap"][tname] = {}
        for sname, sst in stack_stems.items():
            inter = tst & sst
            report["overlap"][tname][sname] = {
                "count": len(inter),
                "samples": sorted(inter)[:20],
            }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()

import importlib.util
from pathlib import Path


