#!/usr/bin/env python3
"""
串联 Pipeline 入口：分割筛选 → 分类筛选。

待做文档任务1+2的完整实现：
  1. 分割 Agent 用 radiomics 裁判评估 pred mask 可信度
  2. 筛选后的 mask 喂给分类 Agent（mask_source="segmentation_agent_filtered"）
用法: python run_pipeline.py [--config config/config.yaml]
"""

from __future__ import annotations

import json
import os
import argparse
from pathlib import Path

import yaml

from shared.image_io import ImageIO
from shared.llm_client import LLMClient
from segmentation import (
    SegModelRegistry,
    SegmentationQualityEvaluator,
    SegmentationAgent,
)
from segmentation.model_factory import build_seg_model
from classification import (
    ClsModelRegistry,
    LLMClassificationAgent,
    load_calibration_map,
)
from classification.model_factory import build_cls_model
from radiomics_judge import RadiomicsJudge
from pipeline import CascadePipeline


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


def build_cls_registry(cls_cfg: dict, device: str = "cuda") -> ClsModelRegistry:
    cal_cfg = cls_cfg.get("calibration", {})
    cal_map = load_calibration_map(cal_cfg.get("artifacts_dir", "")) if cal_cfg.get("enabled") else {}

    registry = ClsModelRegistry(calibration_map=cal_map)
    for m in cls_cfg.get("models", []):
        m = dict(m)
        m["device"] = "cpu" if m.get("type") == "autogluon_radiomics" else device
        model = build_cls_model(m)
        model.load_model()
        registry.register_model(model)
    return registry


def main():
    parser = argparse.ArgumentParser(description="串联 Pipeline: 分割筛选 → 分类筛选")
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    config = load_config(args.config)
    llm_cfg = config["shared"]["agent_llm"]
    seg_cfg = config["segmentation"]
    cls_cfg = config["classification"]
    judge_cfg = config.get("radiomics_judge", {})
    pipe_cfg = config.get("pipeline", {})
    data_cfg = pipe_cfg.get("data", {})

    # LLM 客户端
    api_key = os.getenv(llm_cfg["api_key_env"], "")
    if not api_key:
        print("⚠️ 警告: API key 未设置（环境变量 %s）" % llm_cfg["api_key_env"])
    llm_client = LLMClient(
        api_key=api_key,
        base_url=llm_cfg["base_url"],
        model_name=llm_cfg["model_name"],
        temperature=llm_cfg["temperature"],
        max_tokens=llm_cfg["max_tokens"],
    )

    # Radiomics 裁判
    judge = None
    if judge_cfg.get("enabled", False):
        try:
            judge = RadiomicsJudge(
                model_dir=judge_cfg["model_dir"],
                top_k_features=judge_cfg.get("top_k_features", 5),
                shap_reference_path=judge_cfg.get("shap_reference_path"),
            )
            print("✓ Radiomics 裁判已加载")
        except Exception as e:
            print(f"⚠️ Radiomics 裁判加载失败: {e}")

    # 构建组件
    print("\n加载分割模型...")
    seg_registry = build_seg_registry(seg_cfg, args.device)
    print("\n加载分类模型...")
    cls_registry = build_cls_registry(cls_cfg, args.device)

    seg_agent = SegmentationAgent(
        llm_client=llm_client,
        quality_evaluator=SegmentationQualityEvaluator(),
        radiomics_judge=judge,
        config=seg_cfg.get("agent", {}),
    )
    cls_agent = LLMClassificationAgent(
        llm_client=llm_client,
        config=cls_cfg.get("agent", {}),
    )

    # 构建 Pipeline
    pipeline = CascadePipeline(
        seg_agent=seg_agent,
        cls_agent=cls_agent,
        seg_registry=seg_registry,
        cls_registry=cls_registry,
        image_io=ImageIO(),
        config=pipe_cfg.get("output", {}),
    )

    # 运行
    results = pipeline.run_batch(
        image_dir=data_cfg["image_input"],
        output_dir=pipe_cfg.get("output", {}).get("output_dir", "output/pipeline_run"),
        gt_mask_dir=data_cfg.get("gt_mask_dir"),
        label_file=data_cfg.get("label_file"),
        input_device_info=data_cfg.get("device_info"),
        start_index=data_cfg.get("start_index", 0),
        max_images=data_cfg.get("max_images"),
    )

    print(f"\nPipeline 完成: {len(results)} 张图像")


if __name__ == "__main__":
    main()
