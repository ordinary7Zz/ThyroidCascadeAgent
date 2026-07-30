"""
LLM 驱动的分类 Agent：从多个模型预测中选择最佳结果。

重写自 Classification_Agent/agent/classification_agent.py。
关键改动：
  - 用 shared/llm_client.LLMClient 代替内联 OpenAI 调用
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
    selected_models: Optional[list[str]] = None  # top_k soft voting 时
    method: str = "single"  # "single" | "soft_voting" | "unanimous" | "fallback"

    def to_dict(self) -> dict[str, Any]:
        result = {
            "selected_model": self.selected_model,
            "selected_class": self.selected_class,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "all_predictions": self.all_predictions,
            "method": self.method,
        }
        if self.selected_models:
            result["selected_models"] = self.selected_models
        return result


class LLMClassificationAgent:
    """LLM 驱动的分类选择 Agent。"""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
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

【字段】top_confidence（或 top_confidence_calibrated）为主置信度。entropy 越大越不确定，margin_top2 越大越稳。num_models_same_class 为投票一致性。

【决策序】1) 主置信度高 2) training_devices 与输入设备匹配 3) entropy↓ margin↑ 4) dataset_size 大优先 5) 投票一致性高。

【输出】只输出纯JSON（无Markdown/思考/代码块），首尾为{}。字段：selected_model, selected_class, confidence, reasoning。"""

    def _build_system_prompt_multi(self) -> str:
        tk = self.top_k
        return f"""你是甲状腺超声多模型预测整合专家，选出最值得信任的 {tk} 个模型（按信任度从高到低），用于对各类别概率取平均融合。

【字段】top_confidence（或 top_confidence_calibrated）为主置信度。entropy、margin_top2、num_models_same_class。

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

            ds_info = meta.get("dataset_info", {}) or {}
            train_devices = meta.get("training_data_devices") or []

            compact.append({
                "model_name": pd.get("model_name"),
                "top_class": pd.get("top_class"),
                "top_confidence": pd.get("top_confidence"),
                "class_probabilities": top2,
                "metadata": {
                    **({"top_confidence_calibrated": top_conf_cal} if top_conf_cal is not None else {}),
                    "entropy": entropy,
                    "margin_top2": margin_top2,
                    "num_models_same_class": votes_per_class.get(pd.get("top_class"), 0),
                    "training_devices": train_devices,
                    "dataset_size": ds_info.get("dataset_size"),
                },
            })
        return compact

    def format_predictions_json(
        self,
        predictions: list[ClsModelOutput],
    ) -> str:
        """构造 LLM 输入 JSON。"""
        # 计算 vote_entropy（顶层，避免每个模型重复）
        votes_per_class: dict[str, int] = {}
        for pred in predictions:
            votes_per_class[pred.top_class] = votes_per_class.get(pred.top_class, 0) + 1
        total_models = len(predictions)
        vote_entropy = 0.0
        if total_models > 0:
            probs = [c / total_models for c in votes_per_class.values()]
            vote_entropy = -sum(p * math.log(p + 1e-12, 2) for p in probs if p > 0)

        data = {
            "num_models": total_models,
            "vote_entropy": round(vote_entropy, 3),
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
        input_device_info: Optional[list[str]] = None,
        input_data_info: Optional[dict] = None,
    ) -> ClsAgentDecision:
        """
        选择最佳分类结果。

        Args:
            predictions: 多个模型的预测结果。
            input_device_info: 输入设备信息。
            input_data_info: 输入数据元信息。
        """
        if not predictions:
            raise ValueError("没有预测结果")

        # 一致时不调 LLM
        if self._predictions_top_class_unanimous(predictions):
            return self._decision_unanimous(predictions)

        # 不启用 agent 时直接 soft voting
        if not self.enable_agent:
            return self._soft_voting_decision(predictions)

        # 构造 prompt
        formatted = self.format_predictions_json(predictions)
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
            return self._fallback_selection(predictions)

        # 解析决策
        try:
            if self.top_k > 1:
                return self._decision_from_llm_topk(predictions, decision_data)
            else:
                return self._decision_from_llm_single(predictions, decision_data)
        except (KeyError, ValueError) as e:
            print(f"  ✗ 决策解析失败: {e}，使用降级选择")
            return self._fallback_selection(predictions)

    def _decision_from_llm_single(
        self, predictions, decision_data
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
            method="single",
        )

    def _decision_from_llm_topk(
        self, predictions, decision_data
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
            selected_models=[p.model_name for p in subset],
            method="soft_voting",
        )

    def _soft_voting_decision(
        self, predictions: list[ClsModelOutput]
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
            selected_models=[p.model_name for p in subset],
            method="soft_voting",
        )

    def _fallback_selection(
        self, predictions: list[ClsModelOutput]
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
            selected_models=[p.model_name for p in subset],
            method="fallback",
        )

    def resolve_path_b(
        self,
        indie_predictions: list["ClsModelOutput"],
        autogluon_pred: Optional["ClsModelOutput"],
        seg_decision: Any,
    ) -> "ClsAgentDecision":
        """
        Path B 分类裁决：独立分类模型无共识时的分类决策。

        规则优先级：
        1. AutoGluon 与独立模型多数派一致 → 直接输出（不调 LLM）
        2. 不一致但 AutoGluon 高置信(≈conf>0.8) → 信 AutoGluon
        3. 都不确定 → 调 LLM 裁决
        4. LLM 失败 → 输出多数派
        """
        from collections import Counter

        if not indie_predictions:
            raise ValueError("没有独立分类模型预测")

        classes = [p.top_class for p in indie_predictions]
        majority = Counter(classes).most_common(1)[0][0]

        if autogluon_pred is not None:
            al_class = autogluon_pred.top_class
            al_conf = autogluon_pred.top_confidence

            # 规则 1: 与多数派一致
            if al_class == majority:
                reasoning = (
                    f"独立模型无共识(多数派={majority})，"
                    f"AutoGluon 基于筛选 mask 也判断为{majority}(conf={al_conf:.2f})，一致，采纳。"
                )
                return ClsAgentDecision(
                    selected_model="autogluon_majority_agree",
                    selected_class=al_class,
                    confidence=float(al_conf),
                    reasoning=reasoning,
                    all_predictions=[p.to_dict() for p in indie_predictions],
                    method="path_b_majority",
                )

            # 规则 2: 不一致但 AutoGluon 高置信
            if al_conf > 0.8:
                reasoning = (
                    f"独立模型无共识，AutoGluon 基于 ROI 特征分类置信度高"
                    f"({al_conf:.2f})。独立模型可能在无 mask 条件下判断不确定。"
                    f"采纳 AutoGluon: {al_class}。"
                )
                return ClsAgentDecision(
                    selected_model="autogluon_strong_signal",
                    selected_class=al_class,
                    confidence=float(al_conf),
                    reasoning=reasoning,
                    all_predictions=[p.to_dict() for p in indie_predictions],
                    method="path_b_autogluon",
                )

        # 规则 3: 调 LLM 裁决
        if self.enable_agent:
            try:
                return self._resolve_path_b_with_llm(
                    indie_predictions, autogluon_pred, seg_decision
                )
            except Exception as e:
                print(f"  ✗ Path B LLM 裁决失败: {e}")

        # 规则 4: 最终降级 → 多数派
        return self._decision_majority(indie_predictions, majority)

    @staticmethod
    def _decision_majority(predictions, majority) -> "ClsAgentDecision":
        """Path B 最终降级：输出多数派。"""
        best = max(predictions, key=lambda p: p.top_confidence)
        return ClsAgentDecision(
            selected_model="majority_fallback",
            selected_class=majority,
            confidence=float(best.top_confidence),
            reasoning=(
                f"独立模型无共识(多数派={majority})，AutoGluon也不确定，"
                f"退回到多数派投票。置信度=low。"
            ),
            all_predictions=[p.to_dict() for p in predictions],
            method="path_b_majority_fallback",
        )

    def _resolve_path_b_with_llm(
        self,
        indie_preds: list["ClsModelOutput"],
        autogluon_pred: Optional["ClsModelOutput"],
        seg_decision: Any,
    ) -> "ClsAgentDecision":
        """Path B 最困难情况：调 LLM 做最终裁决。

        LLM 收到的信号：
        - 3 个独立模型各自的预测和置信度
        - AutoGluon 基于筛选 mask 的分类结果（如有）
        - 分割 Agent 选择该 mask 的理由
        """
        # 独立模型信息
        indie_info = []
        for p in indie_preds:
            pd = p.to_dict()
            indie_info.append({
                "model_name": pd.get("model_name"),
                "top_class": pd.get("top_class"),
                "top_confidence": pd.get("top_confidence"),
            })

        # AutoGluon 信息
        al_info = None
        if autogluon_pred is not None:
            al_info = {
                "top_class": autogluon_pred.top_class,
                "top_confidence": autogluon_pred.top_confidence,
            }

        # 分割 Agent reasoning
        seg_reason = (
            seg_decision.reasoning
            if hasattr(seg_decision, "reasoning")
            else str(seg_decision)
        )
        seg_model = (
            seg_decision.selected_model
            if hasattr(seg_decision, "selected_model")
            else "unknown"
        )

        prompt_data = {
            "scenario": "独立分类模型无共识，需综合裁决",
            "independent_models": indie_info,
            "autogluon_based_on_selected_mask": al_info,
            "segmentation_decision": {
                "selected_mask_from": seg_model,
                "reasoning": seg_reason,
            },
            "question": "请综合以上信息，给出最终良恶性判断和置信度(0-1)。",
        }

        sys_prompt = """你是甲状腺超声诊断专家。独立分类模型对该图像判断不一致，你需要综合所有信号，自己做出最终的良恶性判断。

你将收到：
1. 独立分类模型预测（3个，无需mask，整图判断）
2. AutoGluon 基于分割筛选 mask 的 Radiomics 分类（有 ROI 引导）
3. 分割 Agent 选择该 mask 的推理

Markup:
- 独立模型置信度普遍低(<0.6) → 整图级特征不明显，ROI 级特征更可信
- AutoGluon 分类基于 ROI 特征 → 在 mask 靠谱的前提下更细腻
- 分割 Agent reasoning 解释了为什么选这个 mask

若所有信号都模糊，保守倾向恶性（宁可假阳性不可假阴性），但标注低置信度。

输出纯JSON（无 Markdown/代码块），首尾为{}：
{"selected_class": "恶性", "confidence": 0.75, "reasoning": "..."}
reasoning 须引用具体置信度数值。"""

        user_prompt = json.dumps(prompt_data, ensure_ascii=False)

        response_text = self.llm_client.chat(sys_prompt, user_prompt)
        json_text = self._extract_json_from_text(response_text)
        decision_data = json.loads(json_text)

        return ClsAgentDecision(
            selected_model="agent_path_b_llm",
            selected_class=decision_data["selected_class"],
            confidence=float(decision_data["confidence"]),
            reasoning=decision_data["reasoning"],
            all_predictions=[p.to_dict() for p in indie_preds],
            method="path_b_llm",
        )

    def batch_select(
        self,
        batch_predictions: list[list[ClsModelOutput]],
        input_device_info: Optional[list[str]] = None,
        input_data_info: Optional[dict] = None,
    ) -> list[ClsAgentDecision]:
        """批处理：逐图调用 select_best_model。"""
        decisions = []
        for preds in batch_predictions:
            decisions.append(
                self.select_best_model(preds, input_device_info, input_data_info)
            )
        return decisions
