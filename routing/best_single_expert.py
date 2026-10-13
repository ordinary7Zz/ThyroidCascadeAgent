"""验证集上为策略 1（best_single）选择最优分割/分类专家。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

import numpy as np

from shared.image_io import ImageIO


def _compare_models():
    from pipeline.compare_models import (
        eval_cls_predictions,
        eval_seg_masks,
        load_cls_model_json,
        load_labels,
        load_seg_model_masks,
    )
    return (
        eval_cls_predictions,
        eval_seg_masks,
        load_cls_model_json,
        load_labels,
        load_seg_model_masks,
    )


def _resolve_val_stems(
    config: dict,
    all_image_names: list[str],
) -> list[str]:
    """返回用于选参的图像 stem 列表（须在 intermediate 中存在）。"""
    ab = config.get("pipeline", {}).get("ablation", {}) or {}
    val_list = ab.get("val_list")
    val_ratio = ab.get("val_ratio")

    stems_from_names = {Path(n).stem for n in all_image_names}

    if val_list:
        if isinstance(val_list, str):
            path = Path(val_list)
            if path.is_file():
                with open(path, "r", encoding="utf-8") as f:
                    val_list = json.load(f)
        out = []
        for item in val_list:
            if isinstance(item, str):
                s = Path(item).stem
            else:
                s = str(item)
            if s in stems_from_names:
                out.append(s)
        if out:
            return sorted(set(out))

    if val_ratio is not None and 0 < float(val_ratio) < 1:
        names = sorted(stems_from_names)
        k = max(1, int(len(names) * float(val_ratio)))
        return names[:k]

    # 无划分时：用全部图像（仅适合 sample 调试；正式实验须在 yaml 写明 val_list）
    return sorted(stems_from_names)


def _image_names_for_stems(all_names: list[str], stems: Iterable[str]) -> list[str]:
    stem_set = set(stems)
    return [n for n in all_names if Path(n).stem in stem_set]


def select_best_seg_expert(
    intermediate_dir: Path,
    val_stems: list[str],
    gt_mask_dir: Path,
    image_io: Optional[ImageIO] = None,
) -> tuple[str, dict]:
    """在 val 上按平均 Dice 选一名分割专家。"""
    (
        _eval_cls,
        eval_seg_masks,
        _load_cls,
        _load_labels,
        load_seg_model_masks,
    ) = _compare_models()
    image_io = image_io or ImageIO()
    seg_dir = intermediate_dir / "seg"
    best_name = ""
    best_score = -1.0
    per_model: dict[str, dict] = {}

    for npz_path in sorted(seg_dir.glob("*.npz")):
        img_names, masks, model_name = load_seg_model_masks(npz_path)
        subset_names = _image_names_for_stems(img_names, val_stems)
        if not subset_names:
            continue
        idx = [img_names.index(n) for n in subset_names]
        sub_masks = [masks[i] for i in idx]
        metrics = eval_seg_masks(subset_names, sub_masks, gt_mask_dir, image_io)
        dice_block = metrics.get("dice")
        dice_mean = dice_block.get("mean") if isinstance(dice_block, dict) else dice_block
        if dice_mean is None:
            continue
        per_model[model_name] = metrics
        if dice_mean > best_score:
            best_score = dice_mean
            best_name = model_name

    if not best_name:
        raise RuntimeError("无法在 val 上为分割选专家（检查 intermediate/seg 与 val_list）")
    return best_name, per_model


def select_best_cls_expert(
    intermediate_dir: Path,
    val_stems: list[str],
    label_file: str,
    label_key: str = "malignancy",
) -> tuple[str, dict]:
    """在 val 上按 AUROC 选一名独立分类专家。"""
    (
        eval_cls_predictions,
        _eval_seg,
        load_cls_model_json,
        load_labels,
        _load_seg,
    ) = _compare_models()
    labels = load_labels(label_file, label_key)
    cls_dir = intermediate_dir / "cls"
    best_name = ""
    best_score = -1.0
    per_model: dict[str, dict] = {}

    for json_path in sorted(cls_dir.glob("*.json")):
        img_to_pred, model_name = load_cls_model_json(json_path)
        metrics = eval_cls_predictions(img_to_pred, labels, subset_stems=set(val_stems))
        auroc = metrics.get("auroc")
        if isinstance(auroc, dict):
            score = float(auroc.get("mean", -1.0))
        elif auroc is not None:
            score = float(auroc)
        else:
            acc = metrics.get("accuracy")
            score = float(acc) if acc is not None else -1.0
        per_model[model_name] = metrics
        if score > best_score:
            best_score = score
            best_name = model_name

    if not best_name:
        raise RuntimeError("无法在 val 上为分类选专家（检查 intermediate/cls 与 label_file）")
    return best_name, per_model


def fit_best_single_on_val(
    config: dict,
    intermediate_dir: Path,
    *,
    gt_mask_dir: Path,
    label_file: str,
    label_key: str = "malignancy",
    artifact_path: Optional[Path] = None,
) -> dict:
    """
    在验证集上选 seg/cls 专家，写入 artifact JSON 并注入 config.pipeline.ablation。
    """
    seg_dir = intermediate_dir / "seg"
    (
        _eval_cls,
        _eval_seg,
        _load_cls,
        _load_labels,
        load_seg_model_masks,
    ) = _compare_models()
    sample_npz = next(seg_dir.glob("*.npz"), None)
    if sample_npz is None:
        raise FileNotFoundError(f"无分割 npz: {seg_dir}")
    img_names, _, _ = load_seg_model_masks(sample_npz)
    val_stems = _resolve_val_stems(config, img_names)

    image_io = ImageIO()
    seg_name, seg_metrics = select_best_seg_expert(
        intermediate_dir, val_stems, gt_mask_dir, image_io
    )
    cls_name, cls_metrics = select_best_cls_expert(
        intermediate_dir, val_stems, label_file, label_key
    )

    payload = {
        "val_stems": val_stems,
        "best_single_seg": seg_name,
        "best_single_cls": cls_name,
        "seg_val_metrics": seg_metrics,
        "cls_val_metrics": cls_metrics,
        "intermediate_dir": str(intermediate_dir),
    }

    if artifact_path:
        artifact_path = Path(artifact_path)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        with open(artifact_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    ab = config.setdefault("pipeline", {}).setdefault("ablation", {})
    ab["best_single_seg"] = seg_name
    ab["best_single_cls"] = cls_name
    return payload


def load_best_single_artifact(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def apply_best_single_artifact(config: dict, artifact: dict) -> dict:
    ab = config.setdefault("pipeline", {}).setdefault("ablation", {})
    ab["best_single_seg"] = artifact.get("best_single_seg")
    ab["best_single_cls"] = artifact.get("best_single_cls")
    return config
