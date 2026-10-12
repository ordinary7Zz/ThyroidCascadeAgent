"""
B6：在复用 intermediate 缓存的前提下，对 LLM 路由重复 N 次并汇总一致率（按 disagreement_tier 分层）。
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Optional

import numpy as np

from shared.routing_log import seg_disagreement_tier
from segmentation.metrics import compute_dice


def _agreement_rate(choices: list[str]) -> float:
    if not choices:
        return float("nan")
    counts = Counter(choices)
    return float(max(counts.values())) / len(choices)


def _summarize_repeats(
    per_case: list[dict[str, Any]],
) -> dict[str, Any]:
    by_tier: dict[str, list[float]] = defaultdict(list)
    all_agree = []
    for row in per_case:
        tier = row.get("disagreement_tier", "unknown")
        ar = row.get("selection_agreement")
        if ar is not None and not np.isnan(ar):
            by_tier[tier].append(ar)
            all_agree.append(ar)
    stratified = {
        tier: {
            "n_cases": len(vals),
            "mean_selection_agreement": float(np.mean(vals)) if vals else None,
        }
        for tier, vals in by_tier.items()
    }
    return {
        "n_cases": len(per_case),
        "mean_selection_agreement": float(np.mean(all_agree)) if all_agree else None,
        "by_disagreement_tier": stratified,
        "per_case": per_case,
    }


def run_stability_from_caches(
    *,
    image_io,
    seg_agent,
    cls_agent,
    image_paths: list[Path],
    img_names: list[str],
    seg_model_configs: list[dict],
    cls_model_configs: list[dict],
    seg_cache_dir: Path,
    cls_cache_dir: Path,
    load_seg_npz,
    load_cls_json,
    check_classification_consensus,
    consensus_threshold: float,
    enable_seg_agent: bool,
    enable_cls_agent: bool,
    device_info: Optional[list[str]],
    gt_mask_dir: Optional[str],
    repeats: int = 5,
    max_cases: Optional[int] = None,
    output_path: Optional[Path] = None,
) -> dict[str, Any]:
    """
    对每张图：若分割 Agent 开启则 5× select_best_mask；
    若分类无共识且 cls agent 开启则 5× resolve_path_b（需先有 seg 决策，用静态 agreement 选 mask 作 stub）。
    """
    from classification.base_model import ClsModelOutput
    from segmentation.agent import SegAgentDecision

    if max_cases is not None:
        image_paths = image_paths[:max_cases]
        img_names = img_names[:max_cases]

    seg_cache_by_model: dict[str, list] = {}
    for model_cfg in seg_model_configs:
        model_name = model_cfg.get("name", "")
        cache_path = seg_cache_dir / f"{model_name}.npz"
        if cache_path.exists():
            seg_cache_by_model[model_name] = load_seg_npz(cache_path, load_confidence=enable_seg_agent)

    cls_cache_by_model: dict[str, list] = {}
    for model_cfg in cls_model_configs:
        model_name = model_cfg.get("name", "")
        cache_path = cls_cache_dir / f"{model_name}.json"
        if cache_path.exists():
            cls_cache_by_model[model_name] = load_cls_json(cache_path)

    per_case: list[dict[str, Any]] = []

    for idx, img_name in enumerate(img_names):
        img_path = image_paths[idx]
        image = image_io.load_image(img_path)

        seg_preds = []
        for model_cfg in seg_model_configs:
            model_name = model_cfg.get("name", "")
            cache = seg_cache_by_model.get(model_name)
            if cache is not None and idx < len(cache):
                seg_preds.append(cache[idx])

        indie_preds = []
        for model_cfg in cls_model_configs:
            model_name = model_cfg.get("name", "")
            cache = cls_cache_by_model.get(model_name)
            if cache is not None and idx < len(cache):
                indie_preds.append(cache[idx])

        consensus, anchor_class = check_classification_consensus(
            indie_preds, min_confidence=consensus_threshold
        )

        gt_mask = None
        if gt_mask_dir:
            gt_path = Path(gt_mask_dir) / img_name
            if gt_path.exists():
                gt_mask = image_io.binarize_mask(image_io.load_mask(gt_path))

        judge_results = None
        judge_obj = getattr(seg_agent, "radiomics_judge", None)
        if judge_obj is not None and seg_preds:
            try:
                judge_results = judge_obj.judge_batch(image, [p.mask for p in seg_preds])
            except Exception:
                judge_results = None

        quality_results = None
        if seg_preds:
            masks = [p.mask for p in seg_preds]
            names = [p.model_name for p in seg_preds]
            quality_results = seg_agent.quality_evaluator.evaluate_batch(masks, names)
        tier = seg_disagreement_tier(quality_results)

        row: dict[str, Any] = {
            "image_name": img_name,
            "classification_consensus": consensus,
            "disagreement_tier": tier,
        }

        if enable_seg_agent and seg_preds:
            seg_choices = []
            dice_vals = []
            for _ in range(repeats):
                dec = seg_agent.select_best_mask(
                    image,
                    seg_preds,
                    classification_anchor=anchor_class,
                    gt_mask=gt_mask,
                    input_device_info=device_info,
                    judge_results=judge_results,
                    image_name=img_name,
                )
                seg_choices.append(dec.selected_model)
                if gt_mask is not None:
                    dice_vals.append(float(compute_dice(dec.selected_mask, gt_mask)))
            row["seg_selection_agreement"] = _agreement_rate(seg_choices)
            row["seg_selected_models"] = seg_choices
            if dice_vals:
                row["seg_dice_std"] = float(np.std(dice_vals))
                row["seg_dice_range"] = float(max(dice_vals) - min(dice_vals))

        if enable_cls_agent and indie_preds and not consensus:
            static_dec = seg_agent._fallback_selection(
                seg_preds,
                gt_mask,
                quality_results,
                judge_results,
                anchor_class,
            ) if seg_preds and quality_results else None
            if static_dec is None and seg_preds:
                static_dec = SegAgentDecision(
                    selected_model=seg_preds[0].model_name,
                    selected_mask=seg_preds[0].mask,
                    confidence=0.5,
                    reasoning="stability stub",
                    all_predictions=[p.to_dict() for p in seg_preds],
                    path="B",
                )
            cls_choices = []
            for _ in range(repeats):
                dec = cls_agent.resolve_path_b(
                    indie_preds,
                    None,
                    static_dec,
                    voting_weights=None,
                    image_name=img_name,
                )
                cls_choices.append(dec.selected_class)
            row["cls_selection_agreement"] = _agreement_rate(cls_choices)
            row["cls_selected_classes"] = cls_choices

        primary = row.get("seg_selection_agreement") or row.get("cls_selection_agreement")
        row["selection_agreement"] = primary
        per_case.append(row)

    summary = _summarize_repeats(per_case)
    summary["repeats"] = repeats
    summary["enable_seg_agent"] = enable_seg_agent
    summary["enable_cls_agent"] = enable_cls_agent

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

    return summary
