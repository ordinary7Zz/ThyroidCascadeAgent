#!/usr/bin/env python3
"""
分类筛选入口：单独跑分类 Agent。

对标 Classification_Agent/main.py，使用统一配置。
mask 来源为外部（config 的 data.mask_input）。
用法: python run_cls.py [--config config/config.yaml]
"""

from __future__ import annotations

import json
import os
import argparse
from pathlib import Path

import numpy as np
import yaml

from shared.image_io import ImageIO
from shared.llm_client import LLMClient
from classification import (
    ClsModelRegistry,
    LLMClassificationAgent,
    compute_roc_auc,
    compute_accuracy,
    bootstrap_auc_ci95,
    load_calibration_map,
)
from classification.model_factory import build_cls_model


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_cls_registry(cls_cfg: dict, device: str = "cuda") -> ClsModelRegistry:
    cal_cfg = cls_cfg.get("calibration", {})
    cal_map = {}
    if cal_cfg.get("enabled", False):
        cal_map = load_calibration_map(cal_cfg.get("artifacts_dir", ""))

    registry = ClsModelRegistry(calibration_map=cal_map)

    for m in cls_cfg.get("models", []):
        m = dict(m)
        m["device"] = "cpu" if m.get("type") == "autogluon_radiomics" else device
        model = build_cls_model(m)
        model.load_model()
        registry.register_model(model)

    return registry


def main():
    parser = argparse.ArgumentParser(description="分类筛选")
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    config = load_config(args.config)
    llm_cfg = config["shared"]["agent_llm"]
    cls_cfg = config["classification"]
    data_cfg = config.get("pipeline", {}).get("data", {})

    api_key = os.getenv(llm_cfg["api_key_env"], "")
    llm_client = LLMClient(
        api_key=api_key,
        base_url=llm_cfg["base_url"],
        model_name=llm_cfg["model_name"],
        temperature=llm_cfg["temperature"],
        max_tokens=llm_cfg["max_tokens"],
    )

    registry = build_cls_registry(cls_cfg, args.device)
    agent = LLMClassificationAgent(
        llm_client=llm_client,
        config=cls_cfg.get("agent", {}),
    )

    image_io = ImageIO()
    image_dir = Path(data_cfg["image_input"])
    mask_dir_input = Path(data_cfg.get("mask_input", data_cfg["image_input"]))
    label_file = data_cfg.get("label_file")
    device_info = data_cfg.get("device_info")
    start_index = data_cfg.get("start_index", 0)
    max_images = data_cfg.get("max_images")

    labels = {}
    if label_file and Path(label_file).exists():
        with open(label_file, "r", encoding="utf-8") as f:
            labels = json.load(f)

    exts = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
    images = sorted([f for f in image_dir.iterdir() if f.suffix.lower() in exts])
    if start_index > 0:
        images = images[start_index:]
    if max_images:
        images = images[:max_images]

    output_dir = Path(config.get("pipeline", {}).get("output", {}).get("output_dir", "output/cls"))
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n分类筛选: {len(images)} 张图像")

    results = []
    for i, img_path in enumerate(images):
        print(f"\n[{i+1}/{len(images)}] {img_path.name}")
        try:
            image = image_io.load_image(img_path)
            mask = None
            mask_path = mask_dir_input / img_path.name
            if mask_path.exists():
                mask = image_io.load_mask(mask_path)

            predictions = registry.predict_all(image, mask)
            decision = agent.select_best_model(
                predictions,
                mask_source="external",
                input_device_info=device_info,
            )

            result = decision.to_dict()
            result["image_name"] = img_path.name
            if img_path.name in labels:
                result["true_label"] = labels[img_path.name]
            results.append(result)
            print(f"  ✓ {decision.selected_class} (conf={decision.confidence:.3f})")

        except Exception as e:
            print(f"  ✗ 失败: {e}")
            results.append({"image_name": img_path.name, "error": str(e)})

        if (i + 1) % 10 == 0:
            with open(output_dir / "results.json", "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

    with open(output_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 评估（如果有标签）
    labeled = [r for r in results if "true_label" in r and "selected_class" in r]
    if labeled:
        true_labels = np.array([1 if r["true_label"] == "恶性" else 0 for r in labeled])
        pred_probs = np.array([r["confidence"] if r["selected_class"] == "恶性" else 1 - r["confidence"] for r in labeled])
        pred_labels = np.array([1 if r["selected_class"] == "恶性" else 0 for r in labeled])

        roc = compute_roc_auc(true_labels, pred_probs)
        acc = compute_accuracy(true_labels, pred_labels)
        ci = bootstrap_auc_ci95(true_labels, pred_probs)

        eval_result = {"auc": roc["auc"], "accuracy": acc, "ci95": list(ci) if ci else None}
        with open(output_dir / "evaluation.json", "w", encoding="utf-8") as f:
            json.dump(eval_result, f, ensure_ascii=False, indent=2)
        print(f"\n评估: AUC={roc['auc']:.4f}, Acc={acc:.4f}, CI95={ci}")

    print(f"\n完成: {len(results)} 张图像 → {output_dir}")


if __name__ == "__main__":
    main()
