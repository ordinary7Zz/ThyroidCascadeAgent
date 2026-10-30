#!/usr/bin/env python3
"""R4 表：在 cohorts_test_fit 的 flag 下计算全集/保留子集 mean Dice（与 pipeline evaluate 同口径）。"""

from __future__ import annotations

import importlib.util
import json
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

import argparse

import numpy as np
import repo_path
import yaml

repo_path.install()

from segmentation.metrics import compute_dice
from shared.image_io import ImageIO

# 与主 pipeline_run（B3 外测）一致，勿用 B6 llm 子集 mask 目录
COHORT_PIPELINE: dict[str, tuple[str, str]] = {
    "tn3k": ("output/TN3K/pipeline_run", "config/revision/b3/tn3k.yaml"),
    "tn5k": ("output/TN5K/pipeline_run", "config/revision/b3/tn5k.yaml"),
    "thyroidxl": ("output/ThyroidXL/pipeline_run", "config/revision/b3/thyroidxl.yaml"),
    "zjh8k": ("output/ZJH-8K/pipeline_run", "config/revision/b3/zjh8k.yaml"),
    "ddti_cls": ("output/DDTI_cls/pipeline_run", "config/revision/b3/ddti_cls.yaml"),
    "ddti_seg": ("output/DDTI_seg/pipeline_run", "config/revision/b3/ddti_seg.yaml"),
    "pktn": ("output/PKTN/pipeline_run", "config/revision/b3/pktn.yaml"),
    "rjh7k": ("output/RJH-7K/pipeline_run", "config/revision/b3/rjh7k.yaml"),
}

COHORT_LABEL = {
    "tn3k": "TN3K",
    "tn5k": "TN5K",
    "thyroidxl": "ThyroidXL",
    "zjh8k": "ZJH-8K",
    "ddti_cls": "DDTI",
    "ddti_seg": "DDTI (seg)",
    "pktn": "PKTN",
    "rjh7k": "RJH-7K",
}


def _gt_mask_dir(config_path: Path) -> str:
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    for key in ("pipeline", "eval"):
        block = cfg.get(key) or {}
        data = block.get("data") or {}
        gt = (data.get("gt_mask_dir") or "").strip()
        if gt:
            return gt
    data = cfg.get("data") or {}
    return (data.get("gt_mask_dir") or "").strip()


def _gt_stem_map(gt_dir: Path) -> dict[str, Path]:
    if not gt_dir.is_dir():
        return {}
    return {p.stem: p for p in gt_dir.iterdir() if p.is_file()}


def dice_all_retained(
    pipeline_dir: Path,
    gt_mask_dir: Path,
    flagged_by_name: dict[str, bool],
) -> tuple[float | None, float | None, int, int]:
    sel_path = pipeline_dir / "intermediate" / "selected_masks.npz"
    if not sel_path.is_file():
        return None, None, 0, 0
    gt_map = _gt_stem_map(gt_mask_dir)
    if not gt_map:
        return None, None, 0, 0

    data = np.load(str(sel_path), allow_pickle=True)
    img_names = list(data["image_names"])
    masks = list(data["selected_masks"])
    io = ImageIO()

    all_d: list[float] = []
    ret_d: list[float] = []
    for img_name, pred in zip(img_names, masks):
        stem = Path(str(img_name)).stem
        gt_path = gt_map.get(stem)
        if gt_path is None or not gt_path.exists():
            continue
        gt = io.binarize_mask(io.load_mask(gt_path))
        pred_m = np.asarray(pred).astype(bool)
        d = float(compute_dice(pred_m, gt))
        if np.isnan(d):
            continue
        all_d.append(d)
        name = str(img_name)
        if not flagged_by_name.get(name, flagged_by_name.get(Path(name).name, False)):
            ret_d.append(d)

    def mean(xs: list[float]) -> float | None:
        return float(np.mean(xs)) if xs else None

    return mean(all_d), mean(ret_d), len(all_d), len(ret_d)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fit-root",
        type=Path,
        default=Path("output/b8/cohorts_test_fit"),
    )
    parser.add_argument(
        "--flagged-json",
        default="results_flagged.json",
        help="各 cohort 子目录下的 flag 文件（如 results_flagged_fake.json）",
    )
    args = parser.parse_args()
    rows = []
    for cohort, (rel_pipe, rel_cfg) in COHORT_PIPELINE.items():
        pipe = Path(rel_pipe)
        cfg = Path(rel_cfg)
        flagged_path = args.fit_root / cohort / args.flagged_json
        if not flagged_path.is_file():
            print(f"skip {cohort}: no {flagged_path}")
            continue
        flagged_rows = json.loads(flagged_path.read_text(encoding="utf-8"))
        flagged_by_name: dict[str, bool] = {}
        for r in flagged_rows:
            name = r.get("image_name") or Path(r.get("path", "")).name
            flagged_by_name[name] = bool(r.get("flagged_for_review"))
            flagged_by_name[Path(name).name] = bool(r.get("flagged_for_review"))

        gt_dir_s = _gt_mask_dir(cfg)
        gt_dir = Path(gt_dir_s) if gt_dir_s else Path()
        d_all, d_ret, n_all, n_ret = dice_all_retained(pipe, gt_dir, flagged_by_name)
        label = COHORT_LABEL[cohort]
        rows.append(
            {
                "cohort": cohort,
                "label": label,
                "dice_all": d_all,
                "dice_retained": d_ret,
                "n_dice": n_all,
                "n_dice_retained": n_ret,
            }
        )
        da = "---" if d_all is None else f"{d_all:.4f}"
        dr = "---" if d_ret is None else f"{d_ret:.4f}"
        print(f"{label}: Dice={da} Dice(ret)={dr} (n={n_all}/{n_ret})")

    out = args.fit_root / "r4_dice_summary.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ {out}")


if __name__ == "__main__":
    main()
