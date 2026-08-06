"""OpenAI 兼容端点客户端（v3.0 用于 model-info.forwe.store 等）

很多 LLM 端点走 OpenAI 兼容协议（v1/chat/completions）：
- DeepSeek（已用）
- 任意代理 / 网关 / 自部署 vLLM

这个 client 是通用 OpenAI 兼容实现，支持自定义 base_url。
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)


class OpenAICompatibleClient:
    """OpenAI 兼容协议客户端

    适用场景：
    - OpenAI / DeepSeek（已用）
    - 自部署 vLLM / Ollama（OpenAI 模式）
    - LLM 网关 / 代理（model-info.forwe.store 等）
    - 其他兼容服务
    """

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = None,
        provider_name: str = "openai_compatible",
        **kwargs,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.provider_name = provider_name

        # 自动从环境变量读 base_url（per-provider 模式）
        env_key_base = provider_name.upper().replace("-", "_") + "_BASE_URL"
        if env_key_base in os.environ:
            self.base_url = os.environ[env_key_base].rstrip("/")
        env_key_api = provider_name.upper().replace("-", "_") + "_API_KEY"
        if env_key_api in os.environ:
            self.api_key = os.environ[env_key_api]

        if not self.api_key:
            logger.warning(f"{provider_name} API key 未配置")

    def messages(
        self,
        system: str,
        messages: list,
        max_tokens: int = 1500,
        tools: list | None = None,
    ) -> Any:
        try:
            import requests
        except ImportError:
            return self._stub(system, messages)

        formatted = [{"role": "system", "content": system}] if system else []
        formatted.extend(messages)

        payload = {
            "model": self.model,
            "messages": formatted,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools

        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()

            # 解析 OpenAI 格式
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            return self._wrap(text, usage)
        except Exception as e:
            logger.error(f"{self.provider_name} 失败: {e}")
            return self._stub(system, messages)

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

    def _stub(self, system, messages):
        from ..agent.llm import MockLLMClient
        return MockLLMClient().messages(system=system, messages=messages)


# 预定义快捷 client
class ModelInfoClient(OpenAICompatibleClient):
    """model-info.forwe.store 网关"""

    def __init__(self, **kwargs):
        super().__init__(
            provider_name="model_info",
            model=os.getenv("MODEL_INFO_MODEL", "model-info"),
            **kwargs,
        )


# 兼容旧有 deepseek client（保持向后兼容）
class DeepSeekClient(OpenAICompatibleClient):
    """DeepSeek（OpenAI 兼容协议）"""

    def __init__(self, **kwargs):
        super().__init__(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            provider_name="deepseek",
            **kwargs,
        )