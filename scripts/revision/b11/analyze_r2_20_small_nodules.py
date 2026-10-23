#!/usr/bin/env python3
"""
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

R2.20(b): GT 小结节统计 + 与 pipeline selected mask 的 Dice。

GT 最大径（等价直径）= 2 * sqrt(foreground_area / pi)，在原图分辨率下计算。
若提供 --mm-per-pixel，则用 d_mm = d_px * mm_per_pixel 与 --max-diameter-mm（默认 5）筛选。

输出 JSON + 可选 CSV，供 B11 回复与补充表填写。
"""

from __future__ import annotations

import importlib.util
from pathlib import Path



import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

import repo_path
_REPO = repo_path.find_repo_root()
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from shared.image_io import ImageIO


def compute_dice(pred_mask: np.ndarray, gt_mask: np.ndarray) -> float:
    pred = pred_mask.astype(bool)
    gt = gt_mask.astype(bool)
    intersection = np.logical_and(pred, gt).sum()
    union = pred.sum() + gt.sum()
    if union == 0:
        return 1.0 if intersection == 0 else 0.0
    return float((2.0 * intersection) / union)


def _equiv_diameter_px(mask_bool: np.ndarray) -> float:
    area = float(mask_bool.sum())
    if area <= 0:
        return 0.0
    return 2.0 * np.sqrt(area / np.pi)


def _load_selected_masks(npz_path: Path) -> dict[str, np.ndarray]:
    data = np.load(npz_path, allow_pickle=True)
    names = list(data["image_names"])
    masks = list(data["selected_masks"])
    out: dict[str, np.ndarray] = {}
    for name, m in zip(names, masks):
        key = Path(str(name)).name
        out[key] = np.asarray(m)
    return out


def _stem_map(mask_dir: Path) -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    if not mask_dir.is_dir():
        return mapping
    for p in mask_dir.iterdir():
        if p.is_file():
            mapping[p.stem] = p
    return mapping


def analyze(
    gt_mask_dir: Path,
    selected_npz: Path,
    mm_per_pixel: float | None,
    max_diameter_mm: float,
    min_component_px: int,
) -> dict:
    io = ImageIO()
    pred_map = _load_selected_masks(selected_npz)
    gt_stems = _stem_map(gt_mask_dir)

    rows: list[dict] = []
    for stem, gt_path in sorted(gt_stems.items()):
        gt = io.binarize_mask(io.load_mask(gt_path))
        d_px = _equiv_diameter_px(gt)
        d_mm = (d_px * mm_per_pixel) if mm_per_pixel else None

        pred = pred_map.get(f"{stem}.jpg")
        if pred is None:
            pred = pred_map.get(f"{stem}.png")
        if pred is None:
            for k, v in pred_map.items():
                if Path(k).stem == stem:
                    pred = v
                    break
        if pred is None:
            continue

        pred_bin = (np.asarray(pred) > 0).astype(bool)
        dice = compute_dice(pred_bin, gt.astype(bool))
        pred_empty = pred_bin.sum() == 0

        rows.append(
            {
                "stem": stem,
                "gt_equiv_diameter_px": round(d_px, 2),
                "gt_equiv_diameter_mm": round(d_mm, 3) if d_mm is not None else None,
                "dice": round(float(dice), 4),
                "pred_empty": bool(pred_empty),
            }
        )

    if mm_per_pixel is None:
        small = []
    else:
        small = [r for r in rows if r["gt_equiv_diameter_mm"] is not None and r["gt_equiv_diameter_mm"] < max_diameter_mm]

    failed = [r for r in small if r["pred_empty"] or r["dice"] < 0.1]
    small_dice = [r["dice"] for r in small if not np.isnan(r["dice"])]

    # 敏感性：GT 前景面积小于直径 min_component_px 的圆盘面积（对应 DINO 专家 50px 规则量级）
    area_thresh = np.pi * (min_component_px / 2.0) ** 2
    tiny_gt = [r for r in rows if r["gt_equiv_diameter_px"] < min_component_px]

    summary = {
        "gt_mask_dir": str(gt_mask_dir),
        "selected_masks_npz": str(selected_npz),
        "n_matched": len(rows),
        "mm_per_pixel": mm_per_pixel,
        "max_diameter_mm": max_diameter_mm,
        "n_gt_below_max_diameter_mm": len(small),
        "n_pred_fail_small": len(failed),
        "mean_dice_small_gt": float(np.mean(small_dice)) if small_dice else None,
        "min_component_px_dino_postprocess": min_component_px,
        "n_gt_foreground_area_below_min_component_disk": len(tiny_gt),
        "note": (
            "Radiomics path has no extra CCA; Dice uses selected_masks. "
            "d_mm requires --mm-per-pixel (cohort-specific; confirm with B1/clinical spacing)."
        ),
    }
    return {"summary": summary, "rows": rows, "small_subset": small, "small_failures": failed}


def main() -> None:
    parser = argparse.ArgumentParser(description="R2.20 small-nodule stats for B11")
    parser.add_argument("--gt-mask-dir", type=Path, required=True)
    parser.add_argument("--selected-npz", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mm-per-pixel", type=float, default=None)
    parser.add_argument("--max-diameter-mm", type=float, default=5.0)
    parser.add_argument("--min-component-px", type=int, default=50)
    args = parser.parse_args()

    result = analyze(
        args.gt_mask_dir,
        args.selected_npz,
        args.mm_per_pixel,
        args.max_diameter_mm,
        args.min_component_px,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    s = result["summary"]
    print(json.dumps(s, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
