#!/usr/bin/env python3
"""导出 LLM 路由器 prompt 模板与解码参数（B6 Supplementary）。

用法:
  python scripts/export_router_spec.py [--config config/config.yaml] [--out docs/supplementary/router_spec.md]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import repo_path
import yaml

_ROOT = repo_path.install()

from segmentation.agent import (
    RADIOMICS_JUDGE_SPEC_PLACEHOLDER,
    SegmentationAgent,
    seg_llm_system_append,
)
from classification.agent import (
    LLMClassificationAgent,
    PATH_B_LLM_SYSTEM_PROMPT,
    PATH_B_USER_PROMPT_EXAMPLE,
)


def _seg_user_prompt_template(ensemble_top_k: int, ensemble_enabled: bool) -> str:
    if ensemble_enabled and ensemble_top_k > 1:
        question = f"请选择 Top {ensemble_top_k} 个最佳模型用于 ensemble。"
        fmt = (
            '{"selected_models": ["模型1", "模型2"], "weights": [0.6, 0.4], '
            '"confidence": 0.95, "reasoning": "..."}'
        )
    else:
        question = "哪个模型提供了最佳分割结果？"
        fmt = '{"selected_model": "模型名称", "confidence": 0.95, "reasoning": "..."}'

    return f"""（运行时拼接，非独立文件）

可选前缀：分歧度量摘要（当 `include_disagreement_metrics_in_prompt: true` 时由代码生成）。

**输入设备** / **输入数据** 行（来自 `pipeline.data.device_info` 与可选 `input_data_info`）。

正文：
```
以下是 {{N}} 个分割模型的输出及质量评估：

{{formatted_predictions_json}}

{question}
只输出纯JSON。格式：{fmt}
```

`formatted_predictions_json` 由 `SegmentationAgent.format_predictions_for_agent()` 生成，
含各模型质量指标、可选 `radiomics_judge`、`group_uncertainty` / `disagreement` 等字段。"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument(
        "--out",
        default="docs/supplementary/router_spec.md",
    )
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    llm_cfg = config["shared"]["agent_llm"]
    seg_cfg = config["segmentation"].get("agent", {})
    cls_cfg = config["classification"].get("agent", {})
    judge_enabled = config.get("radiomics_judge", {}).get("enabled", False)

    seg_agent_no_judge = SegmentationAgent(llm_client=None, config=seg_cfg)
    seg_agent = SegmentationAgent(
        llm_client=None,
        config=seg_cfg,
        radiomics_judge=RADIOMICS_JUDGE_SPEC_PLACEHOLDER
        if judge_enabled
        else None,
    )
    cls_agent = LLMClassificationAgent(llm_client=None, config=cls_cfg)

    ens = seg_cfg.get("ensemble") or {}
    ens_enabled = bool(ens.get("enabled", True))
    ens_top_k = int(ens.get("top_k", 1))

    lines = [
        "# ThyroidCascadeAgent — LLM router specification (B6)",
        "",
        f"_Generated from config: `{args.config}`_",
        "",
        "## Shared decoding (`shared.agent_llm`)",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| API key | environment variable `{llm_cfg.get('api_key_env', 'DASHSCOPE_API_KEY')}` |",
        f"| base_url | `{llm_cfg.get('base_url')}` |",
        f"| model_name | `{llm_cfg.get('model_name')}` |",
        f"| temperature | `{llm_cfg.get('temperature')}` |",
        f"| max_tokens | `{llm_cfg.get('max_tokens')}` |",
        "",
        "Full config excerpt:",
        "",
        "```json",
        json.dumps(llm_cfg, ensure_ascii=False, indent=2),
        "```",
        "",
        "---",
        "",
        "## 1. Segmentation router (`SegmentationAgent`, Phase 3)",
        "",
        f"- `enable_agent`: `{seg_cfg.get('enable_agent')}`",
        f"- `include_disagreement_metrics_in_prompt`: `{seg_cfg.get('include_disagreement_metrics_in_prompt')}`",
        f"- `metadata_mode`: `{seg_cfg.get('metadata_mode', 'full')}`",
        f"- `ensemble`: `{seg_cfg.get('ensemble')}`",
        f"- `radiomics_judge.enabled` (config): `{judge_enabled}`",
        "",
        "### 1.1 System prompt — base",
        "",
        "Used when `radiomics_judge` is injected in pipeline (judge block included below).",
        "If judge is disabled at runtime, omit the radiomics paragraph in the actual call.",
        "",
        "```",
        seg_agent.system_prompt,
        "```",
        "",
    ]

    if judge_enabled:
        lines += [
            "### 1.1b System prompt — base without radiomics judge block",
            "",
            "_Only if `radiomics_judge` is not loaded:_",
            "",
            "```",
            seg_agent_no_judge.system_prompt,
            "```",
            "",
        ]

    lines += [
        "### 1.2 System prompt — append Path A (classification consensus)",
        "",
        "Appended when independent classifiers agree (`classification_anchor` set).",
        "Example anchor shown as `恶性`:",
        "",
        "```",
        seg_llm_system_append("恶性"),
        "```",
        "",
        "### 1.3 System prompt — append Path B (no classification consensus)",
        "",
        "```",
        seg_llm_system_append(None),
        "```",
        "",
        "### 1.4 User message template",
        "",
        _seg_user_prompt_template(ens_top_k, ens_enabled),
        "",
        "### 1.5 LLM output JSON schema",
        "",
    ]

    if ens_enabled and ens_top_k > 1:
        lines.append(
            f'- Ensemble: `{{"selected_models": ["<name>", ...] (length {ens_top_k}), '
            '"weights": [...], "confidence": 0.0-1.0, "reasoning": "..."}}`'
        )
    else:
        lines.append(
            '- Single mask: `{"selected_model": "<name>", "confidence": 0.0-1.0, "reasoning": "..."}`'
        )

    lines += [
        "",
        "### 1.6 Non-LLM fallbacks",
        "",
        "- `enable_agent: false` → `method: static_fallback` / `cascade_static_mask` (rule-based).",
        "- LLM parse/API failure → `method: llm_fallback` (same static selector).",
        "",
        "---",
        "",
        "## 2. Classification — standalone (`run_cls.py` / unanimous bypass)",
        "",
        f"- `enable_agent`: `{cls_cfg.get('enable_agent')}`",
        f"- `top_k`: `{cls_cfg.get('top_k')}`",
        f"- Unanimous top class across models → **no LLM** (`method: unanimous`).",
        "",
        "### 2.1 System prompt — single selection (`top_k == 1`)",
        "",
        "```",
        cls_agent.system_prompt_single,
        "```",
        "",
        "### 2.2 System prompt — top-k fusion (`top_k > 1`)",
        "",
        "```",
        cls_agent.system_prompt_multi,
        "```",
        "",
        "### 2.3 User message template",
        "",
        "```",
        "{system_prompt}",
        "",
        "输入设备: {device_info}",
        "以下为 {N} 个模型的预测(JSON)：",
        "",
        "{formatted_predictions_json}",
        "",
        "{question}",
        "```",
        "",
        "### 2.4 LLM output JSON schema",
        "",
        "- Single: `{\"selected_model\": \"...\", \"selected_class\": \"良性|恶性\", "
        "\"confidence\": 0.0-1.0, \"reasoning\": \"...\"}`",
        "- Top-k: `{\"selected_models\": [\"...\", ...], \"reasoning\": \"...\"}` "
        "(no `selected_class` / `confidence` in multi mode).",
        "",
        "---",
        "",
        "## 3. Classification — Path B (`resolve_path_b`, Phase 5, no consensus)",
        "",
        f"- Invoked when `classification_consensus == false` and `enable_agent: true`.",
        f"- Current config `enable_agent`: `{cls_cfg.get('enable_agent')}`",
        "",
        "### 3.1 System prompt",
        "",
        "```",
        PATH_B_LLM_SYSTEM_PROMPT,
        "```",
        "",
        "### 3.2 User message",
        "",
        "Single JSON string (`ensure_ascii=False`), structure:",
        "",
        "```json",
        json.dumps(PATH_B_USER_PROMPT_EXAMPLE, ensure_ascii=False, indent=2),
        "```",
        "",
        "`autogluon_based_on_selected_mask` may be `null` if AutoGluon unavailable.",
        "",
        "### 3.3 LLM output JSON schema",
        "",
        '`{"selected_class": "良性|恶性", "confidence": 0.0-1.0, "reasoning": "..."}`',
        "",
        "(No `selected_model`; stored decision uses `selected_model: agent_path_b_llm`.)",
        "",
        "### 3.4 Path B without LLM",
        "",
        "- `enable_agent: false` → weighted soft vote (`method: path_b_static_softvote`).",
        "",
        "---",
        "",
        "## 4. Path A classification (no LLM)",
        "",
        "- `task: cls_path_a`, `method: classification_consensus` — logged in `routing_log.jsonl` only.",
        "",
        "---",
        "",
        "## 5. Full prompt examples for Supplementary",
        "",
        "Set `pipeline.routing_log_include_prompts: true`, run pipeline on anonymized cases, "
        "and copy `prompts` from `routing_log.jsonl` (fields `system` / `user`).",
        "",
    ]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
