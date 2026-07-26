"""
LLM 驱动的分割 Agent：从多个模型输出中选择最佳 mask。

重写自 Segmentation_Agent/agent/segmentation_agent.py。
关键改动：
  - 用 shared/llm_client.LLMClient 代替内联 OpenAI 调用
  - 预留 radiomics_judge 接口（Phase 7 注入），select_best_mask 增加 image 参数
  - AgentDecision 增加 judge_scores 字段
  - 用 shared/base_datasets_info.BASE_DATASETS_INFO 作为单一来源
  - 保留全部分歧度量、ensemble、降级选择、JSON 解析逻辑
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional

import cv2
import numpy as np

from shared.base_datasets_info import BASE_DATASETS_INFO, infer_device_match
from shared.llm_client import LLMClient

from .base_model import SegModelOutput
from .quality_evaluator import SegmentationQualityEvaluator
from .metrics import compute_dice, compute_hd95, compute_ece


@dataclass
class SegAgentDecision:
    """Agent 对最佳分割的选择结果。"""

    selected_model: str
    selected_mask: np.ndarray
    confidence: float
    reasoning: str
    all_predictions: list[dict[str, Any]]
    quality_metrics: Optional[dict[str, Any]] = None
    agreement_score: Optional[float] = None
    dice_score: Optional[float] = None
    hd95_score: Optional[float] = None
    ece_metrics: Optional[dict[str, float]] = None
    selected_models: Optional[list[str]] = None
    model_weights: Optional[list[float]] = None
    is_ensemble: bool = False
    judge_scores: Optional[dict[str, Any]] = None  # radiomics 裁判结果

    def to_dict(self, include_mask: bool = False) -> dict:
        result = {
            "selected_model": self.selected_model,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "all_predictions": self.all_predictions,
            "quality_metrics": self.quality_metrics,
            "agreement_score": self.agreement_score,
            "is_ensemble": self.is_ensemble,
        }
        if self.is_ensemble and self.selected_models:
            result["selected_models"] = self.selected_models
            if self.model_weights:
                result["model_weights"] = self.model_weights
        if include_mask:
            result["selected_mask"] = self.selected_mask.tolist()
        else:
            result["mask_shape"] = self.selected_mask.shape
            result["mask_area"] = int(np.sum(self.selected_mask))
        if self.dice_score is not None:
            result["dice_score"] = self.dice_score
        if self.hd95_score is not None:
            result["hd95_score"] = self.hd95_score
        if self.ece_metrics:
            result["ece_metrics"] = self.ece_metrics
            result["ece_mean"] = float(np.mean(list(self.ece_metrics.values())))
        if self.judge_scores:
            result["judge_scores"] = self.judge_scores
        return result

    def to_simplified_dict(self) -> dict:
        simplified_preds = []
        for pred in self.all_predictions:
            p = {"model_name": pred["model_name"], "mask_area": pred.get("mask_area", 0)}
            if pred.get("has_confidence_map"):
                p["mean_confidence"] = pred.get("mean_confidence", 0.0)
            simplified_preds.append(p)
        result = {
            "selected_model": self.selected_model,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "all_predictions": simplified_preds,
            "is_ensemble": self.is_ensemble,
        }
        if self.is_ensemble and self.selected_models:
            result["selected_models"] = self.selected_models
            if self.model_weights:
                result["model_weights"] = [float(w) for w in self.model_weights]
        if self.ece_metrics:
            result["ece_metrics"] = self.ece_metrics
            result["ece_mean"] = float(np.mean(list(self.ece_metrics.values())))
        return result


class SegmentationAgent:
    """LLM 驱动的分割选择 Agent。"""

    def __init__(
        self,
        llm_client: LLMClient,
        quality_evaluator: Optional[SegmentationQualityEvaluator] = None,
        radiomics_judge=None,
        config: Optional[dict] = None,
    ):
        """
        Args:
            llm_client: 共享的 LLM 客户端。
            quality_evaluator: 质量评估器（None 时内部创建）。
            radiomics_judge: GT-trained radiomics 裁判（None 时不启用，Phase 7 注入）。
            config: agent 配置（ensemble, disagreement 等）。
        """
        self.llm_client = llm_client
        self.quality_evaluator = quality_evaluator or SegmentationQualityEvaluator()
        self.radiomics_judge = radiomics_judge
        self.base_datasets_info = BASE_DATASETS_INFO

        cfg = config or {}
        self.ensemble_enabled = cfg.get("ensemble", {}).get("enabled", True)
        self.ensemble_top_k = cfg.get("ensemble", {}).get("top_k", 1)
        self.ensemble_method = cfg.get("ensemble", {}).get("method", "weighted_average")
        self.ensemble_threshold = cfg.get("ensemble", {}).get("threshold", 0.5)
        self.include_disagreement = cfg.get("include_disagreement_metrics_in_prompt", True)

        self.system_prompt = self._generate_system_prompt()

    def _generate_system_prompt(self) -> str:
        if self.ensemble_enabled and self.ensemble_top_k > 1:
            m3 = ', "模型3名称"' if self.ensemble_top_k >= 3 else ''
            w3 = ', 0.0' if self.ensemble_top_k >= 3 else ''
            fmt = f'{{"selected_models": ["模型1", "模型2"{m3}], "weights": [0.6, 0.4{w3}], "confidence": 0.95, "reasoning": "选择理由"}}'
            desc = (
                f'返回JSON: "selected_models"(长度{self.ensemble_top_k}数组), '
                f'"weights"(和为1.0), "confidence"(0-1), '
                f'"reasoning"(3-4句中文含数值, 约120-180字)。'
            )
        else:
            fmt = '{"selected_model": "模型名称", "confidence": 0.95, "reasoning": "选择理由"}'
            desc = (
                '返回JSON: "selected_model", "confidence"(0-1), '
                '"reasoning"(3-4句中文含数值, 约120-180字)。'
            )

        disagreement_block = ""
        if self.include_disagreement:
            disagreement_block = """
当输入含 group_uncertainty 与 disagreement 时：
- group_uncertainty.area_cv：面积离散度，越大共识越差；
- pairwise_hd95_mean/std：边界差异整体水平与波动；
- disagreement.mean_hd95_to_others：该模型与其余模型边界平均 HD95；
- disagreement.area_rel_to_group：面积相对群体均值的偏差。
分歧大时优先选 agreement 高且 mean_hd95_to_others 低的模型。"""

        judge_block = ""
        if self.radiomics_judge is not None:
            judge_block = """
你还将看到每个分割结果经 GT-trained radiomics 模型的分类判断（radiomics_judge 字段）。
该裁判用金标准 mask 训练，分类置信度可作为分割质量的间接信号：
分割越准确，radiomics 特征越接近训练分布，分类置信度越合理。
若多个模型的 radiomics_judge 分类结果分歧大，说明分割质量差异大，需重点分析。
mahalanobis_distance 过大（>3）的 mask 可能分割异常。"""

        return f"""你是一个分割模型选择代理，根据多个模型的掩码质量指标选择最佳结果。
只输出一个JSON对象，首字符{{末字符}}，无前缀后缀或Markdown。

输出格式：{desc}
示例：{fmt}
{disagreement_block}
{judge_block}
决策优先级（从高到低）：
1) 模型间一致性：agreement_with_others 高更可靠；分歧大时倚重 agreement 高且 mean_hd95_to_others 低的候选；
2) radiomics 裁判（如有）：分类置信度合理、mahalanobis_distance 不过大的 mask 更可信；
3) 设备匹配：训练设备与输入设备越接近越好；
4) 形态学：单连通、边界平滑、circularity 0.6-0.9、面积与长宽比合理；
5) 数据集性能：dice 高、hd95 低、dataset_size 大的模型更优；
6) 置信度：mean_confidence 较高为次要加分项。

reasoning 须引用关键数值（agreement、dice、hd95、area_cv、pairwise_hd95_mean、radiomics_judge 等）。"""

    # ========== 分歧度量 ==========

    @staticmethod
    def _compact_disagreement_fields(
        agreement_metrics: dict, n_models: int
    ) -> tuple[Optional[dict], Optional[list[dict]]]:
        if n_models < 2:
            return None, None
        vols = np.asarray(agreement_metrics.get("volumes") or [], dtype=np.float64)
        hdm = np.asarray(agreement_metrics.get("pairwise_hd95_matrix") or [], dtype=np.float64)
        if vols.size != n_models or hdm.shape != (n_models, n_models):
            return None, None
        vmean = float(vols.mean())
        per_model = []
        for i in range(n_models):
            others = hdm[i, [j for j in range(n_models) if j != i]]
            mhd = float(np.mean(others)) if others.size else 0.0
            area_rel = float((vols[i] - vmean) / vmean) if vmean > 1e-6 else 0.0
            per_model.append({"mean_hd95_to_others": round(mhd, 2), "area_rel_to_group": round(area_rel, 4)})
        group = {
            "area_cv": round(float(agreement_metrics.get("volume_cv", 0.0)), 4),
            "pairwise_hd95_mean": round(float(agreement_metrics.get("pairwise_hd95_mean", 0.0)), 2),
            "pairwise_hd95_std": round(float(agreement_metrics.get("pairwise_hd95_std", 0.0)), 2),
        }
        return group, per_model

    @staticmethod
    def _build_disagreement_prefix(g_val: dict, per_val, predictions, max_models=8) -> str:
        lines = [
            f"【分歧摘要】area_cv={g_val['area_cv']}, "
            f"pairwise_hd95_mean={g_val['pairwise_hd95_mean']}, "
            f"pairwise_hd95_std={g_val['pairwise_hd95_std']}。"
        ]
        if per_val is not None and len(per_val) == len(predictions) and len(predictions) <= max_models:
            segs = [
                f"{p.model_name}:{dc['mean_hd95_to_others']:.2f},{dc['area_rel_to_group']:.4f}"
                for p, dc in zip(predictions, per_val)
            ]
            lines.append("【各模型】mhd95,area_rel丨" + "丨".join(segs) + "。")
        return "\n".join(lines) + "\n\n"

    # ========== Radiomics 裁判 ==========

    def _run_judge(self, image: np.ndarray, predictions: list[SegModelOutput]) -> Optional[list[dict]]:
        """对每个 pred mask 跑 radiomics 裁判。Phase 7 注入 judge 后生效。"""
        if self.radiomics_judge is None:
            return None
        masks = [p.mask for p in predictions]
        try:
            return self.radiomics_judge.judge_batch(image, masks)
        except Exception as e:
            print(f"  ⚠️ radiomics 裁判失败: {e}")
            return None

    # ========== Prompt 构造 ==========

    def format_predictions_for_agent(
        self,
        predictions: list[SegModelOutput],
        quality_results: dict,
        judge_results: Optional[list[dict]] = None,
        input_device_info: Optional[list[str]] = None,
        input_data_info: Optional[dict] = None,
    ) -> str:
        data: dict[str, Any] = {
            "num_models": len(predictions),
            "input_device_info": input_device_info if input_device_info else "未知 (null)",
            "input_data_info": self._normalize_unknown(input_data_info or {}),
            "base_datasets_info": self.base_datasets_info,
            "models": [],
        }

        am = quality_results.get("agreement_metrics") or {}
        n = len(predictions)
        group_unc, per_disagree = None, None
        if self.include_disagreement:
            group_unc, per_disagree = self._compact_disagreement_fields(am, n)
            if group_unc:
                data["group_uncertainty"] = group_unc

        for idx, pred in enumerate(predictions):
            q = quality_results["individual_quality"][idx]
            meta = pred.metadata or {}

            model_info: dict[str, Any] = {
                "model_name": pred.model_name,
                "training_devices": meta.get("training_data_devices", []),
                "mask_statistics": {
                    "area": q["area"],
                    "is_single_component": q["is_single_component"],
                    "num_components": q["num_components"],
                    "circularity": round(q["circularity"], 2),
                    "smoothness": round(q["smoothness"], 2),
                    "compactness": round(q["compactness"], 2),
                    "solidity": round(q["solidity"], 2),
                    "aspect_ratio": round(q["aspect_ratio"], 2),
                },
                "agreement_with_others": round(am.get("average_agreement", [0])[idx], 2) if am.get("average_agreement") else 0.0,
            }
            if per_disagree and idx < len(per_disagree):
                model_info["disagreement"] = per_disagree[idx]

            # 设备匹配
            base_datasets = meta.get("dataset_info", {}).get("base_datasets", [])
            if base_datasets and input_device_info:
                dm = infer_device_match(input_device_info, base_datasets)
                model_info["device_match"] = dm

            # 性能
            bdp = meta.get("base_dataset_performance", {})
            if bdp:
                model_info["base_dataset_performance"] = {
                    ds: {"dice": round(v.get("dice", 0), 2), "hd95": round(v.get("hd95", 999), 2)}
                    for ds, v in bdp.items()
                }

            # 数据集信息
            di = meta.get("dataset_info", {})
            if di:
                model_info["dataset_info"] = {
                    "base_datasets": di.get("base_datasets", []),
                    "dataset_size": di.get("dataset_size", 0),
                }

            # 置信度
            if pred.confidence_map is not None and np.sum(pred.mask) > 0:
                model_info["mean_confidence"] = round(float(np.mean(pred.confidence_map[pred.mask > 0])), 2)

            # radiomics 裁判（新增）
            if judge_results and idx < len(judge_results) and judge_results[idx].get("valid", False):
                jr = judge_results[idx]
                model_info["radiomics_judge"] = {
                    "malignant_prob": round(jr["malignant_prob"], 3),
                    "confidence": round(jr["confidence"], 3),
                    "top_features": jr.get("top_features", [])[:5],
                    "mahalanobis_distance": round(jr.get("mahalanobis_distance", 0), 2),
                }

            data["models"].append(model_info)

        data["overall_agreement"] = round(am.get("overall_agreement", 0), 2)

        req: dict[str, Any] = {}
        if group_unc:
            req["follow_prefix"] = "reasoning 须含 area_cv、pairwise_hd95_mean/std 及所选模型 disagreement 两项。"
        if self.radiomics_judge is not None and judge_results:
            req["mention_judge"] = "reasoning 须提及 radiomics_judge 的分类置信度或特征差异。"
        if req:
            data["reasoning_requirements"] = req

        return json.dumps(data, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _normalize_unknown(value: Any) -> Any:
        if value is None:
            return "未知 (null)"
        if isinstance(value, dict):
            return {k: SegmentationAgent._normalize_unknown(v) for k, v in value.items()}
        if isinstance(value, list):
            return ["未知 (空列表)"] if not value else [SegmentationAgent._normalize_unknown(v) for v in value]
        if isinstance(value, str) and not value.strip():
            return "未知 (空字符串)"
        return value

    # ========== JSON 解析 ==========

    @staticmethod
    def _extract_json_from_text(text: str) -> str:
        # markdown code block
        if "```json" in text:
            extracted = text.split("```json")[1].split("```")[0].strip()
            if extracted.startswith("{") and ("selected_model" in extracted or "selected_models" in extracted):
                return extracted
        elif "```" in text:
            for part in text.split("```"):
                p = part.strip()
                if p.startswith("{") and ("selected_model" in p or "selected_models" in p):
                    complete = SegmentationAgent._extract_complete_json(p)
                    if complete:
                        return complete

        text = re.sub(r"\*Thinking[^*]*\*", "", text, flags=re.DOTALL)
        text = re.sub(r"^#+\s+.*$", "", text, flags=re.MULTILINE)

        start = text.find("{")
        if start != -1:
            complete = SegmentationAgent._extract_complete_json_from_position(text, start)
            if complete and ("selected_model" in complete or "selected_models" in complete):
                return complete

        raise ValueError(f"无法提取 JSON。响应前500字: {text[:500]}")

    @staticmethod
    def _extract_complete_json(text: str) -> Optional[str]:
        start = text.find("{")
        return SegmentationAgent._extract_complete_json_from_position(text, start) if start != -1 else None

    @staticmethod
    def _extract_complete_json_from_position(text: str, start: int) -> Optional[str]:
        brace = 0
        in_str = False
        escape = False
        for i in range(start, len(text)):
            c = text[i]
            if escape:
                escape = False
                continue
            if c == "\\":
                escape = True
                continue
            if c == '"' and not escape:
                in_str = not in_str
                continue
            if not in_str:
                if c == "{":
                    brace += 1
                elif c == "}":
                    brace -= 1
                    if brace == 0:
                        s = text[start : i + 1]
                        s = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", s)
                        if "selected_model" in s or "selected_models" in s:
                            return s.strip()
                        return None
        return None

    # ========== Ensemble ==========

    @staticmethod
    def _ensemble_probability_maps(
        prob_maps: list[np.ndarray], weights: list[float], method: str = "weighted_average"
    ) -> np.ndarray:
        total = sum(weights)
        weights = [w / total for w in weights] if total > 0 else [1.0 / len(weights)] * len(weights)

        target = prob_maps[0].shape
        normalized = [
            cv2.resize(pm.astype(np.float32), (target[1], target[0]), interpolation=cv2.INTER_LINEAR)
            if pm.shape != target
            else pm.astype(np.float32)
            for pm in prob_maps
        ]

        if method in ("weighted_average", "equal_weight"):
            result = np.zeros_like(normalized[0])
            for pm, w in zip(normalized, weights):
                result += pm * w
        elif method == "geometric_mean":
            result = np.ones_like(normalized[0])
            for pm, w in zip(normalized, weights):
                result *= np.power(np.clip(pm, 1e-6, 1.0), w)
        else:
            raise ValueError(f"未知 ensemble 方法: {method}")

        return np.clip(result, 0.0, 1.0)

    @staticmethod
    def _generate_mask_from_probability(prob_map: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        mask = (prob_map > threshold).astype(np.uint8)
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        if num_labels > 1:
            largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
            mask = (labels == largest).astype(np.uint8)
        return mask

    # ========== 核心选择方法 ==========

    def select_best_mask(
        self,
        image: np.ndarray,
        predictions: list[SegModelOutput],
        gt_mask: Optional[np.ndarray] = None,
        input_device_info: Optional[list[str]] = None,
        input_data_info: Optional[dict] = None,
    ) -> SegAgentDecision:
        """
        选择最佳分割 mask。

        Args:
            image: (H, W, 3) RGB uint8 [0,255]。radiomics_judge 需要。
            predictions: 多个模型的预测结果。
            gt_mask: 可选 GT mask（仅用于评估，不影响选择）。
            input_device_info: 输入设备信息。
            input_data_info: 输入数据元信息。
        """
        if not predictions:
            raise ValueError("没有预测结果")

        masks = [p.mask for p in predictions]
        model_names = [p.model_name for p in predictions]

        # 统一 mask 尺寸
        shapes = {m.shape[:2] for m in masks}
        if len(shapes) > 1:
            target = masks[0].shape[:2]
            masks = [
                cv2.resize(m.astype(np.uint8), (target[1], target[0]), interpolation=cv2.INTER_NEAREST)
                if m.shape[:2] != target
                else m
                for m in masks
            ]

        quality_results = self.quality_evaluator.evaluate_batch(masks, model_names)

        # 分歧度量
        g_val, per_val = None, None
        if self.include_disagreement:
            g_val, per_val = self._compact_disagreement_fields(
                quality_results.get("agreement_metrics") or {}, len(predictions)
            )
        prefix = ""
        if g_val:
            prefix = self._build_disagreement_prefix(g_val, per_val, predictions)

        # radiomics 裁判（新增）
        judge_results = self._run_judge(image, predictions)

        # 构造 prompt
        formatted = self.format_predictions_for_agent(
            predictions, quality_results, judge_results, input_device_info, input_data_info
        )

        device_text = f"\n**输入设备**: {', '.join(input_device_info)}\n" if input_device_info else "\n**输入设备**: 未知\n"
        data_text = f"\n**输入数据**: {json.dumps(self._normalize_unknown(input_data_info or {}), ensure_ascii=False)}\n"

        if self.ensemble_enabled and self.ensemble_top_k > 1:
            question = f"请选择 Top {self.ensemble_top_k} 个最佳模型用于 ensemble。"
            fmt = '{"selected_models": ["模型1", "模型2"], "weights": [0.6, 0.4], "confidence": 0.95, "reasoning": "..."}'
        else:
            question = "哪个模型提供了最佳分割结果？"
            fmt = '{"selected_model": "模型名称", "confidence": 0.95, "reasoning": "..."}'

        user_prompt = f"""{prefix}{device_text}{data_text}
以下是 {len(predictions)} 个分割模型的输出及质量评估：

{formatted}

{question}
只输出纯JSON。格式：{fmt}"""

        # 调用 LLM
        try:
            response_text = self.llm_client.chat(self.system_prompt, user_prompt)
            json_text = self._extract_json_from_text(response_text)
            decision_data = json.loads(json_text)
        except Exception as e:
            print(f"  ✗ LLM 调用或解析失败: {e}，使用降级选择")
            return self._fallback_selection(predictions, gt_mask, quality_results, judge_results)

        # 解析决策
        try:
            confidence = max(0.0, min(1.0, float(decision_data["confidence"])))
            reasoning = str(decision_data["reasoning"]).strip()
            if not reasoning:
                raise ValueError("reasoning 为空")

            is_ensemble = "selected_models" in decision_data and self.ensemble_enabled

            if is_ensemble:
                return self._handle_ensemble(
                    decision_data, predictions, quality_results, gt_mask, judge_results, confidence, reasoning
                )
            else:
                return self._handle_single(
                    decision_data, predictions, quality_results, gt_mask, judge_results, confidence, reasoning
                )
        except (KeyError, ValueError) as e:
            print(f"  ✗ 决策解析失败: {e}，使用降级选择")
            return self._fallback_selection(predictions, gt_mask, quality_results, judge_results)

    def _handle_single(
        self, decision_data, predictions, quality_results, gt_mask, judge_results, confidence, reasoning
    ) -> SegAgentDecision:
        name = str(decision_data.get("selected_model", "")).strip()
        idx = self._find_pred_index(predictions, name)
        if idx is None:
            raise ValueError(f"模型 '{name}' 不在预测列表中")

        pred = predictions[idx]
        selected_q = quality_results["individual_quality"][idx]
        agreement = quality_results["agreement_metrics"].get("average_agreement", [None])[idx]

        dice, hd95 = self._compute_metrics(pred.mask, gt_mask) if gt_mask is not None else (None, None)
        ece = self._compute_ece(pred, gt_mask) if gt_mask is not None else None

        jr = {predictions[i].model_name: judge_results[i] for i in range(len(predictions))} if judge_results else None

        return SegAgentDecision(
            selected_model=pred.model_name,
            selected_mask=pred.mask,
            confidence=confidence,
            reasoning=reasoning,
            all_predictions=[p.to_dict() for p in predictions],
            quality_metrics=selected_q,
            agreement_score=agreement,
            dice_score=dice,
            hd95_score=hd95,
            ece_metrics=ece,
            is_ensemble=False,
            judge_scores=jr,
        )

    def _handle_ensemble(
        self, decision_data, predictions, quality_results, gt_mask, judge_results, confidence, reasoning
    ) -> SegAgentDecision:
        names = decision_data["selected_models"][: self.ensemble_top_k]
        weights = [float(w) for w in decision_data.get("weights", [])[: len(names)]]
        if not weights:
            weights = [1.0 / len(names)] * len(names)
        total = sum(weights)
        weights = [w / total for w in weights] if total > 0 else [1.0 / len(names)] * len(names)

        selected_preds, indices = [], []
        for name in names:
            idx = self._find_pred_index(predictions, name)
            if idx is None:
                raise ValueError(f"模型 '{name}' 不在预测列表中")
            selected_preds.append(predictions[idx])
            indices.append(idx)

        prob_maps = [
            p.confidence_map if p.confidence_map is not None else p.mask.astype(np.float32)
            for p in selected_preds
        ]
        ensemble_map = self._ensemble_probability_maps(prob_maps, weights, self.ensemble_method)
        final_mask = self._generate_mask_from_probability(ensemble_map, self.ensemble_threshold)

        selected_q = quality_results["individual_quality"][indices[0]]
        agreement = quality_results["agreement_metrics"].get("average_agreement", [None])[indices[0]]
        dice, hd95 = self._compute_metrics(final_mask, gt_mask) if gt_mask is not None else (None, None)
        ece = None
        if gt_mask is not None:
            gt_r = self._resize_gt(gt_mask, final_mask.shape)
            ece = {"ece": compute_ece(ensemble_map, gt_r)} if gt_r is not None else None

        jr = {predictions[i].model_name: judge_results[i] for i in range(len(predictions))} if judge_results else None

        return SegAgentDecision(
            selected_model=names[0],
            selected_mask=final_mask,
            confidence=confidence,
            reasoning=reasoning,
            all_predictions=[p.to_dict() for p in predictions],
            quality_metrics=selected_q,
            agreement_score=agreement,
            dice_score=dice,
            hd95_score=hd95,
            ece_metrics=ece,
            selected_models=names,
            model_weights=weights,
            is_ensemble=True,
            judge_scores=jr,
        )

    def _fallback_selection(
        self, predictions, gt_mask, quality_results, judge_results=None
    ) -> SegAgentDecision:
        """降级选择：选一致性最高的模型。"""
        agreement = quality_results["agreement_metrics"].get("average_agreement")
        if agreement and len(agreement) > 0:
            if self.ensemble_enabled and self.ensemble_top_k > 1:
                top_k = min(self.ensemble_top_k, len(predictions))
                indices = np.argsort(agreement)[-top_k:][::-1].tolist()
            else:
                indices = [int(np.argmax(agreement))]
        else:
            indices = list(range(min(self.ensemble_top_k if self.ensemble_enabled else 1, len(predictions))))

        best_idx = indices[0]
        best_pred = predictions[best_idx]
        selected_q = quality_results["individual_quality"][best_idx]
        agree = agreement[best_idx] if agreement else None

        dice, hd95 = self._compute_metrics(best_pred.mask, gt_mask) if gt_mask is not None else (None, None)
        ece = self._compute_ece(best_pred, gt_mask) if gt_mask is not None else None

        jr = {predictions[i].model_name: judge_results[i] for i in range(len(predictions))} if judge_results else None

        reasoning = f"降级选择：一致性最高（IoU={agree:.2f}）" if agree else "降级选择：第一个模型"

        if self.ensemble_enabled and self.ensemble_top_k > 1 and len(indices) > 1:
            selected_preds = [predictions[i] for i in indices]
            names = [p.model_name for p in selected_preds]
            weights = [1.0 / len(names)] * len(names)
            prob_maps = [
                p.confidence_map if p.confidence_map is not None else p.mask.astype(np.float32)
                for p in selected_preds
            ]
            ensemble_map = self._ensemble_probability_maps(prob_maps, weights, self.ensemble_method)
            final_mask = self._generate_mask_from_probability(ensemble_map, self.ensemble_threshold)
            return SegAgentDecision(
                selected_model=names[0],
                selected_mask=final_mask,
                confidence=agree or 0.5,
                reasoning=f"降级选择：ensemble {len(names)} 个模型（平均IoU={agree:.2f}）" if agree else "降级选择",
                all_predictions=[p.to_dict() for p in predictions],
                quality_metrics=selected_q,
                agreement_score=agree,
                dice_score=dice,
                hd95_score=hd95,
                ece_metrics=ece,
                selected_models=names,
                model_weights=weights,
                is_ensemble=True,
                judge_scores=jr,
            )

        return SegAgentDecision(
            selected_model=best_pred.model_name,
            selected_mask=best_pred.mask,
            confidence=agree or 0.5,
            reasoning=reasoning,
            all_predictions=[p.to_dict() for p in predictions],
            quality_metrics=selected_q,
            agreement_score=agree,
            dice_score=dice,
            hd95_score=hd95,
            ece_metrics=ece,
            is_ensemble=False,
            judge_scores=jr,
        )

    # ========== 辅助方法 ==========

    @staticmethod
    def _find_pred_index(predictions: list[SegModelOutput], name: str) -> Optional[int]:
        if not name:
            return None
        nl = name.strip().lower()
        for i, p in enumerate(predictions):
            if p.model_name == name or p.model_name.strip().lower() == nl:
                return i
        return None

    @staticmethod
    def _compute_metrics(pred_mask, gt_mask):
        if pred_mask is None or gt_mask is None:
            return None, None
        try:
            gt_r = SegmentationAgent._resize_gt(gt_mask, pred_mask.shape)
            if gt_r is None:
                return None, None
            return compute_dice(pred_mask, gt_r), compute_hd95(pred_mask, gt_r)
        except Exception:
            return None, None

    @staticmethod
    def _resize_gt(gt_mask, target_shape):
        if gt_mask.shape == target_shape:
            return gt_mask
        try:
            return cv2.resize(
                gt_mask.astype(np.uint8),
                (target_shape[1], target_shape[0]),
                interpolation=cv2.INTER_NEAREST,
            )
        except Exception:
            return None

    @staticmethod
    def _compute_ece(pred: SegModelOutput, gt_mask):
        if pred is None or gt_mask is None or pred.confidence_map is None:
            return None
        try:
            gt_r = SegmentationAgent._resize_gt(gt_mask, pred.confidence_map.shape)
            if gt_r is None:
                return None
            return {"ece": compute_ece(pred.confidence_map, gt_r)}
        except Exception:
            return None
