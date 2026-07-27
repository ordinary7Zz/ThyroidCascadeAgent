"""
串联 Pipeline：分割筛选 → 分类筛选。

待做文档任务2核心：分割 Agent 筛选出的 mask 喂给分类 Agent。
CascadePipeline.run_single 实现：
  1. seg_registry.predict_all(image) → 多个分割预测
  2. seg_agent.select_best_mask(image, seg_predictions) → 筛选 + radiomics 裁判
  3. 取筛后 mask → cls_registry.predict_all(image, selected_mask) → 多个分类预测
  4. cls_agent.select_best_model(cls_predictions)
  5. 返回 {seg_decision, selected_mask, cls_decision, final_label}
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

import numpy as np

from shared.image_io import ImageIO
from segmentation.agent import SegmentationAgent, SegAgentDecision
from segmentation.model_registry import SegModelRegistry
from classification.agent import LLMClassificationAgent, ClsAgentDecision
from classification.model_registry import ClsModelRegistry


class CascadePipeline:
    """串联分割筛选与分类筛选。"""

    def __init__(
        self,
        seg_agent: SegmentationAgent,
        cls_agent: LLMClassificationAgent,
        seg_registry: SegModelRegistry,
        cls_registry: ClsModelRegistry,
        image_io: ImageIO,
        config: Optional[dict] = None,
    ):
        self.seg_agent = seg_agent
        self.cls_agent = cls_agent
        self.seg_registry = seg_registry
        self.cls_registry = cls_registry
        self.image_io = image_io
        self.config = config or {}

    def run_single(
        self,
        image: np.ndarray,
        gt_mask: Optional[np.ndarray] = None,
        input_device_info: Optional[list[str]] = None,
        input_data_info: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        对单张图执行级联推理。

        Args:
            image: (H, W, 3) RGB uint8 [0,255]。
            gt_mask: 可选 GT mask（仅用于评估）。
            input_device_info: 输入设备信息。
            input_data_info: 输入数据元信息。

        Returns:
            {
                'seg_decision': dict,
                'selected_mask_shape': tuple,
                'cls_decision': dict,
                'final_label': str,
                'final_confidence': float,
            }
        """
        # ===== Phase A: 分割筛选 =====
        seg_predictions = self.seg_registry.predict_all(image)
        if not seg_predictions:
            raise RuntimeError("分割模型全部失败，无法继续")

        seg_decision: SegAgentDecision = self.seg_agent.select_best_mask(
            image,
            seg_predictions,
            gt_mask=gt_mask,
            input_device_info=input_device_info,
            input_data_info=input_data_info,
        )

        selected_mask = seg_decision.selected_mask

        # ===== Phase B: 分类筛选 =====
        cls_predictions = self.cls_registry.predict_all(image, selected_mask)
        if not cls_predictions:
            raise RuntimeError("分类模型全部失败，无法继续")

        cls_decision: ClsAgentDecision = self.cls_agent.select_best_model(
            cls_predictions,
            input_device_info=input_device_info,
            input_data_info=input_data_info,
        )

        return {
            "seg_decision": seg_decision.to_simplified_dict(),
            "selected_mask_shape": selected_mask.shape,
            "selected_mask_area": int(np.sum(selected_mask)),
            "cls_decision": cls_decision.to_dict(),
            "final_label": cls_decision.selected_class,
            "final_confidence": cls_decision.confidence,
        }

    def run_batch(
        self,
        image_dir: str,
        output_dir: str,
        gt_mask_dir: Optional[str] = None,
        label_file: Optional[str] = None,
        input_device_info: Optional[list[str]] = None,
        input_data_info: Optional[dict] = None,
        start_index: int = 0,
        max_images: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """
        批量级联推理。

        Args:
            image_dir: 输入图像目录。
            output_dir: 输出目录。
            gt_mask_dir: 可选 GT mask 目录（用于评估）。
            label_file: 可选标签文件（JSON，{image_name: label}）。
            input_device_info: 输入设备信息。
            input_data_info: 输入数据元信息。
            start_index: 起始索引（断点续跑）。
            max_images: 最大处理数量（None=全部）。
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        mask_out = out_path / "masks"
        if self.config.get("save_masks", True):
            mask_out.mkdir(parents=True, exist_ok=True)

        # 加载标签
        labels: dict[str, Any] = {}
        if label_file:
            with open(label_file, "r", encoding="utf-8") as f:
                labels = json.load(f)

        # 收集图像
        img_dir = Path(image_dir)
        exts = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
        images = sorted(
            [f for f in img_dir.iterdir() if f.suffix.lower() in exts],
            key=lambda x: x.name,
        )

        if start_index > 0:
            images = images[start_index:]
        if max_images is not None:
            images = images[:max_images]

        print(f"级联推理: {len(images)} 张图像 (start={start_index})")

        results: list[dict[str, Any]] = []
        for i, img_path in enumerate(images):
            img_name = img_path.name
            print(f"\n[{i + 1}/{len(images)}] {img_name}")

            try:
                image = self.image_io.load_image(img_path)

                # 加载 GT mask（如果有）
                gt_mask = None
                if gt_mask_dir:
                    gt_path = Path(gt_mask_dir) / img_name
                    if gt_path.exists():
                        gt_mask = self.image_io.binarize_mask(self.image_io.load_mask(gt_path))

                result = self.run_single(
                    image,
                    gt_mask=gt_mask,
                    input_device_info=input_device_info,
                    input_data_info=input_data_info,
                )
                result["image_name"] = img_name
                result["image_file"] = str(img_path)

                # 添加真实标签（如果有）
                if img_name in labels:
                    result["true_label"] = labels[img_name]

                # 保存 mask
                if self.config.get("save_masks", True):
                    self.image_io.save_mask(
                        result["seg_decision"].get("selected_mask", image[:, :, 0] * 0),
                        str(mask_out / img_name),
                    )

                results.append(result)

            except Exception as e:
                print(f"  ✗ 处理失败: {e}")
                import traceback

                traceback.print_exc()
                results.append({
                    "image_name": img_name,
                    "image_file": str(img_path),
                    "error": str(e),
                })

            # 增量保存
            if (i + 1) % 10 == 0 or i == len(images) - 1:
                self._save_results(results, out_path / "results.json")
                print(f"  已保存 {len(results)} 条结果")

        # 最终保存
        self._save_results(results, out_path / "results.json")
        print(f"\n级联推理完成: {len(results)} 张图像")
        return results

    @staticmethod
    def _save_results(results: list[dict], path: Path) -> None:
        """保存结果到 JSON。"""
        serializable = []
        for r in results:
            s = {}
            for k, v in r.items():
                if isinstance(v, np.ndarray):
                    s[k] = v.tolist()
                elif isinstance(v, (np.integer, np.floating)):
                    s[k] = float(v)
                else:
                    s[k] = v
            serializable.append(s)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2)
