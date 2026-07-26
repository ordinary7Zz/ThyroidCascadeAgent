"""
OpenAI 兼容 LLM 客户端，支持重试与指数退避。

合并自两个 Agent 仓库中分散的 LLM 调用逻辑，统一为一处。
API key 通过构造函数参数传入（由 config 从环境变量读取），不硬编码。
"""

from __future__ import annotations

import time
from typing import Optional

from openai import OpenAI, APIError, APITimeoutError, RateLimitError


class LLMClient:
    """OpenAI 兼容 API 客户端（支持 DashScope/Qwen 等）。"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model_name: str = "qwen2.5-32b-instruct",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
    ) -> str:
        """
        发送 chat completion 请求，返回模型文本响应。

        失败时按指数退避重试（1s, 2s, 4s, ...），最多 max_retries 次。
        重试覆盖的异常：APIError, APITimeoutError, RateLimitError。

        Args:
            system_prompt: 系统提示词。
            user_prompt: 用户提示词。
            max_retries: 最大重试次数。
            retry_base_delay: 首次重试延迟（秒），后续翻倍。

        Returns:
            模型响应文本 (choices[0].message.content)。

        Raises:
            RuntimeError: 所有重试均失败后抛出。
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        last_error: Optional[Exception] = None
        for attempt in range(max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                return response.choices[0].message.content

            except (APIError, APITimeoutError, RateLimitError) as e:
                last_error = e
                if attempt < max_retries:
                    delay = retry_base_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue

        raise RuntimeError(
            f"LLM 调用失败（重试 {max_retries} 次后仍报错）: {last_error}"
        )
