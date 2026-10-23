#!/usr/bin/env python3
"""B1: perceptual-hash near-duplicate screen (64-bit difference hash, Pillow only).

import importlib.util
from pathlib import Path

Typical use:
  python scripts/revision/b1/audit_near_duplicates.py --preset all
  python scripts/revision/b1/audit_near_duplicates.py --preset tn3k_zjh --hamming-max 5

Outputs JSON under docs/revision/b1/tables/ for Methods / Supp.
"""

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
from typing import Iterable

import numpy as np
from PIL import Image
from tqdm import tqdm

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def iter_images(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    out: list[Path] = []
    for p in directory.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES:
            out.append(p)
    return sorted(out)


def unique_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for p in paths:
        key = p.resolve()
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def dedupe_pairs(pairs: list[dict]) -> list[dict]:
    seen: set[tuple[int, str, str]] = set()
    out: list[dict] = []
    for p in pairs:
        key = (p["hamming"], p["left"], p["right"])
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def dhash64(path: Path, hash_size: int = 8) -> int:
    with Image.open(path) as im:
        im = im.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
        px = list(im.getdata())
    bits = 0
    idx = 0
    for row in range(hash_size):
        base = row * (hash_size + 1)
        for col in range(hash_size):
            if px[base + col] > px[base + col + 1]:
                bits |= 1 << idx
            idx += 1
    return bits


def popcount_u64(x: np.ndarray) -> np.ndarray:
    x = x.astype(np.uint64, copy=False)
    x = x - ((x >> np.uint64(1)) & np.uint64(0x5555555555555555))
    x = (x & np.uint64(0x3333333333333333)) + ((x >> np.uint64(2)) & np.uint64(0x3333333333333333))
    x = (x + (x >> np.uint64(4))) & np.uint64(0x0f0f0f0f0f0f0f0f)
    return (x * np.uint64(0x0101010101010101)) >> np.uint64(56)


def hash_paths(paths: Iterable[Path], desc: str) -> tuple[list[str], np.ndarray]:
    names: list[str] = []
    hashes: list[int] = []
    for p in tqdm(list(paths), desc=desc, unit="img"):
        try:
            hashes.append(dhash64(p))
            names.append(p.name)
        except Exception as exc:  # noqa: BLE001 — audit script, skip corrupt files
            tqdm.write(f"skip {p}: {exc}")
    return names, np.array(hashes, dtype=np.uint64)


def find_pairs(
    left_names: list[str],
    left_h: np.ndarray,
    right_names: list[str],
    right_h: np.ndarray,
    hamming_max: int,
    chunk: int = 256,
) -> list[dict]:
    """Pairs with left from set A, right from set B (cross-set only)."""
    pairs: list[dict] = []
    if len(left_h) == 0 or len(right_h) == 0:
        return pairs

    for start in range(0, len(right_h), chunk):
        rh = right_h[start : start + chunk]
        rn = right_names[start : start + chunk]
        diff = rh[:, None] ^ left_h[None, :]
        dist = popcount_u64(diff).astype(np.int16)
        for i in range(dist.shape[0]):
            js = np.where(dist[i] <= hamming_max)[0]
            for j in js:
                pairs.append(
                    {
                        "hamming": int(dist[i, j]),
                        "left": left_names[int(j)],
                        "right": rn[i],
                    }
                )
    pairs.sort(key=lambda x: (x["hamming"], x["left"], x["right"]))
    return pairs


def summarize_pairs(pairs: list[dict], hamming_max: int) -> dict:
    pairs = dedupe_pairs(pairs)
    exact = sum(1 for p in pairs if p["hamming"] == 0)
    near = sum(1 for p in pairs if 0 < p["hamming"] <= hamming_max)
    return {
        "pair_count": len(pairs),
        "exact_hamming_0": exact,
        "near_only": near,
        "unique_left_images": len({p["left"] for p in pairs}),
        "unique_right_images": len({p["right"] for p in pairs}),
        "top_samples": pairs[:50],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("/mnt/wangbd8/workspace/DataSets/ThyroidAgent"),
    )
    parser.add_argument("--hamming-max", type=int, default=5, help="Max Hamming distance (64-bit dHash)")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("docs/revision/b1/tables/near_duplicates.json"),
    )
    parser.add_argument(
        "--preset",
        choices=("train_vs_tests", "tn3k_zjh", "stacked_vs_zjh", "all"),
        default="all",
    )
    parser.add_argument(
        "--export-pairs-dir",
        type=Path,
        default=None,
        help="Write full deduped pair lists as <label>.pairs.json (for exclude-list export)",
    )
    args = parser.parse_args()
    root = args.data_root / "train_val_test"

    stacks = {
        "dataset_3_train": root / "Superimposed_multitask/dataset_3/train/images",
        "dataset_4_train": root / "Superimposed_experiment/dataset_4/train/images",
    }
    tests = {
        "TN3K_test": root / "TN3K/test/images",
        "TN5K_test": root / "TN5K/test/images",
        "ThyroidXL_test": root / "ThyroidXL/test/images",
        "ZJH-8K": root / "ZJH-8K/images",
        "DDTI_test": root / "DDTI/test/images",
        "PKTN_test": root / "PKTN/test/images",
    }
    tn3k_splits = [
        root / "TN3K/train/images",
        root / "TN3K/valid/images",
        root / "TN3K/test/images",
    ]

    report: dict = {
        "method": "64-bit difference hash (dHash), grayscale resize; Hamming threshold configurable",
        "hamming_max": args.hamming_max,
        "comparisons": {},
    }

    def write_pairs_file(label: str, pairs: list[dict]) -> None:
        if args.export_pairs_dir is None:
            return
        args.export_pairs_dir.mkdir(parents=True, exist_ok=True)
        deduped = dedupe_pairs(pairs)
        out_path = args.export_pairs_dir / f"{label}.pairs.json"
        out_path.write_text(json.dumps(deduped, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {len(deduped)} pairs -> {out_path}")

    def record_comparison(label: str, left_dir: str, right_dir: str, left_n: int, right_n: int, pairs: list[dict]) -> None:
        write_pairs_file(label, pairs)
        report["comparisons"][label] = {
            "left_dir": left_dir,
            "right_dir": right_dir,
            "left_n": left_n,
            "right_n": right_n,
            **summarize_pairs(pairs, args.hamming_max),
        }

    def run_comparison(label: str, left_dir: Path, right_dir: Path) -> None:
        left_paths = iter_images(left_dir)
        right_paths = iter_images(right_dir)
        ln, lh = hash_paths(left_paths, f"hash {label} left")
        rn, rh = hash_paths(right_paths, f"hash {label} right")
        pairs = find_pairs(ln, lh, rn, rh, args.hamming_max)
        record_comparison(label, str(left_dir), str(right_dir), len(ln), len(rn), pairs)

    stack_ln: np.ndarray | None = None
    stack_lh: np.ndarray | None = None
    stack_paths: list[Path] = []

    def ensure_stack_hashes() -> tuple[list[str], np.ndarray]:
        nonlocal stack_ln, stack_lh, stack_paths
        if stack_ln is None:
            stack_paths = unique_paths([p for d in stacks.values() for p in iter_images(d)])
            stack_ln, stack_lh = hash_paths(stack_paths, "hash stacked train")
        return stack_ln, stack_lh

    if args.preset in ("train_vs_tests", "stacked_vs_zjh", "all"):
        sln, slh = ensure_stack_hashes()
        cohorts = tests.items() if args.preset != "stacked_vs_zjh" else [("ZJH-8K", tests["ZJH-8K"])]
        for tname, tdir in cohorts:
            rn, rh = hash_paths(iter_images(tdir), f"hash {tname}")
            pairs = find_pairs(sln, slh, rn, rh, args.hamming_max)
            record_comparison(
                f"stacked_train_vs_{tname}",
                "dataset_3+4 train (stacked)",
                str(tdir),
                len(sln),
                len(rn),
                pairs,
            )

    if args.preset in ("tn3k_zjh", "all"):
        tn3k_paths = unique_paths([p for d in tn3k_splits for p in iter_images(d)])
        zjh_dir = tests["ZJH-8K"]
        ln, lh = hash_paths(tn3k_paths, "hash TN3K splits")
        rn, rh = hash_paths(iter_images(zjh_dir), "hash ZJH-8K")
        pairs = find_pairs(ln, lh, rn, rh, args.hamming_max)
        report["comparisons"]["TN3K_splits_vs_ZJH-8K"] = {
            "left_dir": "TN3K train+valid+test/images",
            "right_dir": str(zjh_dir),
            "left_n": len(ln),
            "right_n": len(rn),
            **summarize_pairs(pairs, args.hamming_max),
        }
        run_comparison("TN3K_test_vs_ZJH-8K", tests["TN3K_test"], tests["ZJH-8K"])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "comparisons"}, indent=2))
    for k, v in report["comparisons"].items():
        print(f"{k}: pairs={v['pair_count']} exact={v['exact_hamming_0']} near={v['near_only']}")
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
