"""LLM 客户端抽象（v2.19 §5.1 / §28.3 路由）

v0.1 实现：抽象 _LLMClient + MockLLMClient（开发/测试用）+ DeepSeekLLMClient（生产用，走 OpenAI 兼容协议）
v2.20+ 计划：OllamaLLMClient（本地 Layer 2）
"""
from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from typing import Any

import openai


class ToolCall(dict):
    """工具调用请求（OpenAI 风格）"""

    def __init__(self, call_id: str, name: str, arguments: dict):
        super().__init__(
            {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": arguments if isinstance(arguments, str) else json.dumps(arguments, ensure_ascii=False),
                },
            }
        )


class LLMResponse:
    """统一响应结构"""

    def __init__(
        self,
        text: str = "",
        tool_calls: list[ToolCall] | None = None,
        stop_reason: str = "end_turn",
        usage: dict | None = None,
    ):
        self.text = text
        self.tool_calls = tool_calls or []
        self.stop_reason = stop_reason
        self.usage = usage or {}

    def __repr__(self):
        return f"LLMResponse(text={self.text[:40]!r}, tools={len(self.tool_calls)}, stop={self.stop_reason})"


class _LLMClient(ABC):
    """LLM 客户端抽象接口"""

    @abstractmethod
    def messages(
        self,
        *,
        system: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """发送对话并获取响应（含可选工具调用）"""
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        pass


class MockLLMClient(_LLMClient):
    """v0.1 模拟客户端

    行为：
    - 不发网络请求，本地循环
    - "今天天气怎么样" → 返回 "今天天气晴，25 度"
    - 含工具列表 + 含"开灯" → 返回工具调用
    - 其他 → 复读最后一条用户消息 + "(mock)"
    """

    def __init__(self, model: str = "mock-1"):
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    def messages(
        self,
        *,
        system: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        # 模拟网络延迟
        time.sleep(0.1)

        # 找最后一条 user 消息
        last_user = next(
            (m for m in reversed(messages) if m.get("role") == "user"),
            {"content": ""},
        )
        text = last_user.get("content", "").strip()

        # 工具调用模式：含工具 + 含控制词
        if tools and any(kw in text for kw in ("开", "关", "调", "设置", "关灯", "开灯")):
            # 简单匹配第一个工具
            tool = tools[0]
            name = tool.get("function", {}).get("name", "unknown")
            return LLMResponse(
                text="",
                tool_calls=[ToolCall(call_id="call_mock_1", name=name, arguments={"raw": text})],
                stop_reason="tool_use",
                usage={"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
            )

        # 简单回显
        if "天气" in text:
            return LLMResponse(
                text="今天天气晴，25 度，微风。（mock 响应）",
                stop_reason="end_turn",
                usage={"prompt_tokens": 80, "completion_tokens": 20, "total_tokens": 100},
            )

        if "你好" in text or "hi" in text.lower():
            return LLMResponse(
                text="你好！我是 myhome-agent 管家，当前运行在 mock 模式下。",
                stop_reason="end_turn",
                usage={"prompt_tokens": 50, "completion_tokens": 25, "total_tokens": 75},
            )

        return LLMResponse(
            text=f"（mock 模式）你说的是：{text}",
            stop_reason="end_turn",
            usage={"prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80},
        )


class DeepSeekLLMClient(_LLMClient):
    """v0.1 DeepSeek 客户端（OpenAI 兼容协议）

    用法：
        client = DeepSeekLLMClient(api_key="sk-...", model="deepseek-chat")
    """

    DEFAULT_BASE_URL = "https://api.deepseek.com"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "deepseek-chat",
        base_url: str | None = None,
        timeout: float = 30.0,
    ):
        self._model = model
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        if not self.api_key or self.api_key == "sk-xxxx":
            raise ValueError(
                "DEEPSEEK_API_KEY 未配置。请在 .env 中设置，或使用 MockLLMClient 进行开发。"
            )
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=base_url or self.DEFAULT_BASE_URL,
            timeout=timeout,
        )

    @property
    def model(self) -> str:
        return self._model

    def messages(
        self,
        *,
        system: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        # 转为 OpenAI 格式
        oai_messages = [{"role": "system", "content": system}] + messages

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": oai_messages,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        resp = self.client.chat.completions.create(**kwargs)

        # 解析响应
        choice = resp.choices[0]
        msg = choice.message

        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                import json

                try:
                    args = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, TypeError):
                    args = {"raw": tc.function.arguments}
                tool_calls.append(ToolCall(call_id=tc.id, name=tc.function.name, arguments=args))

        return LLMResponse(
            text=msg.content or "",
            tool_calls=tool_calls,
            stop_reason=choice.finish_reason or "end_turn",
            usage={
                "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
                "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
                "total_tokens": resp.usage.total_tokens if resp.usage else 0,
            },
        )


def get_default_client() -> _LLMClient:
    """工厂：按环境变量选择客户端

    - DEEPSEEK_API_KEY 已配置 + 不为占位 → DeepSeekLLMClient
    - 否则 → MockLLMClient
    """
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if api_key and api_key not in ("", "sk-xxxx"):
        try:
            return DeepSeekLLMClient(api_key=api_key)
        except Exception as e:
            print(f"[llm] DeepSeek 客户端初始化失败 ({e})，降级到 mock")
    return MockLLMClient()
