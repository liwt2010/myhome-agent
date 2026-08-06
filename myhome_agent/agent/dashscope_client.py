"""阿里云 DashScope 客户端（Qwen / Qwen-VL）

v3.0 国产首选。
- Qwen-Plus：日常对话（¥0.0004/1K）
- Qwen2-VL-Max：视觉（¥0.02/1K image）
- 128K 上下文
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)


class DashScopeClient:
    """阿里云 DashScope 客户端（Qwen 系列）"""

    def __init__(self, model: str = "qwen-plus", **kwargs):
        self.model = model
        self.api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
        if not self.api_key:
            logger.warning("DASHSCOPE_API_KEY 未配置")

    def messages(
        self,
        system: str,
        messages: list,
        max_tokens: int = 1500,
        tools: list | None = None,
    ) -> Any:
        """OpenAI 兼容协议（v3.0 统一接口）"""
        try:
            import aiohttp
        except ImportError:
            return self._fallback_stub(system, messages)

        import asyncio

        # 转换 messages
        formatted_messages = [{"role": "system", "content": system}] if system else []
        formatted_messages.extend(messages)

        payload = {
            "model": self.model,
            "input": {"messages": formatted_messages},
            "parameters": {"max_tokens": max_tokens},
        }
        if tools:
            payload["parameters"]["tools"] = tools

        return asyncio.run(self._async_call(payload, messages, system, max_tokens))

    async def _async_call(self, payload, messages, system, max_tokens):
        """异步 → 同步"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/services/aigc/text-generation/generation",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    data = await resp.json()
                    output = data.get("output", {})
                    text = output.get("text", "（Qwen 无响应）")
                    usage = data.get("usage", {})
                    return self._wrap_response(text, usage)
        except Exception as e:
            logger.error(f"Qwen 调用失败: {e}")
            return self._fallback_stub(system, messages)

    def _wrap_response(self, text: str, usage: dict):
        """v3.0 统一响应格式"""
        from ..agent.llm import LLMResponse
        return LLMResponse(
            text=text,
            tool_calls=[],
            stop_reason="end_turn",
            usage={
                "input_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        )

    def _fallback_stub(self, system, messages):
        from ..agent.llm import LLMResponse, MockLLMClient
        logger.warning("Qwen 降级到 mock")
        return MockLLMClient().messages(system=system, messages=messages)