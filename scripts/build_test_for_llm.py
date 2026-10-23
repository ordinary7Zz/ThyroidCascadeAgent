#!/usr/bin/env python3
"""构建 test_for_llm_<label_key> 等 LLM/消融用小子集（分层抽样或整集复制）。

用法: python scripts/build_test_for_llm.py --src .../TN3K/test --n 250
"""

from __future__ import annotations

import repo_path

repo_path.install()

import argparse
import json
import random
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Optional

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}


def _default_out_dir(split_root: Path, label_key: str) -> Path:
    tag = label_key.strip() or "malignancy"
    if split_root.name == "test":
        return split_root.parent / f"test_for_llm_{tag}"
    return split_root.parent / f"{split_root.name}_for_llm_{tag}"


def _find_label_file(split_root: Path, explicit: Optional[Path]) -> Optional[Path]:
    if explicit is not None:
        p = explicit if explicit.is_absolute() else (split_root / explicit)
        p = p.resolve()
        if not p.is_file():
            raise FileNotFoundError(f"label 文件不存在: {p}")
        return p
    candidates = sorted(
        p
        for p in split_root.glob("*.json")
        if p.is_file()
        and "checkpoint" not in p.name.lower()
        and "label" in p.name.lower()
        and "patient_map" not in p.name.lower()
    )
    return candidates[0] if candidates else None


def _load_labels(path: Path) -> tuple[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, list):
        return "list", raw
    if isinstance(raw, dict):
        return "dict", raw
    raise ValueError(f"不支持的 label JSON 类型: {type(raw)}")


def _stem_label_map(fmt: str, raw: Any, label_key: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if fmt == "list":
        for item in raw:
            if not isinstance(item, dict):
                continue
            fn = item.get("filename") or item.get("image") or item.get("name")
            if not fn:
                continue
            if label_key not in item:
                continue
            val = item[label_key]
            if val is None:
                continue
            out[Path(fn).stem] = val
    elif fmt == "dict":
        for k, v in raw.items():
            stem = Path(k).stem
            if isinstance(v, dict):
                if label_key in v and v[label_key] is not None:
                    out[stem] = v[label_key]
            elif v is not None:
                out[stem] = v
    return out


def _list_image_files(images_dir: Path) -> list[Path]:
    if not images_dir.is_dir():
        return []
    return sorted(
        [
            p
            for p in images_dir.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS and not p.name.startswith(".")
        ],
        key=lambda p: p.name,
    )


def _build_mask_index(masks_dir: Path) -> dict[str, Path]:
    """stem -> mask 路径（每 stem 取一个文件，扩展名可不同于 image）。"""
    index: dict[str, Path] = {}
    for p in masks_dir.iterdir():
        if not p.is_file() or p.name.startswith("."):
            continue
        prev = index.get(p.stem)
        if prev is None or p.suffix.lower() < prev.suffix.lower():
            index[p.stem] = p
    return index


def _find_mask_for_stem(mask_index: dict[str, Path], stem: str) -> Optional[Path]:
    return mask_index.get(stem)


def _allocate_stratified(class_counts: Counter, n: int) -> dict[Any, int]:
    if n <= 0:
        return {}
    total = sum(class_counts.values())
    if total == 0:
        return {}
    classes = list(class_counts.keys())
    raw = {c: n * class_counts[c] / total for c in classes}
    alloc = {c: int(raw[c]) for c in classes}
    rem = n - sum(alloc.values())
    order = sorted(classes, key=lambda c: raw[c] - alloc[c], reverse=True)
    for i in range(rem):
        alloc[order[i % len(order)]] += 1
    for c in classes:
        cap = class_counts[c]
        if alloc[c] > cap:
            surplus = alloc[c] - cap
            alloc[c] = cap
            for c2 in order:
                if surplus <= 0:
                    break
                room = class_counts[c2] - alloc[c2]
                if room <= 0:
                    continue
                take = min(room, surplus)
                alloc[c2] += take
                surplus -= take
    return alloc


def _stratified_sample(
    stems_by_class: dict[Any, list[str]],
    n: int,
    rng: random.Random,
) -> list[str]:
    counts = Counter({c: len(stems) for c, stems in stems_by_class.items()})
    alloc = _allocate_stratified(counts, min(n, sum(counts.values())))
    picked: list[str] = []
    for c, k in alloc.items():
        pool = list(stems_by_class[c])
        rng.shuffle(pool)
        picked.extend(pool[:k])
    if len(picked) < n:
        rest = [s for c, stems in stems_by_class.items() for s in stems if s not in picked]
        rng.shuffle(rest)
        picked.extend(rest[: n - len(picked)])
    return picked[:n]


def _filter_label_json(fmt: str, raw: Any, selected_stems: set[str]) -> Any:
    if fmt == "list":
        out = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            fn = item.get("filename") or item.get("image") or item.get("name")
            if fn and Path(fn).stem in selected_stems:
                out.append(item)
        return out
    return {k: v for k, v in raw.items() if Path(k).stem in selected_stems}


def build_subset(
    src: Path,
    n: int,
    *,
    images_dir_name: str = "images",
    masks_dir_name: Optional[str] = "masks",
    use_masks: bool = True,
    out_dir: Optional[Path] = None,
    label_file: Optional[Path] = None,
    label_key: str = "malignancy",
    seed: int = 42,
    dry_run: bool = False,
) -> dict[str, Any]:
    split_root = src.resolve()
    images_dir = split_root / images_dir_name
    if not images_dir.is_dir():
        raise FileNotFoundError(f"图像目录不存在: {images_dir}")

    masks_dir: Optional[Path] = None
    if use_masks and masks_dir_name:
        candidate = split_root / masks_dir_name
        if candidate.is_dir():
            masks_dir = candidate
        elif use_masks:
            raise FileNotFoundError(f"需要 mask 目录但未找到: {candidate}")

    out = (out_dir or _default_out_dir(split_root, label_key)).resolve()

    mask_index: dict[str, Path] = {}
    if masks_dir is not None:
        mask_index = _build_mask_index(masks_dir)

    entries: list[tuple[Path, Optional[Path], str]] = []
    for img in _list_image_files(images_dir):
        mask = _find_mask_for_stem(mask_index, img.stem) if masks_dir else None
        if masks_dir is not None and mask is None:
            continue
        entries.append((img, mask, img.stem))

    if not entries:
        raise RuntimeError(f"没有可用样本: {split_root} (images={images_dir_name}, masks={use_masks})")

    label_path = _find_label_file(split_root, label_file)
    stem_to_class: dict[str, Any] = {}
    label_fmt: Optional[str] = None
    label_raw: Any = None
    if label_path is not None:
        label_fmt, label_raw = _load_labels(label_path)
        stem_to_class = _stem_label_map(label_fmt, label_raw, label_key)

    pool_stems = [s for _, _, s in entries]
    n_population = len(pool_stems)
    n_requested = n

    copied_all = n_population <= n_requested
    use_stratified = False

    if copied_all:
        selected_stems = list(pool_stems)
    else:
        population_counts = Counter(stem_to_class[s] for s in pool_stems if s in stem_to_class)
        use_stratified = len(population_counts) >= 1 and sum(population_counts.values()) > 0
        rng = random.Random(seed)
        n_sample = n_requested

        if use_stratified:
            stratified_stems = [s for s in pool_stems if s in stem_to_class]
            if len(stratified_stems) < len(pool_stems):
                missing = len(pool_stems) - len(stratified_stems)
                print(f"  注意: {missing} 张样本 label 中无 {label_key}，分层时排除", file=sys.stderr)
            by_class: dict[Any, list[str]] = {}
            for s in stratified_stems:
                by_class.setdefault(stem_to_class[s], []).append(s)
            if not by_class:
                use_stratified = False
            else:
                selected_stems = _stratified_sample(by_class, n_sample, rng)
        if not use_stratified:
            pool = list(pool_stems)
            rng.shuffle(pool)
            selected_stems = pool[:n_sample]

    selected_set = set(selected_stems)
    stem_to_entry = {s: (img, mask) for img, mask, s in entries}

    report: dict[str, Any] = {
        "src": str(split_root),
        "out": str(out),
        "images_dir": images_dir_name,
        "masks_dir": masks_dir_name if masks_dir else None,
        "n_requested": n_requested,
        "n_selected": len(selected_stems),
        "copied_all": copied_all,
        "seed": seed,
        "label_file": str(label_path) if label_path else None,
        "label_key": label_key,
        "stratified": use_stratified and not copied_all,
        "total_pool": n_population,
        "class_counts_full": dict(Counter(stem_to_class[s] for s in pool_stems if s in stem_to_class))
        if stem_to_class
        else {},
        "class_counts_selected": dict(
            Counter(stem_to_class[s] for s in selected_stems if s in stem_to_class)
        )
        if stem_to_class
        else {},
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))

    if dry_run:
        return report

    if out.exists():
        raise FileExistsError(f"输出目录已存在，请删除或指定 --out: {out}")

    out_images = out / images_dir_name
    out_images.mkdir(parents=True)
    out_masks_path: Optional[Path] = None
    if masks_dir is not None:
        out_masks_path = out / masks_dir_name
        out_masks_path.mkdir(parents=True)

    for stem in selected_stems:
        img, mask = stem_to_entry[stem]
        shutil.copy2(img, out_images / img.name)
        if mask is not None and out_masks_path is not None:
            shutil.copy2(mask, out_masks_path / mask.name)

    if label_path and label_fmt and label_raw is not None:
        filtered = _filter_label_json(label_fmt, label_raw, selected_set)
        out_label = out / label_path.name
        with open(out_label, "w", encoding="utf-8") as f:
            json.dump(filtered, f, ensure_ascii=False, indent=2)
            f.write("\n")
        report["out_label"] = str(out_label)

    manifest = out / "subset_manifest.json"
    with open(manifest, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")

    unit = "对" if masks_dir else "张"
    print(f"✓ 已写入 {out}（{len(selected_stems)} {unit}）")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="构建 test_for_llm 分层子集")
    parser.add_argument("--src", required=True, type=Path, help="数据集根目录（含图像/掩膜/label）")
    parser.add_argument("--n", required=True, type=int, help="抽样数量")
    parser.add_argument("--images-dir", default="images", help="图像子目录名（相对 --src）")
    parser.add_argument(
        "--masks-dir",
        default="masks",
        help="掩膜子目录名；与 --no-masks 互斥时忽略",
    )
    parser.add_argument("--no-masks", action="store_true", help="仅分类：不复制 mask")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--label-key",
        default="malignancy",
        help="分层用的分类字段；默认输出目录名含该键，如 test_for_llm_malignancy",
    )
    parser.add_argument(
        "--label-file",
        type=Path,
        default=None,
        help="label JSON（相对 --src 或绝对路径）；默认自动查找 *label*.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="输出根目录（默认 test_for_llm_<label_key> 或 <split>_for_llm_<label_key>）",
    )
    parser.add_argument("--dry-run", action="store_true", help="只打印统计，不复制")
    args = parser.parse_args()

    if args.n < 1:
        parser.error("--n 须 >= 1")

    report = build_subset(
        args.src,
        args.n,
        images_dir_name=args.images_dir,
        masks_dir_name=args.masks_dir if not args.no_masks else None,
        use_masks=not args.no_masks,
        out_dir=args.out,
        label_file=args.label_file,
        label_key=args.label_key,
        seed=args.seed,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
