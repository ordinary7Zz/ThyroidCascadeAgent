#!/usr/bin/env python3
"""Copy ZJH-8K 6807 subset (full pool minus TN3K train dHash H=0) into images_6807 / masks_6807."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

DEFAULT_ZJH_ROOT = Path("/mnt/wangbd8/workspace/DataSets/ThyroidAgent/train_val_test/ZJH-8K")
DEFAULT_EXCLUDE_MANIFEST = (
    Path(__file__).resolve().parents[3]
    / "docs/revision/b1/tables/zjh_excl_tn3k_train_dhash0_manifest.json"
)
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _copy_verified(src: Path, dst: Path) -> None:
    shutil.copy2(src, dst)
    if dst.stat().st_size != src.stat().st_size:
        raise OSError(f"size mismatch after copy: {dst} ({dst.stat().st_size} vs {src.stat().st_size})")
    if dst.suffix.lower() == ".png":
        with dst.open("rb") as f:
            if f.read(len(PNG_MAGIC)) != PNG_MAGIC:
                raise OSError(f"not a valid PNG after copy: {dst}")


def load_exclude_names(manifest_path: Path) -> set[str]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    names = data.get("images") or []
    if not names:
        raise SystemExit(f"Empty exclude list in {manifest_path}")
    return set(names)


def materialize(
    zjh_root: Path,
    exclude_manifest: Path,
    *,
    images_dir_name: str = "images_6807",
    masks_dir_name: str = "masks_6807",
    dry_run: bool = False,
) -> dict:
    src_images = zjh_root / "images"
    src_masks = zjh_root / "masks"
    dst_images = zjh_root / images_dir_name
    dst_masks = zjh_root / masks_dir_name

    if not src_images.is_dir():
        raise SystemExit(f"Missing {src_images}")
    if not src_masks.is_dir():
        raise SystemExit(f"Missing {src_masks}")
    if not exclude_manifest.is_file():
        raise SystemExit(f"Missing exclude manifest: {exclude_manifest}")

    exclude = load_exclude_names(exclude_manifest)

    if not dry_run:
        dst_images.mkdir(parents=True, exist_ok=True)
        dst_masks.mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped_excluded = 0
    missing_mask: list[str] = []

    for img_path in sorted(src_images.iterdir()):
        if not img_path.is_file() or img_path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        if img_path.name in exclude:
            skipped_excluded += 1
            continue

        mask_path = src_masks / f"{img_path.stem}.png"
        if not mask_path.is_file():
            missing_mask.append(img_path.name)
            continue

        out_img = dst_images / img_path.name
        out_mask = dst_masks / mask_path.name
        if not dry_run:
            _copy_verified(img_path, out_img)
            _copy_verified(mask_path, out_mask)
        copied += 1

    return {
        "zjh_root": str(zjh_root),
        "exclude_manifest": str(exclude_manifest),
        "n_exclude": len(exclude),
        "n_copied": copied,
        "n_skipped_excluded": skipped_excluded,
        "n_missing_mask": len(missing_mask),
        "missing_mask_examples": missing_mask[:10],
        "dst_images": str(dst_images),
        "dst_masks": str(dst_masks),
        "dry_run": dry_run,
    }


def verify_or_repair(
    zjh_root: Path,
    exclude_manifest: Path,
    *,
    images_dir_name: str = "images_6807",
    masks_dir_name: str = "masks_6807",
    repair: bool = False,
) -> dict:
    """Check subset copies; optionally re-copy files that are missing, empty, or size-mismatched."""
    src_images = zjh_root / "images"
    src_masks = zjh_root / "masks"
    dst_images = zjh_root / images_dir_name
    dst_masks = zjh_root / masks_dir_name
    exclude = load_exclude_names(exclude_manifest)

    bad_images: list[str] = []
    bad_masks: list[str] = []
    repaired = 0

    for img_path in sorted(src_images.iterdir()):
        if not img_path.is_file() or img_path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        if img_path.name in exclude:
            continue
        out_img = dst_images / img_path.name
        mask_path = src_masks / f"{img_path.stem}.png"
        out_mask = dst_masks / mask_path.name

        def _needs_fix(dst: Path, src: Path, *, png: bool) -> bool:
            if not dst.is_file() or dst.stat().st_size == 0:
                return True
            if dst.stat().st_size != src.stat().st_size:
                return True
            if png:
                with dst.open("rb") as f:
                    return f.read(len(PNG_MAGIC)) != PNG_MAGIC
            return False

        if _needs_fix(out_img, img_path, png=False):
            bad_images.append(img_path.name)
            if repair:
                _copy_verified(img_path, out_img)
                repaired += 1
        if _needs_fix(out_mask, mask_path, png=True):
            bad_masks.append(mask_path.name)
            if repair:
                _copy_verified(mask_path, out_mask)
                repaired += 1

    return {
        "n_bad_images": len(bad_images),
        "n_bad_masks": len(bad_masks),
        "bad_image_examples": bad_images[:10],
        "bad_mask_examples": bad_masks[:10],
        "repaired": repaired,
        "repair": repair,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zjh-root", type=Path, default=DEFAULT_ZJH_ROOT)
    parser.add_argument("--exclude-manifest", type=Path, default=DEFAULT_EXCLUDE_MANIFEST)
    parser.add_argument("--images-dir-name", default="images_6807")
    parser.add_argument("--masks-dir-name", default="masks_6807")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="只检查 images_6807/masks_6807 是否与源文件一致（大小 + PNG 头）",
    )
    parser.add_argument(
        "--repair",
        action="store_true",
        help="与 --verify 合用：自动重拷损坏/空文件",
    )
    args = parser.parse_args()

    if args.verify or args.repair:
        rep = verify_or_repair(
            args.zjh_root.resolve(),
            args.exclude_manifest.resolve(),
            images_dir_name=args.images_dir_name,
            masks_dir_name=args.masks_dir_name,
            repair=args.repair,
        )
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        if rep["n_bad_images"] or rep["n_bad_masks"]:
            if not args.repair:
                raise SystemExit("subset 存在损坏副本，请加 --repair 或重新运行本脚本（无 --verify）")
        return

    stats = materialize(
        args.zjh_root.resolve(),
        args.exclude_manifest.resolve(),
        images_dir_name=args.images_dir_name,
        masks_dir_name=args.masks_dir_name,
        dry_run=args.dry_run,
    )

    print(json.dumps(stats, indent=2, ensure_ascii=False))
    if stats["n_missing_mask"]:
        raise SystemExit(f"{stats['n_missing_mask']} images in subset lack masks (see missing_mask_examples)")
    if stats["n_copied"] != 6807:
        print(
            f"⚠ expected 6807 copies, got {stats['n_copied']} "
            f"(exclude list has {stats['n_exclude']} names, skipped {stats['n_skipped_excluded']})"
        )


if __name__ == "__main__":
    main()
