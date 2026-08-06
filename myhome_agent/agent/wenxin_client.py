"""百度文心一言 客户端（ERNIE-4.0）

v3.0 国产补充。
- ERNIE-4.0-8K（¥0.0008/1K）
- 中文最强
- 8K 上下文（短）
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)


class WenxinClient:
    """百度文心一言客户端"""

    def __init__(self, model: str = "ernie-4.0-8k", **kwargs):
        self.model = model
        self.api_key = os.getenv("WENXIN_API_KEY", "")
        self.secret_key = os.getenv("WENXIN_SECRET_KEY", "")
        self.base_url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat"
        if not self.api_key:
            logger.warning("WENXIN_API_KEY 未配置")

    def _get_access_token(self) -> str:
        """OAuth2 获取 access_token（30 天有效）"""
        import requests
        if hasattr(self, "_cached_token") and self._cached_token_expires > time.time():
            return self._cached_token
        resp = requests.post(
            "https://aip.baidubce.com/oauth/2.0/token",
            params={"grant_type": "client_credentials",
                    "client_id": self.api_key, "client_secret": self.secret_key},
            timeout=10,
        )
        self._cached_token = resp.json()["access_token"]
        self._cached_token_expires = time.time() + 86400  # 24h 缓存
        return self._cached_token

    def messages(self, system: str, messages: list, max_tokens: int = 1500, tools=None) -> Any:
        import requests
        try:
            token = self._get_access_token()
            # 文心消息格式（content 单个 string，不支持 system）
            user_msg = messages[-1]["content"] if messages else ""
            full_prompt = f"{system}\n\n{user_msg}" if system else user_msg

            resp = requests.post(
                f"{self.base_url}/ernie-4.0-8k",
                json={"messages": [{"role": "user", "content": full_prompt}], "max_output_tokens": max_tokens},
                params={"access_token": token},
                timeout=30,
            )
            data = resp.json()
            text = data.get("result", "（文心 无响应）")
            usage = data.get("usage", {})
            return self._wrap(text, usage)
        except Exception as e:
            logger.error(f"文心 失败: {e}")
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