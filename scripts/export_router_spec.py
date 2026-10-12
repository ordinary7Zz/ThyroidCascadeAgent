#!/usr/bin/env python3
"""导出 LLM 路由器 prompt 模板与解码参数（B6 Supplementary）。用法: python scripts/export_router_spec.py [--config config/config.yaml]"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from segmentation.agent import SegmentationAgent
from classification.agent import LLMClassificationAgent


def main():
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

    seg_agent = SegmentationAgent(llm_client=None, config=seg_cfg)
    cls_agent = LLMClassificationAgent(llm_client=None, config=cls_cfg)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# ThyroidCascadeAgent — LLM router specification (B6)",
        "",
        "## Shared decoding (config `shared.agent_llm`)",
        "",
        "```json",
        json.dumps(llm_cfg, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Segmentation router (`SegmentationAgent`)",
        "",
        f"- `enable_agent`: {seg_cfg.get('enable_agent')}",
        f"- `ensemble`: {seg_cfg.get('ensemble')}",
        "",
        "### System prompt (base)",
        "",
        "```",
        seg_agent.system_prompt,
        "```",
        "",
        "### Single-model JSON schema (LLM output)",
        "",
        '`{"selected_model": "<name>", "confidence": 0.0-1.0, "reasoning": "..."}`',
        "",
        "## Classification router (`LLMClassificationAgent`)",
        "",
        f"- `enable_agent`: {cls_cfg.get('enable_agent')}",
        f"- `top_k`: {cls_cfg.get('top_k')}",
        "",
        "### System prompt (single selection)",
        "",
        "```",
        cls_agent.system_prompt_single,
        "```",
        "",
        "### System prompt (top-k)",
        "",
        "```",
        cls_agent.system_prompt_multi,
        "```",
        "",
        "### Path B arbitration",
        "",
        "See `classification/agent.py` → `_resolve_path_b_with_llm` (dynamic user JSON + fixed system prompt).",
        "",
        "### Single-model JSON schema",
        "",
        '`{"selected_model": "...", "selected_class": "良性|恶性", "confidence": 0.0-1.0, "reasoning": "..."}`',
        "",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
