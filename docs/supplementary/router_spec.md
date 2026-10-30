# ThyroidCascadeAgent — LLM router specification (B6)

_Generated from config: `config/revision/b6/tn3k.yaml`_

## Shared decoding (`shared.agent_llm`)

| Field | Value |
|-------|-------|
| API key | environment variable `DASHSCOPE_API_KEY` |
| base_url | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| model_name | `deepseek-v4-pro-0813` |
| temperature | `0.3` |
| max_tokens | `2048` |

Full config excerpt:

```json
{
  "api_key_env": "DASHSCOPE_API_KEY",
  "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "model_name": "deepseek-v4-pro-0813",
  "temperature": 0.3,
  "max_tokens": 2048,
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
只输出一行 JSON："selected_model", "confidence"(0-1)；勿输出 reasoning 字段。示例：{"selected_model":"模型名", "confidence":0.9}
优先级：agreement_with_others↑；分歧大时 mean_hd95_to_others↓；radiomics_judge 与 classification_anchor 一致者优先；形态学与设备匹配次之。
```

### 1.1b System prompt — base without radiomics judge block

_Only if `radiomics_judge` is not loaded:_

```
你是分割模型选择代理。根据 user 中 JSON 指标选最佳 mask。
禁止输出思考过程、Markdown 或任何 JSON 外的文字。第一个字符必须是 {，最后一个必须是 }。
只输出一行 JSON："selected_model", "confidence"(0-1)；勿输出 reasoning 字段。示例：{"selected_model":"模型名", "confidence":0.9}
优先级：agreement_with_others↑；分歧大时 mean_hd95_to_others↓；radiomics_judge 与 classification_anchor 一致者优先；形态学与设备匹配次之。
```

### 1.2 System prompt — append Path A (classification consensus)

Appended at runtime when independent classifiers agree (`classification_anchor` set).
Example anchor shown as `恶性`:

```

分类锚点：恶性。与锚点矛盾的 radiomics_judge 降权。
```

### 1.3 System prompt — append when no classification consensus

```

无分类锚点。以 radiomics 内部一致性与 agreement 为主。
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
只输出纯JSON。（brief：勿输出 reasoning 字段）格式：{"selected_model": "模型名称", "confidence": 0.95}
```

`formatted_predictions_json` 由 `SegmentationAgent.format_predictions_for_agent()` 生成，
含各模型质量指标、可选 `radiomics_judge`、`group_uncertainty` / `disagreement` 等字段。

### 1.5 LLM output JSON schema

- Single mask (LLM JSON): `{"selected_model": "<name>", "confidence": 0.0-1.0}` — no `reasoning` key.
- `routing_log.jsonl` still stores `reasoning: "-"` for successful LLM routes (filled by the pipeline).

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
禁止思考/Markdown。只输出一行 JSON：selected_model, selected_class, confidence(0-1)。勿输出 reasoning 字段。
```

### 2.2 System prompt — top-k fusion (`top_k > 1`)

```
你是甲状腺超声多模型预测整合专家，选出最值得信任的 5 个模型（按信任度从高到低），用于对各类别概率取平均融合。

【字段】top_confidence（或 top_confidence_calibrated）为主置信度。entropy、margin_top2、num_models_same_class。

【决策序】综合判断哪 5 个模型组合最可信，优先级与单选类似，需考虑组合互补性。

【输出】只输出纯JSON（无Markdown/思考），首尾为{}。字段：selected_models(长度恰好5的字符串数组)。勿输出 reasoning、selected_class 或 confidence。
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

- Single (LLM JSON): `{"selected_model": "...", "selected_class": "良性|恶性", "confidence": 0.0-1.0}` — no `reasoning` key.
- Top-k (LLM JSON): `{"selected_models": ["...", ...]}` — no `reasoning` / `selected_class` / `confidence`.
- Log field `reasoning` may still be `"-"` or empty for LLM rows (pipeline default).

---

## 3. Classification — LLM arbitration when classifiers disagree (`resolve_path_b`)

- Invoked when `classification_consensus == false` and `enable_agent: true`.
- Current config `enable_agent`: `True`
- `brief_routing_prompt`: `True`

### 3.1 System prompt

```
甲状腺超声分类裁决：各独立分类模型未形成共识。
依据 user JSON 中的 independent_models、autogluon_based_on_selected_mask、segmentation_decision。
禁止思考过程与 Markdown。只输出一行 JSON：
{"selected_class":"恶性或良性", "confidence":0.0-1.0}
勿输出 reasoning 字段。信号均模糊时略倾向恶性但降低 confidence。
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

`{"selected_class": "良性|恶性", "confidence": 0.0-1.0}` — no `reasoning` key.

(No `selected_model`; stored decision uses `selected_model: agent_path_b_llm`.)

### 3.4 Arbitration without LLM

- `enable_agent: false` → weighted soft vote (`method: path_b_static_softvote`).

---

## 4. Path A classification (no LLM)

- `task: cls_path_a`, `method: classification_consensus` — logged in `routing_log.jsonl` only.

---

## 5. Full prompt examples for Supplementary

Set `pipeline.routing_log_include_prompts: true`, run pipeline on anonymized cases, and copy `prompts` from `routing_log.jsonl` (fields `system` / `user`).
