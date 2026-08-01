"""
串联 Pipeline：5 阶段级联推理（按需加载/卸载模型）。

Phase 1: 依次加载分割模型 → 推理全部图像 → 保存 npz → 卸载
Phase 2: 依次加载独立分类模型 → 推理全部图像 → 保存 json → 卸载
Phase 3: 从缓存加载结果 → 分割 Agent 选 mask → 保存 selected_masks.npz
Phase 4: AutoGluon 加载 → 推理无共识图像 → 保存 json → 卸载
Phase 5: 分类裁决 + 保存 results.json

agent_enabled=true  → Phase 3 调 LLM, Phase 5 可能调 LLM
agent_enabled=false → Phase 3/5 纯规则（不调 LLM）
"""

from __future__ import annotations

import json
import pickle
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
    """串联分割筛选与分类筛选（按需加载/卸载模型）。"""

    def __init__(
        self,
        seg_agent: SegmentationAgent,
        cls_agent: LLMClassificationAgent,
        seg_registry: Optional[SegModelRegistry] = None,
        cls_registry: Optional[ClsModelRegistry] = None,
        image_io: ImageIO = None,
        config: Optional[dict] = None,
        device: str = "cuda",
    ):
        self.seg_agent = seg_agent
        self.cls_agent = cls_agent
        self.seg_registry = seg_registry
        self.cls_registry = cls_registry
        self.image_io = image_io or ImageIO()
        self.config = config or {}
        self.output_cfg = config.get("pipeline", {}).get("output", {}) if config else {}
        self.device = device

    # ===== 缓存读写工具 =====

    @staticmethod
    def _save_seg_npz(
        path: Path,
        image_names: list[str],
        seg_outputs: list,
    ) -> None:
        """将一个分割模型对所有图像的结果保存为 npz。

        npz 内部结构:
            image_names: np.ndarray[str]
            masks: np.ndarray (N, H, W) uint8
            confidence_maps: np.ndarray (N, H, W) float32  (无 conf 时为空数组)
            metadata: bytes (pickle 序列化的 list[dict])
            model_names: np.ndarray[str]
        """
        masks = []
        confs = []
        metas = []
        model_names = []
        for pred in seg_outputs:
            masks.append(pred.mask if pred.mask is not None else np.zeros((1, 1), dtype=np.uint8))
            confs.append(
                pred.confidence_map
                if pred.confidence_map is not None
                else np.zeros((1, 1), dtype=np.float32)
            )
            metas.append(pred.metadata or {})
            model_names.append(pred.model_name)

        # 统一 shape（可能不同图像尺寸不同，用 object 数组）
        masks_arr = np.empty(len(masks), dtype=object)
        confs_arr = np.empty(len(confs), dtype=object)
        for i in range(len(masks)):
            masks_arr[i] = masks[i]
            confs_arr[i] = confs[i]

        np.savez_compressed(
            str(path),
            image_names=np.array(image_names),
            masks=masks_arr,
            confidence_maps=confs_arr,
            metadata=np.array(pickle.dumps(metas)),
            model_names=np.array(model_names),
        )

    @staticmethod
    def _load_seg_npz(path: Path) -> list[dict[str, Any]]:
        """加载分割 npz，返回每张图的 SegModelOutput dict。

        Returns:
            list[dict], 每个 dict 有 keys: model_name, mask, confidence_map, metadata
        """
        from segmentation.base_model import SegModelOutput

        data = np.load(str(path), allow_pickle=True)
        image_names = data["image_names"]
        masks = data["masks"]
        confs = data["confidence_maps"]
        metas = pickle.loads(data["metadata"].item())
        model_names = data["model_names"]

        results = []
        for i in range(len(image_names)):
            mask = masks[i]
            conf = confs[i]
            # 恢复为 SegModelOutput 对象
            has_conf = conf.shape != (1, 1)
            results.append(SegModelOutput(
                model_name=str(model_names[i]),
                mask=mask.astype(np.uint8),
                confidence_map=conf.astype(np.float32) if has_conf else None,
                metadata=metas[i],
            ))
        return results

    @staticmethod
    def _save_cls_json(path: Path, image_names: list[str], cls_outputs: list) -> None:
        """将一个分类模型对所有图像的结果保存为 json。"""
        results = {}
        for img_name, pred in zip(image_names, cls_outputs):
            results[img_name] = pred.to_dict()

        with open(path, "w", encoding="utf-8") as f:
            json.dump({"model_name": cls_outputs[0].model_name if cls_outputs else "", "results": results}, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _load_cls_json(path: Path) -> list:
        """加载分类 json，返回 list[ClsModelOutput]。"""
        from classification.base_model import ClsModelOutput

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        results = []
        for img_name, pred_dict in data["results"].items():
            results.append(ClsModelOutput(
                model_name=pred_dict["model_name"],
                predictions=pred_dict["predictions"],
                top_class=pred_dict["top_class"],
                top_confidence=pred_dict["top_confidence"],
                requires_mask=pred_dict["requires_mask"],
                metadata=pred_dict.get("metadata", {}),
            ))
        return results

    @staticmethod
    def _save_selected_masks_npz(
        path: Path,
        image_names: list[str],
        masks: list[np.ndarray],
        seg_decisions_serialized: list[dict],
    ) -> None:
        """保存 Phase 3 选定的 mask + 分割决策摘要。"""
        masks_arr = np.empty(len(masks), dtype=object)
        for i, m in enumerate(masks):
            masks_arr[i] = m

        np.savez_compressed(
            str(path),
            image_names=np.array(image_names),
            selected_masks=masks_arr,
            seg_decisions=np.array(pickle.dumps(seg_decisions_serialized)),
        )

    @staticmethod
    def _load_selected_masks_npz(path: Path) -> tuple[list[str], list[np.ndarray], list[dict]]:
        """加载选定 mask + 分割决策摘要。"""
        data = np.load(str(path), allow_pickle=True)
        image_names = list(data["image_names"])
        masks = list(data["selected_masks"])
        decisions = pickle.loads(data["seg_decisions"].item())
        return image_names, masks, decisions

    @staticmethod
    def _save_results_json(results: list[dict], path: Path) -> None:
        """保存最终结果到 JSON（去除 numpy 类型）。"""
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

    # ===== Phase 辅助方法 =====

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

    def _select_mask_static(
        self, image, seg_predictions, anchor_class,
        gt_mask=None, input_device_info=None, input_data_info=None
    ) -> "SegAgentDecision":
        """静态规则选择最佳分割 mask。"""
        from segmentation.agent import SegAgentDecision

        pred_map = {p.model_name: p for p in seg_predictions}
        names = [p.model_name for p in seg_predictions]
        masks = [p.mask for p in seg_predictions]
        preds_list = list(seg_predictions)

        quality_results = self.seg_agent.quality_evaluator.evaluate_batch(masks, names)
        agreement_dict = (
            quality_results.get("agreement_metrics", {})
            .get("average_agreement", {})
        )

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
                    remaining_names = set(names)

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

            if al_class == majority:
                return ClsAgentDecision(
                    selected_model="autogluon_majority_agree",
                    selected_class=al_class,
                    confidence=float(al_conf),
                    reasoning=f"独立模型多数派={majority}，AutoGluon一致({al_conf:.2f})",
                    all_predictions=[p.to_dict() for p in indie_preds],
                    method="path_b_static_majority",
                )
            if al_conf > 0.8:
                return ClsAgentDecision(
                    selected_model="autogluon_strong_signal",
                    selected_class=al_class,
                    confidence=float(al_conf),
                    reasoning=f"AutoGluon高置信({al_conf:.2f})，信ROI级特征",
                    all_predictions=[p.to_dict() for p in indie_preds],
                    method="path_b_static_autogluon",
                )

        best = max(indie_preds, key=lambda p: p.top_confidence)
        return ClsAgentDecision(
            selected_model="majority_fallback",
            selected_class=majority,
            confidence=float(best.top_confidence),
            reasoning=f"独立模型无共识(多数派={majority})，退回多数派投票",
            all_predictions=[p.to_dict() for p in indie_preds],
            method="path_b_static_fallback",
        )

    # ===== 主入口 =====

    def run_single(
        self,
        image: np.ndarray,
        gt_mask: Optional[np.ndarray] = None,
        input_device_info: Optional[list[str]] = None,
        input_data_info: Optional[dict] = None,
    ) -> dict[str, Any]:
        """单图推理（需预加载模型，仅用于调试）。"""
        cls_cfg = self.config.get("classification", {}).get("agent", {})
        seg_cfg = self.config.get("segmentation", {}).get("agent", {})
        enable_seg_agent = seg_cfg.get("enable_agent", True)
        enable_cls_agent = cls_cfg.get("enable_agent", True)
        consensus_threshold = cls_cfg.get("consensus_min_confidence", 0.6)

        indie_preds = self._get_independent_classification_predictions(image)
        consensus, anchor_class = self._check_classification_consensus(
            indie_preds, min_confidence=consensus_threshold
        )

        seg_predictions = self.seg_registry.predict_all(image)
        if not seg_predictions:
            raise RuntimeError("分割模型全部失败，无法继续")

        if enable_seg_agent:
            seg_decision: SegAgentDecision = self.seg_agent.select_best_mask(
                image, seg_predictions,
                classification_anchor=anchor_class,
                gt_mask=gt_mask,
                input_device_info=input_device_info,
                input_data_info=input_data_info,
            )
        else:
            seg_decision = self._select_mask_static(
                image, seg_predictions, anchor_class,
                gt_mask=gt_mask,
                input_device_info=input_device_info,
                input_data_info=input_data_info,
            )

        selected_mask = seg_decision.selected_mask

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
            "selected_mask": selected_mask,
            "selected_mask_shape": selected_mask.shape,
            "selected_mask_area": int(np.sum(selected_mask)),
            "cls_decision": cls_decision.to_dict(),
            "final_label": cls_decision.selected_class,
            "final_confidence": cls_decision.confidence,
        }

    def _get_independent_classification_predictions(self, image):
        """单图模式：跑独立分类模型（需 cls_registry 已加载）。"""
        preds = []
        for name, model in self.cls_registry.get_independent_models():
            try:
                preds.append(model.predict(image, mask=None))
            except Exception as e:
                print(f"  ✗ 独立分类模型 {name} 失败: {e}")
        return preds

    def _run_autogluon_classification(self, image, mask):
        """单图模式：跑 AutoGluon（需 cls_registry 已加载）。"""
        for name, model in self.cls_registry.get_mask_dependent_models():
            try:
                return model.predict(image, mask)
            except Exception as e:
                print(f"  ✗ AutoGluon 分类失败 ({name}): {e}")
        return None

    # ===== 批量推理（5 阶段按需加载）=====

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
        """批量级联推理（按需加载/卸载模型，中间结果落盘）。

        5 个 Phase:
          Phase 1: 依次加载分割模型 → 推理全部图像 → 保存 npz → 卸载
          Phase 2: 依次加载独立分类模型 → 推理全部图像 → 保存 json → 卸载
          Phase 3: 从缓存加载 → 分割 Agent 选择 → 保存 selected_masks.npz
          Phase 4: AutoGluon 加载 → 推理无共识图像 → 保存 json → 卸载
          Phase 5: 分类裁决 + 保存 results.json

        每个 Phase 检查缓存文件是否已存在，存在则跳过（支持断点续跑）。
        """
        from segmentation.model_factory import build_seg_model
        from classification.model_factory import build_cls_model

        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        inter_dir = out_path / "intermediate"
        seg_cache_dir = inter_dir / "seg"
        cls_cache_dir = inter_dir / "cls"
        seg_cache_dir.mkdir(parents=True, exist_ok=True)
        cls_cache_dir.mkdir(parents=True, exist_ok=True)

        # 加载标签
        labels: dict[str, Any] = {}
        if label_file:
            with open(label_file, "r", encoding="utf-8") as f:
                labels = json.load(f)

        # 收集图像
        img_dir = Path(image_dir)
        exts = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
        image_paths = sorted(
            [f for f in img_dir.iterdir() if f.suffix.lower() in exts],
            key=lambda x: x.name,
        )
        if start_index > 0:
            image_paths = image_paths[start_index:]
        if max_images is not None:
            image_paths = image_paths[:max_images]

        img_names = [p.name for p in image_paths]
        print(f"级联推理: {len(img_names)} 张图像 (start={start_index})")

        # 获取配置
        seg_cfg_full = self.config.get("segmentation", {})
        cls_cfg_full = self.config.get("classification", {})
        seg_model_configs = seg_cfg_full.get("models", [])
        cls_model_configs = cls_cfg_full.get("models", [])
        seg_agent_cfg = seg_cfg_full.get("agent", {})
        cls_agent_cfg = cls_cfg_full.get("agent", {})
        enable_seg_agent = seg_agent_cfg.get("enable_agent", True)
        enable_cls_agent = cls_agent_cfg.get("enable_agent", True)
        consensus_threshold = cls_agent_cfg.get("consensus_min_confidence", 0.6)

        # ===== Phase 1: 分割模型（逐个加载 → 推理全部图像 → 保存 npz → 卸载）=====
        print(f"\n{'='*60}")
        print("Phase 1: 依次加载分割模型并推理全部图像")
        print(f"{'='*60}")

        for i, model_cfg in enumerate(seg_model_configs):
            model_cfg = dict(model_cfg)
            model_name = model_cfg.get("name", f"seg_{i}")
            model_cfg["device"] = self.device
            cache_path = seg_cache_dir / f"{model_name}.npz"

            if cache_path.exists():
                print(f"  [{i+1}/{len(seg_model_configs)}] ⏭ {model_name} 已有缓存，跳过")
                continue

            model = build_seg_model(model_cfg)
            model.load_model()

            seg_outputs = []
            for img_path in image_paths:
                try:
                    image = self.image_io.load_image(img_path)
                    pred = model.predict(image)
                    seg_outputs.append(pred)
                except Exception as e:
                    print(f"  ✗ {model.model_name} 推理 {img_path.name} 失败: {e}")
                    from segmentation.base_model import SegModelOutput
                    seg_outputs.append(SegModelOutput(
                        model_name=model.model_name,
                        mask=np.zeros((image.shape[0], image.shape[1]), dtype=np.uint8),
                        confidence_map=None,
                        metadata={"error": str(e)},
                    ))

            model.unload_model()
            self._save_seg_npz(cache_path, img_names, seg_outputs)
            print(f"  [{i+1}/{len(seg_model_configs)}] ✓ {model.model_name} 推理完成，已保存 {cache_path.name}，已卸载")

        # ===== Phase 2: 独立分类模型（逐个加载 → 推理全部图像 → 保存 json → 卸载）=====
        print(f"\n{'='*60}")
        print("Phase 2: 依次加载独立分类模型并推理全部图像")
        print(f"{'='*60}")

        mask_dep_cfgs = []

        for i, model_cfg in enumerate(cls_model_configs):
            model_cfg = dict(model_cfg)
            model_name = model_cfg.get("name", f"cls_{i}")
            model_cfg["device"] = "cpu" if model_cfg.get("type") == "autogluon_radiomics" else self.device
            cache_path = cls_cache_dir / f"{model_name}.json"

            # 先构建模型判断 requires_mask
            model = build_cls_model(model_cfg)

            if model.requires_mask:
                mask_dep_cfgs.append(model_cfg)
                print(f"  [{i+1}/{len(cls_model_configs)}] ⏭ {model_name} 需 mask，延迟到 Phase 4")
                continue

            if cache_path.exists():
                print(f"  [{i+1}/{len(cls_model_configs)}] ⏭ {model_name} 已有缓存，跳过")
                continue

            model.load_model()

            cls_outputs = []
            for img_path in image_paths:
                try:
                    image = self.image_io.load_image(img_path)
                    pred = model.predict(image, mask=None)
                    cls_outputs.append(pred)
                except Exception as e:
                    print(f"  ✗ {model.model_name} 推理 {img_path.name} 失败: {e}")
                    from classification.base_model import ClsModelOutput
                    cls_outputs.append(ClsModelOutput(
                        model_name=model.model_name,
                        predictions={},
                        top_class="unknown",
                        top_confidence=0.0,
                        requires_mask=False,
                        metadata={"error": str(e)},
                    ))

            model.unload_model()
            self._save_cls_json(cache_path, img_names, cls_outputs)
            print(f"  [{i+1}/{len(cls_model_configs)}] ✓ {model.model_name} 推理完成，已保存 {cache_path.name}，已卸载")

        # ===== Phase 3: 分类共识 + 分割 Agent（从缓存加载，CPU 运行）=====
        print(f"\n{'='*60}")
        print("Phase 3: 分类共识判断 + 分割 Agent 选择")
        print(f"{'='*60}")

        selected_masks_path = inter_dir / "selected_masks.npz"

        if selected_masks_path.exists():
            print("  ⏭ selected_masks.npz 已存在，跳过 Phase 3")
            sel_img_names, sel_masks, seg_decisions_serialized = \
                self._load_selected_masks_npz(selected_masks_path)
        else:
            import gc

            # 逐图像：从缓存按需加载 → Agent 决策 → 释放 → 增量保存
            sel_img_names = []
            sel_masks = []
            seg_decisions_serialized = []

            for idx, img_name in enumerate(img_names):
                img_path = image_paths[idx]
                image = self.image_io.load_image(img_path)

                gt_mask = None
                if gt_mask_dir:
                    gt_path = Path(gt_mask_dir) / img_name
                    if gt_path.exists():
                        gt_mask = self.image_io.binarize_mask(self.image_io.load_mask(gt_path))

                # 按需加载该图像的分割结果（从 npz 缓存）
                seg_preds = []
                for model_cfg in seg_model_configs:
                    model_name = model_cfg.get("name", "")
                    cache_path = seg_cache_dir / f"{model_name}.npz"
                    if cache_path.exists():
                        all_outputs = self._load_seg_npz(cache_path)
                        if idx < len(all_outputs):
                            seg_preds.append(all_outputs[idx])
                        del all_outputs

                # 按需加载该图像的分类结果（从 json 缓存）
                indie_preds = []
                for model_cfg in cls_model_configs:
                    model_name = model_cfg.get("name", "")
                    cache_path = cls_cache_dir / f"{model_name}.json"
                    if cache_path.exists():
                        all_outputs = self._load_cls_json(cache_path)
                        if idx < len(all_outputs):
                            indie_preds.append(all_outputs[idx])
                        del all_outputs

                # 分类共识
                consensus, anchor_class = self._check_classification_consensus(
                    indie_preds, min_confidence=consensus_threshold
                )

                # 分割 Agent
                if not seg_preds:
                    print(f"  ✗ {img_name} 无分割结果，跳过")
                    continue

                if enable_seg_agent:
                    seg_decision = self.seg_agent.select_best_mask(
                        image, seg_preds,
                        classification_anchor=anchor_class,
                        gt_mask=gt_mask,
                        input_device_info=input_device_info,
                        input_data_info=input_data_info,
                    )
                else:
                    seg_decision = self._select_mask_static(
                        image, seg_preds, anchor_class,
                        gt_mask=gt_mask,
                        input_device_info=input_device_info,
                        input_data_info=input_data_info,
                    )

                sel_img_names.append(img_name)
                sel_masks.append(seg_decision.selected_mask)
                seg_decisions_serialized.append({
                    "img_name": img_name,
                    "consensus": consensus,
                    "anchor_class": anchor_class,
                    "selected_model": seg_decision.selected_model,
                    "confidence": seg_decision.confidence,
                    "reasoning": seg_decision.reasoning,
                    "path": seg_decision.path,
                    "all_predictions": seg_decision.all_predictions,
                })
                print(f"  [{idx+1}/{len(img_names)}] {img_name}: {seg_decision.selected_model} (consensus={consensus})")

                # 释放本图内存
                del image, seg_preds, indie_preds, gt_mask, seg_decision
                gc.collect()

            self._save_selected_masks_npz(
                selected_masks_path, sel_img_names, sel_masks, seg_decisions_serialized
            )
            print(f"  ✓ 已保存 {selected_masks_path.name}")

        # 构建 img_name → (mask, decision, consensus, anchor) 映射
        sel_map: dict[str, dict] = {}
        for i, name in enumerate(sel_img_names):
            d = seg_decisions_serialized[i]
            sel_map[name] = {
                "mask": sel_masks[i],
                "decision": d,
                "consensus": d["consensus"],
                "anchor_class": d["anchor_class"],
            }

        # ===== Phase 4: AutoGluon 分类（仅对无共识的图像）=====
        print(f"\n{'='*60}")
        print("Phase 4: AutoGluon 分类（基于选定 mask）")
        print(f"{'='*60}")

        autogluon_cache_path = inter_dir / "autogluon.json"

        # 确定哪些图像需要 AutoGluon
        needs_autogluon_names = [
            name for name in img_names
            if name in sel_map and not sel_map[name]["consensus"]
        ]

        if not needs_autogluon_names:
            print("  所有图像均有分类共识，无需 AutoGluon")
            autogluon_results: dict[str, Any] = {}
        elif not mask_dep_cfgs:
            print("  ⚠️ 需 AutoGluon 但未配置 mask 依赖模型")
            autogluon_results = {}
        elif autogluon_cache_path.exists():
            print(f"  ⏭ {autogluon_cache_path.name} 已存在，跳过")
            with open(autogluon_cache_path, "r", encoding="utf-8") as f:
                autogluon_results = json.load(f)
        else:
            # 加载 AutoGluon
            model_cfg = dict(mask_dep_cfgs[0])
            model_cfg["device"] = "cpu"
            model = build_cls_model(model_cfg)
            model.load_model()

            autogluon_results = {}
            for idx, img_name in enumerate(needs_autogluon_names):
                img_path = image_paths[img_names.index(img_name)]
                image = self.image_io.load_image(img_path)
                mask = sel_map[img_name]["mask"]

                try:
                    pred = model.predict(image, mask=mask)
                    autogluon_results[img_name] = pred.to_dict()
                except Exception as e:
                    print(f"  ✗ {model.model_name} 推理 {img_name} 失败: {e}")
                    autogluon_results[img_name] = {
                        "model_name": model.model_name,
                        "predictions": {},
                        "top_class": "unknown",
                        "top_confidence": 0.0,
                        "requires_mask": True,
                        "metadata": {"error": str(e)},
                    }

            model.unload_model()
            print(f"  ✓ {model.model_name} 推理完成，已卸载")

            with open(autogluon_cache_path, "w", encoding="utf-8") as f:
                json.dump(autogluon_results, f, ensure_ascii=False, indent=2)

        # ===== Phase 5: 分类裁决 + 保存最终结果 =====
        print(f"\n{'='*60}")
        print("Phase 5: 分类裁决 + 保存最终结果")
        print(f"{'='*60}")

        # 从缓存加载独立分类结果（用于裁决）
        all_indie_cls: dict[str, list] = {name: [] for name in img_names}
        for model_cfg in cls_model_configs:
            model_name = model_cfg.get("name", "")
            cache_path = cls_cache_dir / f"{model_name}.json"
            if cache_path.exists():
                cls_outputs = self._load_cls_json(cache_path)
                for j, img_name in enumerate(img_names):
                    if j < len(cls_outputs):
                        all_indie_cls[img_name].append(cls_outputs[j])

        results: list[dict[str, Any]] = []

        for idx, img_name in enumerate(img_names):
            if img_name not in sel_map:
                results.append({"image_name": img_name, "error": "无分割结果"})
                continue

            sel_info = sel_map[img_name]
            consensus = sel_info["consensus"]
            anchor_class = sel_info["anchor_class"]
            seg_decision_dict = sel_info["decision"]
            selected_mask = sel_info["mask"]
            indie_preds = all_indie_cls[img_name]

            # 分类裁决
            if consensus:
                cls_decision = self._make_anchor_classification_decision(anchor_class, indie_preds)
            else:
                # 构造 AutoGluon ClsModelOutput
                from classification.base_model import ClsModelOutput
                ag_dict = autogluon_results.get(img_name)
                autogluon_pred = None
                if ag_dict:
                    autogluon_pred = ClsModelOutput(
                        model_name=ag_dict["model_name"],
                        predictions=ag_dict["predictions"],
                        top_class=ag_dict["top_class"],
                        top_confidence=ag_dict["top_confidence"],
                        requires_mask=ag_dict["requires_mask"],
                        metadata=ag_dict.get("metadata", {}),
                    )

                # 构造 SegAgentDecision（简化版，仅用于 resolve_path_b）
                from segmentation.agent import SegAgentDecision
                seg_decision = SegAgentDecision(
                    selected_model=seg_decision_dict["selected_model"],
                    selected_mask=selected_mask,
                    confidence=seg_decision_dict["confidence"],
                    reasoning=seg_decision_dict["reasoning"],
                    all_predictions=seg_decision_dict["all_predictions"],
                    classification_anchor=anchor_class,
                    path=seg_decision_dict["path"],
                )

                if enable_cls_agent:
                    cls_decision = self.cls_agent.resolve_path_b(
                        indie_preds, autogluon_pred, seg_decision
                    )
                else:
                    cls_decision = self._resolve_classification_path_b_static(
                        indie_preds, autogluon_pred
                    )

            result = {
                "path": "A" if consensus else "B",
                "classification_consensus": consensus,
                "seg_decision": seg_decision_dict,
                "selected_mask_shape": list(selected_mask.shape),
                "selected_mask_area": int(np.sum(selected_mask)),
                "cls_decision": cls_decision.to_dict(),
                "final_label": cls_decision.selected_class,
                "final_confidence": cls_decision.confidence,
                "image_name": img_name,
            }

            if img_name in labels:
                result["true_label"] = labels[img_name]

            results.append(result)
            print(f"  [{idx+1}/{len(img_names)}] {img_name}: {result['final_label']} (conf={result['final_confidence']:.3f})")

            # 增量保存
            if (idx + 1) % 10 == 0 or idx == len(img_names) - 1:
                self._save_results_json(results, out_path / "results.json")

        self._save_results_json(results, out_path / "results.json")
        print(f"\n级联推理完成: {len(results)} 张图像")
        return results
