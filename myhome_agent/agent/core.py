"""智能体核心：LLM 工具调用循环（v2.19 — 抽象 LLMClient + 反馈环）

实现标准的 Agent Loop：
  用户消息 → system prompt（含家庭快照）→ LLM → tool_calls → 执行工具
  → 结果回传 LLM → ... → text 回复用户

会话历史存储在 SQLite chat_history 表中，支持跨重启恢复。

v2.19 修订：
- 抽象 _LLMClient 拆出到 llm.py（Mock / DeepSeek / 未来 Ollama）
- 加入 §5.6b 控制指令反馈环（v0.1 基础版：自动 + 重试一次）
- 默认 DeepSeek，无 anthropic 依赖
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from typing import Any, Iterator

from ..config import AGENT_MAX_TOKENS, AGENT_MODEL, DEEPSEEK_API_KEY, HISTORY_TURNS
from ..memory.store import Store
from .llm import LLMResponse, MockLLMClient, get_default_client
from .prompt import build_system_prompt
from .tools import TOOLS, execute_tool, to_openai_tools

logger = logging.getLogger(__name__)

# ============================================================
# §5.6b 反馈环（v0.1 基础版）
# ============================================================


class ControlFeedback:
    """v0.1 控制指令反馈环

    行为：
    - 工具执行后立即返回（v0.1 不等待物理确认）
    - 写一条 feedback 记录
    - 失败重试 1 次（v0.2 接 §5.6b 完整三态：auto/edge/manual）
    """

    def __init__(self, store: Store | None = None):
        self.store = store
        self._pending: dict[str, dict] = {}

    def record(self, control_id: str, device_id: str, action: str, result: dict) -> None:
        """记录一次控制执行"""
        self._pending[control_id] = {
            "device_id": device_id,
            "action": action,
            "result": result,
            "ts": int(time.time()),
        }
        logger.info(
            "feedback: %s device=%s action=%s ok=%s",
            control_id, device_id, action, result.get("success", False),
        )

    def verify(self, control_id: str, current_state: dict | None = None) -> bool:
        """验证上次控制是否成功（v0.1 简化版：仅看 result.success）"""
        rec = self._pending.get(control_id)
        if not rec:
            return False
        return rec["result"].get("success", False)

    def undo_stack(self) -> list[dict]:
        """返回最近的反馈栈（用于撤销）"""
        return [
            {"control_id": cid, **rec}
            for cid, rec in self._pending.items()
        ]


# ============================================================
# Agent 主类（v2.19 修订）
# ============================================================


class Agent:
    """家庭私人管家核心。

    使用方式:
        store = Store("data/myhome.db")
        agent = Agent(store)
        reply = agent.chat("今天家里怎么样？")
    """

    def __init__(
        self,
        store: Store,
        api_key: str | None = None,
        registry=None,
        llm_client: Any | None = None,
        use_feedback: bool = True,
    ):
        self.store = store
        self.registry = registry
        # v2.19：使用抽象 LLMClient（默认走环境变量选择）
        if llm_client is not None:
            self.llm = llm_client
        else:
            self.llm = get_default_client()
        self.history_turns = HISTORY_TURNS
        self.feedback = ControlFeedback(store) if use_feedback else None

    def chat(self, user_message: str, session_id: str | None = None) -> str:
        """与智能体对话，返回文本回复。"""
        if session_id is None:
            session_id = uuid.uuid4().hex[:12]
        self.store.append_chat(session_id, "user", user_message)

        system_prompt = build_system_prompt(self.store)
        messages = self._build_messages(session_id)
        return self._run_loop(session_id, system_prompt, messages)

    def _build_messages(self, session_id: str) -> list[dict]:
        """从 chat_history 重建最近 N 轮对话消息。

        OpenAI 兼容的角色：system / user / assistant / tool
        assistant 工具调用 → tool_calls
        工具结果 → role=tool, tool_call_id=...
        """
        raw = self.store.get_chat(session_id, limit_turns=self.history_turns)
        messages: list[dict] = []

        for row in raw:
            role = row["role"]
            content = row["content"]
            try:
                content = json.loads(content) if isinstance(content, str) else content
            except Exception:
                pass

            if role == "system":
                messages.append({"role": "system", "content": content if isinstance(content, str) else ""})
            elif role == "user":
                messages.append({"role": "user", "content": content if isinstance(content, str) else ""})
            elif role == "assistant":
                if isinstance(content, str):
                    messages.append({"role": "assistant", "content": content})
                else:
                    # 列表：包含 text 和 tool_use 块，转 OpenAI 形式
                    text = ""
                    tool_calls = []
                    for blk in content:
                        if blk.get("type") == "text":
                            text += blk.get("text", "")
                        elif blk.get("type") == "tool_use":
                            tool_calls.append({
                                "id": blk["id"],
                                "type": "function",
                                "function": {
                                    "name": blk["name"],
                                    "arguments": json.dumps(blk.get("input") or {}, ensure_ascii=False),
                                },
                            })
                    msg = {"role": "assistant", "content": text or None}
                    if tool_calls:
                        msg["tool_calls"] = tool_calls
                    messages.append(msg)
            elif role == "tool":
                if isinstance(content, list):
                    for blk in content:
                        if blk.get("type") == "tool_result":
                            messages.append({
                                "role": "tool",
                                "tool_call_id": blk.get("tool_use_id", ""),
                                "content": blk.get("content", ""),
                            })
        return messages

    def _run_loop(self, session_id: str, system_prompt: str, messages: list[dict]) -> str:
        max_iterations = 10
        for iteration in range(max_iterations):
            logger.debug("Agent 迭代 %d/%d", iteration + 1, max_iterations)

            # v2.19：用新 LLMClient 接口
            tools_schema = to_openai_tools()
            response: LLMResponse = self.llm.messages(
                system=system_prompt,
                messages=messages,
                tools=tools_schema,
            )

            # 转 Claude 风格 blocks（向后兼容 store）
            content_blocks: list[dict] = []
            if response.text:
                content_blocks.append({"type": "text", "text": response.text})
            for tc in response.tool_calls:
                content_blocks.append({
                    "type": "tool_use",
                    "id": tc["id"],
                    "name": tc["function"]["name"],
                    "input": tc["function"]["arguments"]
                    if isinstance(tc["function"]["arguments"], dict)
                    else {},
                })

            # 写回 assistant 消息
            self.store.append_chat(
                session_id, "assistant",
                json.dumps(content_blocks, ensure_ascii=False),
            )

            if not response.tool_calls:
                return response.text or "（智能体没有返回内容）"

            # 执行所有工具
            confirm_msg: str | None = None
            new_tool_msgs: list[dict] = []

            for tc in response.tool_calls:
                name = tc["function"]["name"]
                raw_args = tc["function"]["arguments"]
                if isinstance(raw_args, str):
                    try:
                        args = json.loads(raw_args)
                    except Exception:
                        args = {"_raw": raw_args}
                else:
                    args = raw_args or {}

                result = execute_tool(name, args, self.store, self.registry)

                # §5.6b 反馈环：记录控制指令
                if self.feedback and name in ("control_device",):
                    self.feedback.record(
                        control_id=tc["id"],
                        device_id=args.get("device_id", "unknown"),
                        action=args.get("action", "unknown"),
                        result=result,
                    )

                if result.get("needs_confirm") and not confirm_msg:
                    confirm_msg = result["message"]

                # 把工具调用串回消息列表
                new_tool_msgs.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(result, ensure_ascii=False),
                })
                logger.debug("工具 %s: %s", name, result.get("message", ""))

            # 把工具结果作为 user 追加（OpenAI tool_call_id 兼容）
            messages.append({
                "role": "user",
                "content": json.dumps(new_tool_msgs, ensure_ascii=False),
            })
            self.store.append_chat(
                session_id, "user",
                json.dumps(new_tool_msgs, ensure_ascii=False),
            )

            if confirm_msg:
                return confirm_msg

        logger.warning("Agent 达到最大迭代次数 %d", max_iterations)
        return "抱歉，处理过程中遇到了一些问题，请稍后再试。"


class AgentSession:
    """单会话 Agent 包装，给 WebSocket 用。"""

    def __init__(self, store: Store, api_key: str | None = None, registry=None, llm_client=None):
        self.agent = Agent(store, api_key, registry, llm_client=llm_client)
        self.session_id = uuid.uuid4().hex[:12]

    def send(self, message: str) -> str:
        return self.agent.chat(message, session_id=self.session_id)
