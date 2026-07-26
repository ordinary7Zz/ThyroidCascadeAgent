"""
LLM 驱动的分类 Agent：从多个模型预测中选择最佳结果。

重写自 Classification_Agent/agent/classification_agent.py。
关键改动：
  - 用 shared/llm_client.LLMClient 代替内联 OpenAI 调用
  - 增加 mask_source 参数（pipeline 串联时标注 mask 来源）
  - ClsAgentDecision 增加 mask_source 字段
  - 修复 __init__ 导出（原代码导出废弃的 GeminiAgent）
  - 保留 unanimous check / top_k soft voting / fallback 逻辑
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from shared.base_datasets_info import BASE_DATASETS_INFO, infer_device_match
from shared.llm_client import LLMClient

from .base_model import ClsModelOutput
from .soft_voting import (
    average_class_probabilities,
    winning_class_from_avg_probs,
    resolve_topk_model_outputs,
)


@dataclass
class ClsAgentDecision:
    """Agent 对最佳分类的选择结果。"""

    selected_model: str
    selected_class: str
    confidence: float
    reasoning: str
    all_predictions: list[dict[str, Any]]
    mask_source: str = "external"  # "segmentation_agent_filtered" | "external"
    selected_models: Optional[list[str]] = None  # top_k soft voting 时
    method: str = "single"  # "single" | "soft_voting" | "unanimous" | "fallback"

    def to_dict(self) -> dict[str, Any]:
        result = {
            "selected_model": self.selected_model,
            "selected_class": self.selected_class,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "all_predictions": self.all_predictions,
            "mask_source": self.mask_source,
            "method": self.method,
        }
        if self.selected_models:
            result["selected_models"] = self.selected_models
        return result


class LLMClassificationAgent:
    """LLM 驱动的分类选择 Agent。"""

    def __init__(
        self,
        llm_client: LLMClient,
        config: Optional[dict] = None,
    ):
        self.llm_client = llm_client
        self.base_datasets_info = BASE_DATASETS_INFO

        cfg = config or {}
        self.top_k = max(1, int(cfg.get("top_k", 1)))
        self.enable_agent = cfg.get("enable_agent", True)

        self.system_prompt_single = self._build_system_prompt_single()
        self.system_prompt_multi = self._build_system_prompt_multi()

    def _build_system_prompt_single(self) -> str:
        return """你是甲状腺超声多模型预测整合专家，从若干模型输出中选最可信的一项。

【设备】设备决定成像风格；训练数据覆盖输入同款/同品牌者更可信。GE(Logiq E9/S7)与 Hitachi(ARIETTA 等)各系内部风格近；其余品牌有差异。Heterogeneous=多设备混合。输入设备未知则忽略。

【字段】主置信度优先 metadata.classification_uncertainty.top_confidence_calibrated，否则 top_confidence。entropy(越大越不确定)、margin_top2(越大越稳)。consistency_metrics: num_models_same_class、total_models、vote_entropy。

【决策序】1)主置信度 2)已知输入设备则设备匹配 3)主置信度差<0.05 比验证集 acc/AUC/F1 4)entropy↓ margin↑ 5)能推断数据集则看 base_dataset_performance，否则 dataset_size 大优先 6)差<0.05 结合投票 7)差<0.02 考虑模型差异。

【mask来源】若 mask_source="segmentation_agent_filtered"，说明 mask 已经过分割 Agent + radiomics 裁判验证，可信度较高；若="external"，mask 未经验证。

【输出】只输出纯JSON（无Markdown/思考/代码块），首尾为{}。字段：selected_model, selected_class, confidence, reasoning。"""

    def _build_system_prompt_multi(self) -> str:
        tk = self.top_k
        return f"""你是甲状腺超声多模型预测整合专家，选出最值得信任的 {tk} 个模型（按信任度从高到低），用于对各类别概率取平均融合。

【设备】设备决定成像风格；训练数据覆盖输入同款/同品牌者更可信。

【字段】主置信度优先 top_confidence_calibrated，否则 top_confidence。entropy、margin_top2、consistency_metrics。

【决策序】综合判断哪 {tk} 个模型组合最可信，优先级与单选类似，需考虑组合互补性。

【输出】只输出纯JSON（无Markdown/思考），首尾为{{}}。字段：selected_models(长度恰好{tk}的字符串数组), reasoning。不要输出 selected_class 或 confidence。"""

    # ========== 一致性检查 ==========

    @staticmethod
    def _predictions_top_class_unanimous(predictions: list[ClsModelOutput]) -> bool:
        if not predictions:
            return False
        first = predictions[0].top_class
        return all(p.top_class == first for p in predictions)

    def _decision_unanimous(self, predictions: list[ClsModelOutput]) -> ClsAgentDecision:
        """各模型类别一致：不调 LLM，取 top_confidence 最高者。"""
        best = max(predictions, key=lambda p: p.top_confidence)
        reasoning = (
            f"所有模型均预测为「{best.top_class}」，决策一致，未调用大模型；"
            f"选取 top_confidence 最高的模型 {best.model_name}（{best.top_confidence:.4f}）。"
        )
        return ClsAgentDecision(
            selected_model=best.model_name,
            selected_class=best.top_class,
            confidence=float(best.top_confidence),
            reasoning=reasoning,
            all_predictions=[p.to_dict() for p in predictions],
            method="unanimous",
        )

    # ========== Prompt 构造 ==========

    def _build_compact_prediction_dicts(self, predictions: list[ClsModelOutput]) -> list[dict[str, Any]]:
        """构建 LLM 输入的紧凑预测 JSON。"""
        votes_per_class: dict[str, int] = {}
        for pred in predictions:
            votes_per_class[pred.top_class] = votes_per_class.get(pred.top_class, 0) + 1

        total_models = len(predictions)
        vote_entropy = 0.0
        if total_models > 0:
            probs = [c / total_models for c in votes_per_class.values()]
            vote_entropy = -sum(p * math.log(p + 1e-12, 2) for p in probs if p > 0)

        compact: list[dict[str, Any]] = []
        for pred in predictions:
            pd = pred.to_dict()
            meta = pd.get("metadata") or {}
            full_probs = pd.get("predictions", {}) or {}

            class_probs = list(full_probs.values())
            entropy = None
            margin_top2 = None
            if class_probs:
                total_p = sum(class_probs)
                if total_p > 0:
                    norm = [p / total_p for p in class_probs]
                    entropy = -sum(p * math.log(p + 1e-12, 2) for p in norm if p > 0)
                sorted_p = sorted(class_probs, reverse=True)
                margin_top2 = (sorted_p[0] - sorted_p[1]) if len(sorted_p) >= 2 else sorted_p[0]

            sorted_items = sorted(full_probs.items(), key=lambda x: x[1], reverse=True)
            top2 = [{k: float(v)} for k, v in sorted_items[:2]]

            cu = meta.get("classification_uncertainty", {}) or {}
            top_conf_cal = cu.get("top_confidence_calibrated")

            on_train = (meta.get("validation_metrics", {}) or {}).get("on_training_dataset", {}) or {}
            ds_info = meta.get("dataset_info", {}) or {}
            base_perf = meta.get("base_dataset_performance", {}) or {}
            train_devices = meta.get("training_data_devices") or []

            compact.append({
                "model_name": pd.get("model_name"),
                "top_class": pd.get("top_class"),
                "top_confidence": pd.get("top_confidence"),
                "top2_predictions": top2,
                "metadata": {
                    "classification_uncertainty": {
                        **({"top_confidence_calibrated": top_conf_cal} if top_conf_cal is not None else {}),
                        "top_confidence_raw": pd.get("top_confidence"),
                        "entropy": entropy,
                        "margin_top2": margin_top2,
                    },
                    "consistency_metrics": {
                        "num_models_same_class": votes_per_class.get(pd.get("top_class"), 0),
                        "total_models": total_models,
                        "vote_entropy": vote_entropy,
                    },
                    "training_data_devices": train_devices,
                    "dataset_info": {
                        "training_dataset": ds_info.get("training_dataset"),
                        "base_datasets": ds_info.get("base_datasets", []),
                        "dataset_size": ds_info.get("dataset_size"),
                    },
                    "validation_metrics": {
                        "on_training_dataset": {
                            "accuracy": on_train.get("accuracy"),
                            "auc": on_train.get("auc"),
                            "f1_score": on_train.get("f1_score"),
                        }
                    },
                    "base_dataset_performance": base_perf,
                    "requires_mask": pd.get("requires_mask", False),
                },
            })
        return compact

    def format_predictions_json(
        self,
        predictions: list[ClsModelOutput],
        mask_source: str = "external",
    ) -> str:
        """构造 LLM 输入 JSON。"""
        data = {
            "num_models": len(predictions),
            "mask_source": mask_source,
            "mask_validation": (
                "此 mask 已经过分割 Agent 的 radiomics 裁判验证，可信度较高"
                if mask_source == "segmentation_agent_filtered"
                else "mask 来自外部，未经验证"
            ),
            "predictions": self._build_compact_prediction_dicts(predictions),
        }
        return json.dumps(data, ensure_ascii=False)

    # ========== JSON 解析 ==========

    @staticmethod
    def _extract_json_from_text(text: str) -> str:
        """从 LLM 响应文本提取 JSON 对象。"""
        if text.startswith("*Thinking"):
            parts = text.split("\n\n")
            for i, part in enumerate(parts):
                if "{" in part:
                    text = "\n\n".join(parts[i:])
                    break

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            for part in text.split("```"):
                if "{" in part and "}" in part:
                    text = part.strip()
                    break

        start = text.find("{")
        if start == -1:
            return text

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
                        return s

        s = text[start:]
        return re.sub(r"[\x00-\x1f\x7f-\x9f]", "", s)

    # ========== 核心选择方法 ==========

    def select_best_model(
        self,
        predictions: list[ClsModelOutput],
        mask_source: str = "external",
        input_device_info: Optional[list[str]] = None,
        input_data_info: Optional[dict] = None,
    ) -> ClsAgentDecision:
        """
        选择最佳分类结果。

        Args:
            predictions: 多个模型的预测结果。
            mask_source: mask 来源标注（"segmentation_agent_filtered" | "external"）。
            input_device_info: 输入设备信息。
            input_data_info: 输入数据元信息。
        """
        if not predictions:
            raise ValueError("没有预测结果")

        # 一致时不调 LLM
        if self._predictions_top_class_unanimous(predictions):
            decision = self._decision_unanimous(predictions)
            decision.mask_source = mask_source
            return decision

        # 不启用 agent 时直接 soft voting
        if not self.enable_agent:
            return self._soft_voting_decision(predictions, mask_source)

        # 构造 prompt
        formatted = self.format_predictions_json(predictions, mask_source)
        device_text = f"输入设备: {', '.join(input_device_info)}" if input_device_info else "输入设备: 未知"

        if self.top_k > 1:
            sys_prompt = self.system_prompt_multi
            question = f"选出最值得信任的 {self.top_k} 个模型，严格只回复 JSON。"
        else:
            sys_prompt = self.system_prompt_single
            question = "选出最佳结果，严格只回复 JSON。"

        user_prompt = f"""{sys_prompt}

{device_text}
以下为 {len(predictions)} 个模型的预测(JSON)：

{formatted}

{question}"""

        # 调用 LLM
        try:
            response_text = self.llm_client.chat(sys_prompt, user_prompt)
            json_text = self._extract_json_from_text(response_text)
            decision_data = json.loads(json_text)
        except Exception as e:
            print(f"  ✗ LLM 调用或解析失败: {e}，使用降级选择")
            return self._fallback_selection(predictions, mask_source)

        # 解析决策
        try:
            if self.top_k > 1:
                return self._decision_from_llm_topk(predictions, decision_data, mask_source)
            else:
                return self._decision_from_llm_single(predictions, decision_data, mask_source)
        except (KeyError, ValueError) as e:
            print(f"  ✗ 决策解析失败: {e}，使用降级选择")
            return self._fallback_selection(predictions, mask_source)

    def _decision_from_llm_single(
        self, predictions, decision_data, mask_source
    ) -> ClsAgentDecision:
        """LLM 单选模式。"""
        for field in ["selected_model", "selected_class", "confidence", "reasoning"]:
            if field not in decision_data:
                raise ValueError(f"响应缺少 '{field}'")

        # 修正 confidence 为实际模型置信度
        conf_map = {p.model_name: p.top_confidence for p in predictions}
        selected = decision_data["selected_model"]
        if selected in conf_map:
            confidence = float(conf_map[selected])
        else:
            confidence = max(0.0, min(1.0, float(decision_data["confidence"])))

        return ClsAgentDecision(
            selected_model=selected,
            selected_class=decision_data["selected_class"],
            confidence=confidence,
            reasoning=decision_data["reasoning"],
            all_predictions=[p.to_dict() for p in predictions],
            mask_source=mask_source,
            method="single",
        )

    def _decision_from_llm_topk(
        self, predictions, decision_data, mask_source
    ) -> ClsAgentDecision:
        """LLM top_k 模式：soft voting。"""
        raw_names = decision_data.get("selected_models")
        if not isinstance(raw_names, list):
            raise ValueError("响应缺少有效的 'selected_models'")

        names = [str(x) for x in raw_names]
        subset = resolve_topk_model_outputs(predictions, names, self.top_k)
        avg_probs = average_class_probabilities(subset)
        cls, conf = winning_class_from_avg_probs(avg_probs)

        return ClsAgentDecision(
            selected_model="agent_topk_soft_voting",
            selected_class=cls,
            confidence=float(conf),
            reasoning=str(decision_data.get("reasoning", "")),
            all_predictions=[p.to_dict() for p in predictions],
            mask_source=mask_source,
            selected_models=[p.model_name for p in subset],
            method="soft_voting",
        )

    def _soft_voting_decision(
        self, predictions: list[ClsModelOutput], mask_source: str
    ) -> ClsAgentDecision:
        """不启用 agent 时的 soft voting。"""
        sorted_preds = sorted(predictions, key=lambda p: p.top_confidence, reverse=True)
        k = min(self.top_k, len(sorted_preds))
        subset = sorted_preds[:k]
        avg_probs = average_class_probabilities(subset)
        cls, conf = winning_class_from_avg_probs(avg_probs)

        return ClsAgentDecision(
            selected_model="soft_voting",
            selected_class=cls,
            confidence=float(conf),
            reasoning=f"未启用 agent，按 top_confidence 取前 {k} 个模型 soft voting",
            all_predictions=[p.to_dict() for p in predictions],
            mask_source=mask_source,
            selected_models=[p.model_name for p in subset],
            method="soft_voting",
        )

    def _fallback_selection(
        self, predictions: list[ClsModelOutput], mask_source: str = "external"
    ) -> ClsAgentDecision:
        """降级选择：top_k=1 选最高置信度；top_k>1 soft voting。"""
        if self.top_k <= 1:
            best = max(predictions, key=lambda p: p.top_confidence)
            agree = sum(1 for p in predictions if p.top_class == best.top_class and p.top_confidence > 0.7)
            reasoning = f"降级选择：最高置信度模型（{best.top_confidence:.2%}）"
            if agree >= 3:
                reasoning += f"，{agree} 个模型一致预测为 {best.top_class}"
            return ClsAgentDecision(
                selected_model=best.model_name,
                selected_class=best.top_class,
                confidence=best.top_confidence,
                reasoning=reasoning,
                all_predictions=[p.to_dict() for p in predictions],
                mask_source=mask_source,
                method="fallback",
            )

        sorted_preds = sorted(predictions, key=lambda p: p.top_confidence, reverse=True)
        k = min(self.top_k, len(sorted_preds))
        subset = sorted_preds[:k]
        avg_probs = average_class_probabilities(subset)
        cls, conf = winning_class_from_avg_probs(avg_probs)
        return ClsAgentDecision(
            selected_model="agent_topk_soft_voting",
            selected_class=cls,
            confidence=float(conf),
            reasoning=f"降级选择：前 {k} 个模型 soft voting",
            all_predictions=[p.to_dict() for p in predictions],
            mask_source=mask_source,
            selected_models=[p.model_name for p in subset],
            method="fallback",
        )

    def batch_select(
        self,
        batch_predictions: list[list[ClsModelOutput]],
        mask_source: str = "external",
        input_device_info: Optional[list[str]] = None,
        input_data_info: Optional[dict] = None,
    ) -> list[ClsAgentDecision]:
        """批处理：逐图调用 select_best_model。"""
        decisions = []
        for preds in batch_predictions:
            decisions.append(
                self.select_best_model(preds, mask_source, input_device_info, input_data_info)
            )
        return decisions
