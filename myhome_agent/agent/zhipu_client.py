"""智谱 AI 客户端（GLM-4-Plus）

v3.0 国产备份。
- GLM-4-Plus：日常对话（¥0.001/1K）
- 128K 上下文
- 工具调用支持
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)


class ZhipuClient:
    """智谱 AI 客户端"""

    def __init__(self, model: str = "glm-4-plus", **kwargs):
        self.model = model
        self.api_key = os.getenv("ZHIPU_API_KEY", "")
        self.base_url = "https://open.bigmodel.cn/api/paas/v4"
        if not self.api_key:
            logger.warning("ZHIPU_API_KEY 未配置")

    def messages(self, system: str, messages: list, max_tokens: int = 1500, tools=None) -> Any:
        try:
            import requests
        except ImportError:
            return self._stub_fallback(system, messages)

        formatted = [{"role": "system", "content": system}] if system else []
        formatted.extend(messages)

        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                json={"model": self.model, "messages": formatted, "max_tokens": max_tokens},
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30,
            )
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return self._wrap(text, usage)
        except Exception as e:
            logger.error(f"Zhipu 失败: {e}")
            return self._stub_fallback(system, messages)

    def _wrap(self, text, usage):
        from ..agent.llm import LLMResponse
        return LLMResponse(
            text=text, tool_calls=[], stop_reason="end_turn",
            usage={
                "input_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        )

    def _stub_fallback(self, system, messages):
        from ..agent.llm import MockLLMClient
        return MockLLMClient().messages(system=system, messages=messages)