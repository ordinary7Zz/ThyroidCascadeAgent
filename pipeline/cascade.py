"""
串联 Pipeline：4 步级联推理。

Step 1: 跑 3 个独立分类模型 → 判断共识（无 LLM）
Step 2: 跑 5 个分割模型 + Radiomics 裁判 + quality_evaluator
Step 3: 分割 Agent 选 mask（含/不含分类锚点）
Step 4: 分类裁决（Path A 直接输出 / Path B 规则+LLM）

agent_enabled=true  → Step 3 调 LLM, Step 4 可能调 LLM
agent_enabled=false → Step 3/4 纯规则（不调 LLM）
"""

from __future__ import annotations

import json
import time
from collections import Counter
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
        self.output_cfg = config.get("pipeline", {}).get("output", {}) if config else {}

    def run_single(
        self,
        image: np.ndarray,
        gt_mask: Optional[np.ndarray] = None,
        input_device_info: Optional[list[str]] = None,
        input_data_info: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        Step 1-4 级联推理流程。

        Args:
            image: (H, W, 3) RGB uint8 [0,255]。
            gt_mask: 可选 GT mask（仅用于评估）。
            input_device_info: 输入设备信息。
            input_data_info: 输入数据元信息。

        Returns:
            {path, consensus, seg_decision, cls_decision, final_label, final_confidence}
        """
        cls_cfg = self.config.get("classification", {}).get("agent", {})
        seg_cfg = self.config.get("segmentation", {}).get("agent", {})
        enable_seg_agent = seg_cfg.get("enable_agent", True)
        enable_cls_agent = cls_cfg.get("enable_agent", True)
        consensus_threshold = cls_cfg.get("consensus_min_confidence", 0.6)

        # ===== Step 1: 分类共识判断（只跑独立模型，无 LLM）=====
        indie_preds = self._get_independent_classification_predictions(image)
        consensus, anchor_class = self._check_classification_consensus(
            indie_preds, min_confidence=consensus_threshold
        )

        # ===== Step 2: 分割 + Radiomics 裁判 =====
        seg_predictions = self.seg_registry.predict_all(image)
        if not seg_predictions:
            raise RuntimeError("分割模型全部失败，无法继续")

        if enable_seg_agent:
            # LLM 路径
            seg_decision: SegAgentDecision = self.seg_agent.select_best_mask(
                image, seg_predictions,
                classification_anchor=anchor_class,
                gt_mask=gt_mask,
                input_device_info=input_device_info,
                input_data_info=input_data_info,
            )
        else:
            # 静态规则路径
            seg_decision = self._select_mask_static(
                image, seg_predictions, anchor_class,
                gt_mask=gt_mask,
                input_device_info=input_device_info,
                input_data_info=input_data_info,
            )

        selected_mask = seg_decision.selected_mask

        # ===== Step 3: 分割已完成，分类裁决 =====
        if consensus:
            cls_decision = self._make_anchor_classification_decision(anchor_class, indie_preds)
        else:
            autogluon_pred = self._run_autogluon_classification(image, selected_mask)
            if enable_cls_agent:
                cls_decision = self.cls_agent.resolve_path_b(
                    indie_preds, autogluon_pred, seg_decision
                )
            else:
                cls_decision = self._resolve_classification_path_b_static(
                    indie_preds, autogluon_pred
                )

        return {
            "path": "A" if consensus else "B",
            "classification_consensus": consensus,
            "seg_decision": seg_decision.to_simplified_dict(),
            "selected_mask": selected_mask,  # 供 run_batch 保存用
            "selected_mask_shape": selected_mask.shape,
            "selected_mask_area": int(np.sum(selected_mask)),
            "cls_decision": cls_decision.to_dict(),
            "final_label": cls_decision.selected_class,
            "final_confidence": cls_decision.confidence,
        }

    # ===== Step 1 辅助方法 =====

    def _get_independent_classification_predictions(
        self, image: np.ndarray
    ) -> list:
        """Step 1: 只跑 requires_mask=False 的独立分类模型。"""
        preds = []
        for name, model in self.cls_registry.get_independent_models():
            try:
                preds.append(model.predict(image, mask=None))
            except Exception as e:
                print(f"  ✗ 独立分类模型 {name} 失败: {e}")
        return preds

    @staticmethod
    def _check_classification_consensus(predictions, min_confidence=0.6):
        """判断独立分类模型是否有共识。

        Returns:
            (consensus: bool, anchor_class: str | None)
        """
        if len(predictions) < 2:
            return False, None
        classes = [p.top_class for p in predictions]
        confs = [p.top_confidence for p in predictions]
        if len(set(classes)) == 1 and min(confs) > min_confidence:
            return True, classes[0]
        return False, None

    @staticmethod
    def _make_anchor_classification_decision(
        anchor_class, indie_preds
    ) -> "ClsAgentDecision":
        """Path A: 分类模型一致 → 直接用锚点。"""
        best = max(indie_preds, key=lambda p: p.top_confidence)
        min_conf = min(p.top_confidence for p in indie_preds)
        reasoning = (
            f"独立分类模型一致预测为「{anchor_class}」"
            f"(conf={min_conf:.2f}~{best.top_confidence:.2f})，直接采纳。"
        )
        return ClsAgentDecision(
            selected_model="independent_consensus",
            selected_class=anchor_class,
            confidence=float(best.top_confidence),
            reasoning=reasoning,
            all_predictions=[p.to_dict() for p in indie_preds],
            method="classification_consensus",
        )

    # ===== Step 3 静态规则 =====

    def _select_mask_static(
        self, image, seg_predictions, anchor_class,
        gt_mask=None, input_device_info=None, input_data_info=None
    ) -> "SegAgentDecision":
        """
        静态规则选择最佳分割 mask。

        Path A: 锚点过滤 → average_agreement 最高
        Path B: 直接 average_agreement 最高
        """
        from segmentation.agent import SegAgentDecision

        # 构造 name → pred 映射
        pred_map = {p.model_name: p for p in seg_predictions}
        names = [p.model_name for p in seg_predictions]
        masks = [p.mask for p in seg_predictions]
        preds_list = list(seg_predictions)

        # 用内部 quality_evaluator 计算（复用 SegmentationAgent 的）
        quality_results = self.seg_agent.quality_evaluator.evaluate_batch(masks, names)
        agreement_dict = (
            quality_results.get("agreement_metrics", {})
            .get("average_agreement", {})
        )

        # Path A: 锚点过滤
        remaining_names = set(names)
        if anchor_class:
            judge_results = self.seg_agent._run_judge(image, preds_list)
            if judge_results:
                anchor_numeric = 1 if anchor_class == "恶性" else 0
                for p in preds_list:
                    j = judge_results[preds_list.index(p)] if judge_results else {}
                    if (j.get("valid") and j.get("confidence", 0) > 0.6
                            and abs(j.get("malignant_prob", 0.5) - anchor_numeric) > 0.4):
                        remaining_names.discard(p.model_name)
                if not remaining_names:
                    remaining_names = set(names)  # 全被排除了，回退

        # 选 agreement 最高的
        best_name = max(remaining_names, key=lambda n: agreement_dict.get(n, 0))
        best_pred = pred_map[best_name]
        best_idx = names.index(best_name)

        quality = quality_results["individual_quality"][best_idx]
        agreement = agreement_dict.get(best_name, 0) if agreement_dict else None
        reason = (
            f"静态规则：{best_name}（average_agreement={agreement:.2f}）"
            if agreement else f"静态规则：{best_name}"
        )
        if anchor_class:
            reason += f"，与分类锚点「{anchor_class}」吻合"

        return SegAgentDecision(
            selected_model=best_name,
            selected_mask=best_pred.mask,
            confidence=agreement or 0.5,
            reasoning=reason,
            all_predictions=[p.to_dict() for p in preds_list],
            quality_metrics=quality,
            agreement_score=agreement,
            is_ensemble=False,
            classification_anchor=anchor_class,
            path="A" if anchor_class else "B",
        )

    # ===== Step 4 辅助方法 =====

    def _run_autogluon_classification(self, image, mask):
        """Path B: 用选定 mask 跑 AutoGluon 分类。"""
        for name, model in self.cls_registry.get_mask_dependent_models():
            try:
                return model.predict(image, mask)
            except Exception as e:
                print(f"  ✗ AutoGluon 分类失败 ({name}): {e}")
        return None

    @staticmethod
    def _resolve_classification_path_b_static(
        indie_preds, autogluon_pred
    ) -> "ClsAgentDecision":
        """Path B 静态分类裁决：多数派 vs AutoGluon 比较。"""
        classes = [p.top_class for p in indie_preds]
        majority = Counter(classes).most_common(1)[0][0]

        if autogluon_pred is not None:
            al_class = autogluon_pred.top_class
            al_conf = autogluon_pred.top_confidence

            # 一致
            if al_class == majority:
                return ClsAgentDecision(
                    selected_model="autogluon_majority_agree",
                    selected_class=al_class,
                    confidence=float(al_conf),
                    reasoning=f"独立模型多数派={majority}，AutoGluon一致({al_conf:.2f})",
                    all_predictions=[p.to_dict() for p in indie_preds],
                    method="path_b_static_majority",
                )
            # AutoGluon 强信号
            if al_conf > 0.8:
                return ClsAgentDecision(
                    selected_model="autogluon_strong_signal",
                    selected_class=al_class,
                    confidence=float(al_conf),
                    reasoning=f"AutoGluon高置信({al_conf:.2f})，信ROI级特征",
                    all_predictions=[p.to_dict() for p in indie_preds],
                    method="path_b_static_autogluon",
                )

        # 退回到多数派
        best = max(indie_preds, key=lambda p: p.top_confidence)
        return ClsAgentDecision(
            selected_model="majority_fallback",
            selected_class=majority,
            confidence=float(best.top_confidence),
            reasoning=f"独立模型无共识(多数派={majority})，退回多数派投票",
            all_predictions=[p.to_dict() for p in indie_preds],
            method="path_b_static_fallback",
        )

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
        if self.output_cfg.get("save_masks", True):
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
                if self.output_cfg.get("save_masks", True):
                    self.image_io.save_mask(
                        result.get("selected_mask", np.zeros_like(image[:, :, 0], dtype=np.uint8)),
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
