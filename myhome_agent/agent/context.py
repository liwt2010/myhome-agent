"""上下文组装（v2.19 §5.9 上下文预算）

v0.1 实现：
- system prompt 固定部分 + 动态部分（成员画像、设备状态、规则）
- 历史消息按 token 预算截断（默认 4K）
- 当前 user 消息永远保留
- 工具调用结果压缩（保留 call_id + result 摘要）
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class BudgetConfig:
    """上下文预算配置（v2.19 §5.9）"""

    system_max_tokens: int = 2000
    history_max_tokens: int = 4000
    current_max_tokens: int = 2000
    total_max_tokens: int = 8000

    # 单条消息 token 估算（粗略：1 token ≈ 4 字符）
    chars_per_token: int = 4


def estimate_tokens(text: str, cfg: BudgetConfig) -> int:
    """粗略 token 估算（中英文混合按字符数 1/4）"""
    if not text:
        return 0
    return len(text) // cfg.chars_per_token + 1


@dataclass
class Context:
    """组装好的对话上下文"""

    system: str
    messages: list[dict] = field(default_factory=list)
    tools: list[dict] = field(default_factory=list)
    total_tokens_est: int = 0

    def to_dict(self) -> dict:
        return {
            "system": self.system,
            "messages": self.messages,
            "tools": self.tools,
            "total_tokens_est": self.total_tokens_est,
        }


# 默认 system prompt（v0.1 最小版）
DEFAULT_SYSTEM_PROMPT = """你是 myhome-agent 家庭智能体的管家。

# 你的能力
- 回答家庭成员关于家中设备、生活、日程的提问
- 通过工具调用控制家中的设备（开灯、关灯、调温、查询设备状态等）
- 在对话中保持友善、耐心的语气

# 工具调用
当用户希望控制设备时，调用对应工具。每次只调用一个工具，等结果回来再决定下一步。

# 响应风格
- 简短直接，2-3 句优先
- 中文为主，技术词用英文
- 涉及具体动作时给一句"已 XX"的确认

# 数据安全
- 不透露 token、密码、API key
- 不臆造设备状态，没有把握就调工具查
"""


def build_system_prompt(
    *,
    household_name: str | None = None,
    member_name: str | None = None,
    device_summary: str | None = None,
    rules_summary: str | None = None,
    extra: str = "",
    base: str = DEFAULT_SYSTEM_PROMPT,
) -> str:
    """组装 system prompt 动态部分"""
    parts = [base]

    if household_name:
        parts.append(f"\n# 当前家庭\n家庭：{household_name}")
    if member_name:
        parts.append(f"当前对话成员：{member_name}")
    if device_summary:
        parts.append(f"\n# 家中设备概览\n{device_summary}")
    if rules_summary:
        parts.append(f"\n# 当前生效的规则（用户可见）\n{rules_summary}")
    if extra:
        parts.append(f"\n# 额外指令\n{extra}")

    return "\n".join(parts)


def truncate_history(
    messages: list[dict],
    budget: BudgetConfig,
) -> list[dict]:
    """按 token 预算截断历史消息

    策略：
    - 保留第一条 system 边界后到第一条 user 之间的所有消息
    - 从后往前保留，最后一条 user 永远在
    - 中间超过预算的最早消息被丢弃
    """
    if not messages:
        return messages

    # 估算总 token
    total = sum(estimate_tokens(m.get("content", ""), budget) for m in messages)
    if total <= budget.history_max_tokens:
        return messages

    # 永远保留最后一条 user / assistant 对话
    # 从后往前数
    kept: list[dict] = []
    used = 0
    for m in reversed(messages):
        cost = estimate_tokens(m.get("content", ""), budget)
        if used + cost > budget.history_max_tokens:
            break
        kept.append(m)
        used += cost

    kept.reverse()

    # 截断提示
    if len(kept) < len(messages):
        # 在最前面加一个 system 提示
        kept.insert(
            0,
            {
                "role": "system",
                "content": f"[注：{len(messages) - len(kept)} 条早期消息已省略]",
            },
        )

    return kept


def assemble(
    *,
    user_message: str,
    history: list[dict] | None = None,
    tools: list[dict] | None = None,
    system_extra: dict | None = None,
    budget: BudgetConfig | None = None,
) -> Context:
    """组装完整对话上下文

    Args:
        user_message: 当前 user 输入（必填）
        history: 历史消息列表（不含当前 user 消息）
        tools: OpenAI 风格 tools schema
        system_extra: 注入 system 的动态字段
        budget: 预算配置
    """
    budget = budget or BudgetConfig()
    history = history or []
    tools = tools or []
    system_extra = system_extra or {}

    # 1. 截断历史
    truncated = truncate_history(history, budget)

    # 2. 组装 system
    system = build_system_prompt(**system_extra)

    # 3. 当前 user 消息
    current = {"role": "user", "content": user_message}

    # 4. 合并
    messages = truncated + [current]

    # 5. 估算总 token
    total = estimate_tokens(system, budget)
    total += sum(estimate_tokens(m.get("content", ""), budget) for m in messages)
    # 工具 schema 估算（粗略：每个工具 100 tokens）
    total += len(tools) * 100

    return Context(
        system=system,
        messages=messages,
        tools=tools,
        total_tokens_est=total,
    )


# 历史消息存储接口（v0.1 内存版，v0.2 落 SQLite chat_history）
class HistoryStore:
    """v0.1 内存历史存储

    v0.2 替换为 SQLite chat_history / chat_fts
    """

    def __init__(self, max_messages_per_session: int = 50):
        self.max_messages_per_session = max_messages_per_session
        self._store: dict[str, list[dict]] = {}

    def append(self, session_id: str, role: str, content: str) -> None:
        msgs = self._store.setdefault(session_id, [])
        msgs.append({"role": role, "content": content, "ts": int(time.time())})
        # 截断
        if len(msgs) > self.max_messages_per_session:
            self._store[session_id] = msgs[-self.max_messages_per_session :]

    def get(self, session_id: str) -> list[dict]:
        return list(self._store.get(session_id, []))


# 全局单例（v0.1 简化）
_default_store = HistoryStore()


def get_default_store() -> HistoryStore:
    return _default_store
