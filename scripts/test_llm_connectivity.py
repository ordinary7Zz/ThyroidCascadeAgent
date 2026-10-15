#!/usr/bin/env python3
"""最小 LLM 连通性测试：读 config 中的 agent_llm，发一条短消息并打印结果。"""

from __future__ import annotations

import argparse
import os
import sys

import yaml

from repo_path import install

install()

from openai import OpenAIError

from shared.llm_client import LLMClient


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="测试 DashScope/OpenAI 兼容 LLM 连通性")
    parser.add_argument("--config", default="config/config.yaml", help="含 shared.agent_llm 的配置")
    args = parser.parse_args()

    cfg = load_config(args.config)
    llm_cfg = cfg["shared"]["agent_llm"]
    key_env = llm_cfg.get("api_key_env", "DASHSCOPE_API_KEY")
    api_key = os.getenv(key_env, "").strip()

    base_url = llm_cfg["base_url"]
    model_name = llm_cfg["model_name"]
    print(f"base_url:   {base_url}")
    print(f"model:      {model_name}")
    print(f"api_key:    {key_env} ({'已设置' if api_key else '未设置'})")

    if not api_key:
        print(f"✗ 失败: 请 export {key_env}=<your-key>")
        return 1

    try:
        client = LLMClient(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            temperature=llm_cfg.get("temperature", 0.3),
            max_tokens=min(int(llm_cfg.get("max_tokens", 1024)), 32),
        )
    except OpenAIError as e:
        print(f"✗ 客户端初始化失败: {e}")
        return 1

    try:
        reply = client.chat(
            "You are a connectivity test assistant.",
            "Reply with exactly one word: OK",
            max_retries=0,
        )
    except RuntimeError as e:
        print(f"✗ 请求失败: {e}")
        return 1

    preview = (reply or "").strip().replace("\n", " ")[:120]
    print(f"✓ 连通正常，模型回复: {preview}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
