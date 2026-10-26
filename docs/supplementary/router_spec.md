# ThyroidCascadeAgent — LLM router specification (B6)

_Generated from config: `config/revision/b6/tn3k.yaml`_

## Shared decoding (`shared.agent_llm`)

| Field | Value |
|-------|-------|
| API key | environment variable `DASHSCOPE_API_KEY` |
| base_url | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| model_name | `qwen3.8-27b` |
| temperature | `0.3` |
| max_tokens | `768` |

Full config excerpt:

```json
{
  "api_key_env": "DASHSCOPE_API_KEY",
  "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "model_name": "qwen3.8-27b",
  "temperature": 0.3,
  "max_tokens": 768,
  "enable_thinking": false
}
```

---

## 1. Segmentation router (`SegmentationAgent`, Phase 3)

- `enable_agent`: `True`
- `include_disagreement_metrics_in_prompt`: `True`
- `metadata_mode`: `full`
- `ensemble`: `{'enabled': True, 'top_k': 1, 'method': 'weighted_average', 'threshold': 0.5}`
- `radiomics_judge.enabled` (config): `True`

### 1.1 System prompt — base

Used when `radiomics_judge` is injected in pipeline (judge block included below).
If judge is disabled at runtime, omit the radiomics paragraph in the actual call.

```
你是分割模型选择代理。根据 user 中 JSON 指标选最佳 mask。
禁止输出思考过程、Markdown 或任何 JSON 外的文字。第一个字符必须是 {，最后一个必须是 }。
只输出一行 JSON："selected_model", "confidence"(0-1), "reasoning"(固定为"-")。示例：{"selected_model":"模型名", "confidence":0.9, "reasoning":"-"}
优先级：agreement_with_others↑；分歧大时 mean_hd95_to_others↓；radiomics_judge 与 classification_anchor 一致者优先；形态学与设备匹配次之。
```

### 1.1b System prompt — base without radiomics judge block

_Only if `radiomics_judge` is not loaded:_

```
你是分割模型选择代理。根据 user 中 JSON 指标选最佳 mask。
禁止输出思考过程、Markdown 或任何 JSON 外的文字。第一个字符必须是 {，最后一个必须是 }。
只输出一行 JSON："selected_model", "confidence"(0-1), "reasoning"(固定为"-")。示例：{"selected_model":"模型名", "confidence":0.9, "reasoning":"-"}
优先级：agreement_with_others↑；分歧大时 mean_hd95_to_others↓；radiomics_judge 与 classification_anchor 一致者优先；形态学与设备匹配次之。
```

### 1.2 System prompt — append Path A (classification consensus)

Appended when independent classifiers agree (`classification_anchor` set).
Example anchor shown as `恶性`:

```

【分类锚点（关键信号）】
独立分类模型（3个，无需mask）一致判断该图像为「恶性」。
此锚点用于评估各分割结果的合理性：
- 与锚点矛盾的Radiomics裁判分类 → 该mask可能覆盖了错误的ROI → 可信度显著降低。
- 与锚点吻合的mask → 额外加分。
- 若所有mask的Radiomics分类都与锚点矛盾 → 选confidence最高的mask并解释原因。
```

### 1.3 System prompt — append Path B (no classification consensus)

```

【无分类锚点】
独立分类模型对该图像的判断不一致，未能形成共识。
整图级别特征模糊，分割评估应以以下为主要依据：
1. Radiomics裁判的内部一致性（不同的分割得到相似的分类方向→更可信）
2. 形态学合理性（circularity 0.6-0.9、单连通）
3. 设备匹配与历史性能
```

### 1.4 User message template

（运行时拼接，非独立文件）

可选前缀：分歧度量摘要（当 `include_disagreement_metrics_in_prompt: true` 时由代码生成）。

**输入设备** / **输入数据** 行（来自 `pipeline.data.device_info` 与可选 `input_data_info`）。

正文：
```
以下是 {N} 个分割模型的输出及质量评估：

{formatted_predictions_json}

哪个模型提供了最佳分割结果？
只输出纯JSON。格式：{"selected_model": "模型名称", "confidence": 0.95, "reasoning": "..."}
```

`formatted_predictions_json` 由 `SegmentationAgent.format_predictions_for_agent()` 生成，
含各模型质量指标、可选 `radiomics_judge`、`group_uncertainty` / `disagreement` 等字段。

### 1.5 LLM output JSON schema

- Single mask: `{"selected_model": "<name>", "confidence": 0.0-1.0, "reasoning": "..."}`

### 1.6 Non-LLM fallbacks

- `enable_agent: false` → `method: static_fallback` / `cascade_static_mask` (rule-based).
- LLM parse/API failure → `method: llm_fallback` (same static selector).

---

## 2. Classification — standalone (`run_cls.py` / unanimous bypass)

- `enable_agent`: `True`
- `top_k`: `5`
- Unanimous top class across models → **no LLM** (`method: unanimous`).

### 2.1 System prompt — single selection (`top_k == 1`)

```
从 user JSON  predictions 中选最可信模型。
禁止思考/Markdown。只输出一行 JSON：selected_model, selected_class, confidence(0-1), reasoning 固定为 "-"。
```

### 2.2 System prompt — top-k fusion (`top_k > 1`)

```
你是甲状腺超声多模型预测整合专家，选出最值得信任的 5 个模型（按信任度从高到低），用于对各类别概率取平均融合。

【字段】top_confidence（或 top_confidence_calibrated）为主置信度。entropy、margin_top2、num_models_same_class。

【决策序】综合判断哪 5 个模型组合最可信，优先级与单选类似，需考虑组合互补性。

【输出】只输出纯JSON（无Markdown/思考），首尾为{}。字段：selected_models(长度恰好5的字符串数组), reasoning。不要输出 selected_class 或 confidence。
```

### 2.3 User message template

```
{system_prompt}

输入设备: {device_info}
以下为 {N} 个模型的预测(JSON)：

{formatted_predictions_json}

{question}
```

### 2.4 LLM output JSON schema

- Single: `{"selected_model": "...", "selected_class": "良性|恶性", "confidence": 0.0-1.0, "reasoning": "..."}`
- Top-k: `{"selected_models": ["...", ...], "reasoning": "..."}` (no `selected_class` / `confidence` in multi mode).

---

## 3. Classification — Path B (`resolve_path_b`, Phase 5, no consensus)

- Invoked when `classification_consensus == false` and `enable_agent: true`.
- Current config `enable_agent`: `True`

### 3.1 System prompt

```
你是甲状腺超声诊断专家。独立分类模型对该图像判断不一致，你需要综合所有信号，自己做出最终的良恶性判断。

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
reasoning 须引用具体置信度数值。
```

### 3.2 User message

Single JSON string (`ensure_ascii=False`), structure:

```json
{
  "scenario": "独立分类模型无共识，需综合裁决",
  "independent_models": [
    {
      "model_name": "<name>",
      "top_class": "良性|恶性",
      "top_confidence": 0.0
    }
  ],
  "autogluon_based_on_selected_mask": {
    "top_class": "良性|恶性",
    "top_confidence": 0.0
  },
  "segmentation_decision": {
    "selected_mask_from": "<seg_model_name>",
    "reasoning": "<segmentation agent reasoning>"
  },
  "question": "请综合以上信息，给出最终良恶性判断和置信度(0-1)。"
}
```

`autogluon_based_on_selected_mask` may be `null` if AutoGluon unavailable.

### 3.3 LLM output JSON schema

`{"selected_class": "良性|恶性", "confidence": 0.0-1.0, "reasoning": "..."}`

(No `selected_model`; stored decision uses `selected_model: agent_path_b_llm`.)

### 3.4 Path B without LLM

- `enable_agent: false` → weighted soft vote (`method: path_b_static_softvote`).

---

## 4. Path A classification (no LLM)

- `task: cls_path_a`, `method: classification_consensus` — logged in `routing_log.jsonl` only.

---

## 5. Full prompt examples for Supplementary

Set `pipeline.routing_log_include_prompts: true`, run pipeline on anonymized cases, and copy `prompts` from `routing_log.jsonl` (fields `system` / `user`).
