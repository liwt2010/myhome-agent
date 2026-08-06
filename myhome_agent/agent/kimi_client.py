"""月之暗面 Kimi 客户端（128K 长上下文）

v3.0 长文本首选。
- Moonshot-v1-128k（¥0.012/1K）
- 128K tokens 上下文
- 长摘要 / 长对话首选
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class KimiClient:
    """Moonshot AI Kimi 客户端"""

    def __init__(self, model: str = "moonshot-v1-128k", **kwargs):
        self.model = model
        self.api_key = os.getenv("KIMI_API_KEY", "")
        self.base_url = "https://api.moonshot.cn/v1"
        if not self.api_key:
            logger.warning("KIMI_API_KEY 未配置")

    def messages(self, system: str, messages: list, max_tokens: int = 1500, tools=None) -> Any:
        try:
            import requests
        except ImportError:
            from ..agent.llm import MockLLMClient
            return MockLLMClient().messages(system=system, messages=messages)

        formatted = [{"role": "system", "content": system}] if system else []
        formatted.extend(messages)

        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                json={"model": self.model, "messages": formatted, "max_tokens": max_tokens},
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=60,
            )
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return self._wrap(text, usage)
        except Exception as e:
            logger.error(f"Kimi 失败: {e}")
            from ..agent.llm import MockLLMClient
            return MockLLMClient().messages(system=system, messages=messages)

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