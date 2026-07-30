#!/usr/bin/env python3
"""
分割筛选入口：单独跑分割 Agent。

对标 Segmentation_Agent/main.py，使用统一配置。
用法: python run_seg.py [--config config/config.yaml]
"""

from __future__ import annotations

import json
import os
import sys
import argparse
from pathlib import Path

import numpy as np
import yaml

from shared.image_io import ImageIO
from shared.llm_client import LLMClient
from segmentation import (
    SegModelRegistry,
    SegmentationQualityEvaluator,
    SegmentationAgent,
    build_performance_stats,
)
from segmentation.model_factory import build_seg_model


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_seg_registry(seg_cfg: dict, device: str = "cuda") -> SegModelRegistry:
    registry = SegModelRegistry()
    for m in seg_cfg.get("models", []):
        m = dict(m)
        m["device"] = device
        model = build_seg_model(m)
        model.load_model()
        registry.register_model(model)
    return registry


def main():
    parser = argparse.ArgumentParser(description="分割筛选")
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    config = load_config(args.config)
    llm_cfg = config["shared"]["agent_llm"]
    seg_cfg = config["segmentation"]
    data_cfg = config.get("pipeline", {}).get("data", {})

    # 检查是否需要 LLM
    enable_agent = seg_cfg.get("agent", {}).get("enable_agent", True)

    # 构建 LLM 客户端
    if enable_agent:
        api_key = os.getenv(llm_cfg["api_key_env"], "")
        llm_client = LLMClient(
            api_key=api_key,
            base_url=llm_cfg["base_url"],
            model_name=llm_cfg["model_name"],
            temperature=llm_cfg["temperature"],
            max_tokens=llm_cfg["max_tokens"],
        )
    else:
        print("✓ 分割 Agent 已禁用，跳过 LLM 客户端初始化")
        llm_client = None

    # 构建 radiomics judge（可选）
    judge = None
    judge_cfg = config.get("radiomics_judge", {})
    if judge_cfg.get("enabled", False):
        try:
            from radiomics_judge import RadiomicsJudge
            judge = RadiomicsJudge(
                model_dir=judge_cfg["model_dir"],
                top_k_features=judge_cfg.get("top_k_features", 5),
                shap_reference_path=judge_cfg.get("shap_reference_path"),
            )
            print("✓ Radiomics 裁判已加载")
        except Exception as e:
            print(f"⚠️ Radiomics 裁判加载失败（将不使用）: {e}")

    # 构建组件
    registry = build_seg_registry(seg_cfg, args.device)
    quality_evaluator = SegmentationQualityEvaluator()
    agent = SegmentationAgent(
        llm_client=llm_client,
        quality_evaluator=quality_evaluator,
        radiomics_judge=judge,
        config=seg_cfg.get("agent", {}),
    )

    image_io = ImageIO()
    image_dir = Path(data_cfg["image_input"])
    gt_mask_dir = data_cfg.get("gt_mask_dir")
    device_info = data_cfg.get("device_info")
    start_index = data_cfg.get("start_index", 0)
    max_images = data_cfg.get("max_images")

    exts = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
    images = sorted([f for f in image_dir.iterdir() if f.suffix.lower() in exts])
    if start_index > 0:
        images = images[start_index:]
    if max_images:
        images = images[:max_images]

    output_dir = Path(config.get("pipeline", {}).get("output", {}).get("output_dir", "output/seg"))
    output_dir.mkdir(parents=True, exist_ok=True)
    mask_dir = output_dir / "masks"
    mask_dir.mkdir(exist_ok=True)

    print(f"\n分割筛选: {len(images)} 张图像")

    results = []
    for i, img_path in enumerate(images):
        print(f"\n[{i+1}/{len(images)}] {img_path.name}")
        try:
            image = image_io.load_image(img_path)
            predictions = registry.predict_all(image)

            gt_mask = None
            if gt_mask_dir:
                gt_path = Path(gt_mask_dir) / img_path.name
                if gt_path.exists():
                    gt_mask = image_io.binarize_mask(image_io.load_mask(gt_path))

            decision = agent.select_best_mask(
                image, predictions,
                gt_mask=gt_mask,
                input_device_info=device_info,
            )

            image_io.save_mask(decision.selected_mask, str(mask_dir / img_path.name))

            result = decision.to_simplified_dict()
            result["image_name"] = img_path.name
            results.append(result)
            print(f"  ✓ {decision.selected_model} (conf={decision.confidence:.3f})")

        except Exception as e:
            print(f"  ✗ 失败: {e}")
            results.append({"image_name": img_path.name, "error": str(e)})

        if (i + 1) % 10 == 0:
            with open(output_dir / "results.json", "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

    # 最终保存 + 性能统计
    with open(output_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    stats = build_performance_stats(results)
    if stats:
        with open(output_dir / "performance_stats.json", "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"\n性能统计: {json.dumps(stats, ensure_ascii=False)}")

    print(f"\n完成: {len(results)} 张图像 → {output_dir}")


if __name__ == "__main__":
    main()
