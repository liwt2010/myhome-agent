"""国产优先多 LLM 路由（v3.0）

v3.0 国产为主，国外为辅：
- 默认 5 国产：DeepSeek / Qwen（DashScope）/ 智谱 GLM / 文心一言 / Kimi
- 3 国外补充：OpenAI / Anthropic / Gemini
- 预算 80/20 国产/国外
- 国产优先 fallback 链路

v3.0 真实跑通需做：
- 5 国产 backend 集成（DeepSeek 已有 + Qwen + 智谱 + 文心 + Kimi）
- 3 国外 backend（用户自选接入）
- 重写路由决策（先国产 → 国产不行 → 国外）
"""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================
# 任务类型
# ============================================================


class TaskType(str, Enum):
    CHAT = "chat"
    FALLBACK = "fallback"
    VISION = "vision"
    CODE = "code"
    PLANNING = "planning"
    LONG_CONTEXT = "long_context"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"


class PrivacyLevel(str, Enum):
    PUBLIC = "public"
    SENSITIVE = "sensitive"


# ============================================================
# Provider 能力矩阵（v3.0 国货优先）
# ============================================================


# 国产 Provider
PROVIDER_CAPS = {
    # ========== 国产 5 个（默认）==========
    "deepseek": {
        "name": "DeepSeek-V3",
        "vendor": "DeepSeek（中国）",
        "model": "deepseek-chat",
        "context_window": 64_000,
        "supports_vision": False,
        "supports_tools": True,
        "cost_per_1m_input": 0.14,    # USD
        "cost_per_1m_output": 0.28,
        "privacy": "cloud_cn",
        "regions": ["cn", "global"],
        "speed": "fast",        # fast / medium / slow
        "quality": "high",       # high / medium / low
        "default_priority": 100,  # 路由优先级（数字大优先）
    },
    "qwen": {
        "name": "通义千问 Qwen-Plus",
        "vendor": "阿里云（中国）",
        "model": "qwen-plus",
        "context_window": 128_000,
        "supports_vision": False,
        "supports_tools": True,
        "cost_per_1m_input": 0.08,    # ¥0.5/1K tokens ≈ $0.07
        "cost_per_1m_output": 0.16,
        "privacy": "cloud_cn",
        "regions": ["cn"],
        "speed": "fast",
        "quality": "high",
        "default_priority": 95,
    },
    "qwen_vl": {
        "name": "通义千问 Qwen2-VL-Max（视觉）",
        "vendor": "阿里云（中国）",
        "model": "qwen-vl-max",
        "context_window": 32_000,
        "supports_vision": True,
        "supports_tools": False,
        "cost_per_1m_input": 0.4,     # 视觉更贵
        "cost_per_1m_output": 0.4,
        "privacy": "cloud_cn",
        "regions": ["cn"],
        "speed": "medium",
        "quality": "high",
        "default_priority": 90,
    },
    "zhipu": {
        "name": "智谱 GLM-4-Plus",
        "vendor": "智谱 AI（中国）",
        "model": "glm-4-plus",
        "context_window": 128_000,
        "supports_vision": False,
        "supports_tools": True,
        "cost_per_1m_input": 0.07,
        "cost_per_1m_output": 0.07,
        "privacy": "cloud_cn",
        "regions": ["cn"],
        "speed": "fast",
        "quality": "high",
        "default_priority": 85,
    },
    "wenxin": {
        "name": "文心一言 ERNIE-4.0",
        "vendor": "百度（中国）",
        "model": "ernie-4.0-8k",
        "context_window": 8_000,
        "supports_vision": False,
        "supports_tools": True,
        "cost_per_1m_input": 0.12,    # ¥0.8/1K
        "cost_per_1m_output": 0.12,
        "privacy": "cloud_cn",
        "regions": ["cn"],
        "speed": "fast",
        "quality": "high",
        "default_priority": 80,
    },
    "kimi": {
        "name": "月之暗面 Kimi",
        "vendor": "Moonshot AI（中国）",
        "model": "moonshot-v1-128k",
        "context_window": 128_000,
        "supports_vision": False,
        "supports_tools": True,
        "cost_per_1m_input": 0.12,    # ¥0.8/1K
        "cost_per_1m_output": 0.12,
        "privacy": "cloud_cn",
        "regions": ["cn", "global"],
        "speed": "fast",
        "quality": "high",
        "default_priority": 75,
    },

    # ========== 国外 3 个（补充）==========
    "openai_gpt4o": {
        "name": "OpenAI GPT-4o",
        "vendor": "OpenAI（美国）",
        "model": "gpt-4o",
        "context_window": 128_000,
        "supports_vision": True,
        "supports_tools": True,
        "cost_per_1m_input": 2.5,
        "cost_per_1m_output": 10.0,
        "privacy": "cloud_us",
        "regions": ["global"],
        "speed": "fast",
        "quality": "very_high",
        "default_priority": 50,    # 国产优先，所以国外默认低
    },
    "openai_gpt5": {
        "name": "OpenAI GPT-5",
        "vendor": "OpenAI（美国）",
        "model": "gpt-5",
        "context_window": 200_000,
        "supports_vision": True,
        "supports_tools": True,
        "cost_per_1m_input": 5.0,
        "cost_per_1m_output": 20.0,
        "privacy": "cloud_us",
        "regions": ["global"],
        "speed": "medium",
        "quality": "very_high",
        "default_priority": 45,
    },
    "anthropic_claude4": {
        "name": "Anthropic Claude 4 Sonnet",
        "vendor": "Anthropic（美国）",
        "model": "claude-4-sonnet",
        "context_window": 200_000,
        "supports_vision": True,
        "supports_tools": True,
        "cost_per_1m_input": 3.0,
        "cost_per_1m_output": 15.0,
        "privacy": "cloud_us",
        "regions": ["global"],
        "speed": "fast",
        "quality": "very_high",
        "default_priority": 40,
    },
    "gemini_15": {
        "name": "Google Gemini 1.5 Pro",
        "vendor": "Google（美国）",
        "model": "gemini-1.5-pro",
        "context_window": 1_000_000,  # 1M tokens
        "supports_vision": True,
        "supports_tools": True,
        "cost_per_1m_input": 1.25,
        "cost_per_1m_output": 5.0,
        "privacy": "cloud_us",
        "regions": ["global"],
        "speed": "fast",
        "quality": "very_high",
        "default_priority": 35,
    },

    # ========== 本地（v3.1 计划，v3.0 stub）==========
    "local_qwen7b": {
        "name": "本地 Qwen2-7B-Instruct（Ollama）",
        "vendor": "阿里 + 社区（本地）",
        "model": "qwen2:7b-instruct",
        "context_window": 32_000,
        "supports_vision": False,
        "supports_tools": True,
        "cost_per_1m_input": 0.0,
        "cost_per_1m_output": 0.0,
        "privacy": "local",
        "regions": ["self-hosted"],
        "speed": "fast",  # 在 4090 上
        "quality": "medium",
        "default_priority": 200,  # 隐私最优先
    },
    "local_glm6b": {
        "name": "本地 ChatGLM3-6B（Ollama）",
        "vendor": "智谱 + 清华（本地）",
        "model": "chatglm3:6b",
        "context_window": 8_000,
        "supports_vision": False,
        "supports_tools": True,
        "cost_per_1m_input": 0.0,
        "cost_per_1m_output": 0.0,
        "privacy": "local",
        "regions": ["self-hosted"],
        "speed": "fast",
        "quality": "medium",
        "default_priority": 195,
    },

    # ========== Mock（开发）==========
    "stub": {
        "name": "Stub (Mock)",
        "vendor": "本地",
        "model": "mock-1",
        "context_window": 8_000,
        "supports_vision": False,
        "supports_tools": False,
        "cost_per_1m_input": 0.0,
        "cost_per_1m_output": 0.0,
        "privacy": "local",
        "regions": ["any"],
        "speed": "fast",
        "quality": "low",
        "default_priority": 0,
    },

    # ========== v3.0 测试：model-info.forwe.store 网关 ==========
    "model_info": {
        "name": "Model Info (OpenAI 兼容网关)",
        "vendor": "forwe.store 代理",
        "model": "model-info",
        "context_window": 32_000,  # 估
        "supports_vision": False,
        "supports_tools": True,
        "cost_per_1m_input": 0.0,    # 暂不知
        "cost_per_1m_output": 0.0,
        "privacy": "cloud",
        "regions": ["any"],
        "speed": "medium",
        "quality": "medium",
        "default_priority": 60,
    },
}


# ============================================================
# 任务 → 默认 provider（v3.0 国货优先）
# ============================================================


TASK_DEFAULT_LLM = {
    TaskType.CHAT: "deepseek",         # 日常对话默认 DeepSeek
    TaskType.FALLBACK: "deepseek",     # 兜底
    TaskType.VISION: "qwen_vl",        # 视觉默认国产 Qwen2-VL
    TaskType.CODE: "deepseek",         # 代码
    TaskType.PLANNING: "deepseek",     # 规划
    TaskType.LONG_CONTEXT: "kimi",     # 128K 默认 Kimi（便宜）
    TaskType.TRANSLATION: "qwen",      # 翻译 Qwen 中文好
    TaskType.SUMMARIZATION: "kimi",    # 128K 上下文摘要
}


# 国货 fallback 链
CN_FALLBACK = {
    "qwen_vl": "qwen",          # 视觉失败 → 文字兜底
    "kimi": "deepseek",         # Kimi 失败 → DeepSeek
    "wenxin": "qwen",
    "zhipu": "qwen",
    "qwen": "deepseek",
    "deepseek": "stub",
}

# 国外 fallback 链
INTL_FALLBACK = {
    "openai_gpt5": "openai_gpt4o",
    "openai_gpt4o": "anthropic_claude4",
    "anthropic_claude4": "gemini_15",
    "gemini_15": "stub",
}

# 国货 → 国外 跨域 fallback
CN_TO_INTL_FALLBACK = {
    "deepseek": "openai_gpt4o",   # DeepSeek 不可用 → GPT-4o
    "qwen": "anthropic_claude4",  # Qwen 不可用 → Claude 4
    "qwen_vl": "openai_gpt4o",    # Qwen VL 不可用 → GPT-4o
    "kimi": "anthropic_claude4",
    "wenxin": "gemini_15",
    "zhipu": "openai_gpt4o",
}


# ============================================================
# 路由决策
# ============================================================


@dataclass
class RouteDecision:
    provider: str
    model: str
    reason: str
    cost_estimate_usd: float
    fallback_provider: str | None = None
    task: TaskType = TaskType.CHAT
    vendor: str = ""


class LLMRouter:
    """v3.0 国产优先多 LLM 路由"""

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.budget_monthly_usd = float(os.getenv("MYHOME_LLM_BUDGET", "20.0"))
        # 国产/国外预算分配（默认 80/20）
        self.cn_budget_pct = float(self.config.get("cn_budget_pct", 0.8))
        self.intl_budget_pct = 1.0 - self.cn_budget_pct
        # 默认 provider
        self.preferred_provider = self.config.get("preferred", "deepseek")
        # 隐私模式
        self.privacy_mode = PrivacyLevel(
            self.config.get("privacy", "public")
        )
        # 用量
        self._usage: dict[str, dict] = {}  # (provider, month) → stats

    def route(
        self,
        task: TaskType,
        context_size: int = 0,
        privacy: PrivacyLevel | None = None,
        force_provider: str | None = None,
        require_vision: bool = False,
    ) -> RouteDecision:
        """v3.0 国产优先智能路由

        决策顺序：
        1. 强制 provider
        2. 隐私模式 → 本地
        3. 任务默认
        4. 视觉能力
        5. 上下文大小
        6. 国产预算检查
        7. 国外预算检查（仅 20%）
        8. Fallback
        """
        privacy = privacy or self.privacy_mode

        # 1. 强制 provider
        if force_provider and force_provider in PROVIDER_CAPS:
            return self._decision(force_provider, task, "user 强制")

        # 2. 隐私 → 本地
        if privacy == PrivacyLevel.SENSITIVE:
            return self._decision("local_qwen7b", task, "隐私模式 → 本地 Qwen2-7B")

        # 3. 任务默认（国产优先）
        provider = TASK_DEFAULT_LLM.get(task, "deepseek")
        path_segments = [f"task={task.value} default={provider}"]

        # v3.0.1: 检查默认是否可用
        if not self._provider_available(provider):
            path_segments.append(f"{provider} 不可用")
            # 找替代国产
            for fb in ("deepseek", "qwen", "kimi", "zhipu", "qwen_vl", "stub"):
                if fb != provider and self._provider_available(fb):
                    provider = fb
                    path_segments.append(f"→ {fb}")
                    break

        # 4. 视觉能力检查
        if task == TaskType.VISION or require_vision:
            if not PROVIDER_CAPS[provider].get("supports_vision"):
                path_segments.append(f"{provider} 无 vision")
                for v in ("qwen_vl", "glm4v", "gpt4o", "claude4", "stub"):
                    if self._provider_available(v):
                        provider = v
                        path_segments.append(f"→ {provider}")
                        break

        # 5. 上下文大小匹配
        if context_size > 100_000:
            for long_p in ("kimi", "claude4", "gemini_15", "deepseek", "stub"):
                if self._provider_available(long_p):
                    provider = long_p
                    path_segments.append(f"long {context_size} → {long_p}")
                    break
        elif context_size > 50_000:
            for long_p in ("kimi", "claude4", "deepseek", "stub"):
                if self._provider_available(long_p):
                    provider = long_p
                    path_segments.append(f"long {context_size} → {long_p}")
                    break

        # 6. 国产预算检查
        if not self._within_cn_budget(provider, context_size):
            # 国产超预算 → 试其他国产
            cn_fallback = self._cn_fallback_provider(provider)
            if cn_fallback and self._within_cn_budget(cn_fallback, context_size):
                return self._decision(cn_fallback, task, " / ".join(path_segments) + f" → {cn_fallback}")

            # 国产全超预算 → 试国外（仅 20% 配额）
            intl_fallback = self._intl_fallback_provider()
            if intl_fallback and self._within_intl_budget(intl_fallback, context_size):
                return self._decision(intl_fallback, task, " / ".join(path_segments) + f" → {intl_fallback}")

            # 全超 → stub
            return self._decision("stub", task, " / ".join(path_segments) + " → stub（全超）")

        return self._decision(provider, task, " / ".join(path_segments))

    def _decision(self, provider: str, task: TaskType, reason: str) -> RouteDecision:
        caps = PROVIDER_CAPS.get(provider, {})
        cost = self._estimate_cost(provider, 1000)
        return RouteDecision(
            provider=provider,
            model=caps.get("model", "?"),
            reason=reason,
            cost_estimate_usd=cost,
            fallback_provider=self._cn_fallback_provider(provider) or self._intl_fallback_provider(),
            task=task,
            vendor=caps.get("vendor", ""),
        )

    def _estimate_cost(self, provider: str, tokens: int) -> float:
        caps = PROVIDER_CAPS.get(provider, {})
        return (caps.get("cost_per_1m_input", 0)
                + caps.get("cost_per_1m_output", 0)) * tokens / 1_000_000

    def _within_cn_budget(self, provider: str, context_size: int) -> bool:
        if PROVIDER_CAPS.get(provider, {}).get("privacy") != "cloud_cn":
            return True  # 非国产不查 cn budget
        budget_cn = self.budget_monthly_usd * self.cn_budget_pct
        if budget_cn <= 0:
            return False
        estimated = self._estimate_cost(provider, max(context_size, 1000))
        return (self.get_current_spend_cn() + estimated) <= budget_cn

    def _within_intl_budget(self, provider: str, context_size: int) -> bool:
        if PROVIDER_CAPS.get(provider, {}).get("privacy") != "cloud_us":
            return True
        budget_intl = self.budget_monthly_usd * self.intl_budget_pct
        if budget_intl <= 0:
            return False
        estimated = self._estimate_cost(provider, max(context_size, 1000))
        return (self.get_current_spend_intl() + estimated) <= budget_intl

    def _cn_fallback_provider(self, failed: str) -> str | None:
        return CN_FALLBACK.get(failed)

    def _intl_fallback_provider(self) -> str | None:
        """国外首选（按 budget_pct 排）"""
        # 简单：gpt-4o 优先（性价比高）
        if self._within_intl_budget("openai_gpt4o", 1000):
            return "openai_gpt4o"
        if self._within_intl_budget("anthropic_claude4", 1000):
            return "anthropic_claude4"
        if self._within_intl_budget("gemini_15", 1000):
            return "gemini_15"
        return "stub"

    def get_current_spend(self) -> float:
        return self.get_current_spend_cn() + self.get_current_spend_intl()

    def get_current_spend_cn(self) -> float:
        month = time.strftime("%Y-%m")
        return sum(
            stat.get("cost_usd", 0.0)
            for (p, m), stat in self._usage.items()
            if m == month and PROVIDER_CAPS.get(p, {}).get("privacy") == "cloud_cn"
        )

    def get_current_spend_intl(self) -> float:
        month = time.strftime("%Y-%m")
        return sum(
            stat.get("cost_usd", 0.0)
            for (p, m), stat in self._usage.items()
            if m == month and PROVIDER_CAPS.get(p, {}).get("privacy") == "cloud_us"
        )

    def record_usage(self, provider: str, input_tokens: int, output_tokens: int):
        month = time.strftime("%Y-%m")
        key = (provider, month)
        if key not in self._usage:
            self._usage[key] = {"input": 0, "output": 0, "cost_usd": 0.0}
        caps = PROVIDER_CAPS[provider]
        cost = (input_tokens * caps["cost_per_1m_input"]
                + output_tokens * caps["cost_per_1m_output"]) / 1_000_000
        self._usage[key]["input"] += input_tokens
        self._usage[key]["output"] += output_tokens
        self._usage[key]["cost_usd"] += cost

    def get_stats(self) -> dict:
        cn_providers = [p for p, c in PROVIDER_CAPS.items() if c.get("privacy") == "cloud_cn"]
        intl_providers = [p for p, c in PROVIDER_CAPS.items() if c.get("privacy") == "cloud_us"]
        return {
            "budget_monthly_usd": self.budget_monthly_usd,
            "cn_budget_pct": self.cn_budget_pct,
            "intl_budget_pct": self.intl_budget_pct,
            "current_spend_cn_usd": round(self.get_current_spend_cn(), 4),
            "current_spend_intl_usd": round(self.get_current_spend_intl(), 4),
            "available_cn": [p for p in cn_providers if self._provider_available(p)],
            "available_intl": [p for p in intl_providers if self._provider_available(p)],
            "available_local": ["local_qwen7b"] if self._provider_available("local_qwen7b") else [],
        }

    def _provider_available(self, provider: str) -> bool:
        """v3.0 检查 provider key 配置"""
        KEY_MAP = {
            "deepseek": "DEEPSEEK_API_KEY",
            "qwen": "DASHSCOPE_API_KEY",
            "qwen_vl": "DASHSCOPE_API_KEY",
            "zhipu": "ZHIPU_API_KEY",
            "wenxin": "WENXIN_API_KEY",
            "kimi": "KIMI_API_KEY",
            "openai_gpt4o": "OPENAI_API_KEY",
            "openai_gpt5": "OPENAI_API_KEY",
            "anthropic_claude4": "ANTHROPIC_API_KEY",
            "gemini_15": "GOOGLE_API_KEY",
            "local_qwen7b": "MYHOME_LOCAL_LLM_URL",
            "local_glm6b": "MYHOME_LOCAL_LLM_URL",
            "model_info": "MODEL_INFO_API_KEY",  # v3.0 测试
            "stub": None,  # 永远可用
        }
        env_var = KEY_MAP.get(provider)
        if env_var is None:
            return True  # stub
        return bool(os.getenv(env_var))


# ============================================================
# Provider 工厂
# ============================================================


def get_llm_client(provider: str = None, **kwargs):
    """v3.0 国货优先工厂"""
    if provider == "deepseek" or provider is None:
        from ..agent.llm import DeepSeekLLMClient
        return DeepSeekLLMClient(**kwargs)
    if provider == "stub":
        from ..agent.llm import MockLLMClient
        return MockLLMClient(**kwargs)

    # 国产新 4 个
    if provider == "qwen" or provider == "qwen_vl":
        from .dashscope_client import DashScopeClient
        return DashScopeClient(model=PROVIDER_CAPS[provider]["model"], **kwargs)
    if provider == "zhipu":
        from .zhipu_client import ZhipuClient
        return ZhipuClient(**kwargs)
    if provider == "wenxin":
        from .wenxin_client import WenxinClient
        return WenxinClient(**kwargs)
    # v3.0 测试接入：model-info.forwe.store（OpenAI 兼容网关）
    if provider == "model_info":
        from .openai_compatible import ModelInfoClient
        return ModelInfoClient(**kwargs)

    # Kimi 128K
    if provider == "kimi":
        from .kimi_client import KimiClient
        return KimiClient(**kwargs)

    # 国外 4 个
    if provider in ("openai_gpt4o", "openai_gpt5"):
        from .openai_client import OpenAIClient
        return OpenAIClient(model=PROVIDER_CAPS[provider]["model"], **kwargs)
    if provider == "anthropic_claude4":
        from .anthropic_client import AnthropicClient
        return AnthropicClient(**kwargs)
    if provider == "gemini_15":
        from .gemini_client import GeminiClient
        return GeminiClient(**kwargs)

    # 本地
    if provider in ("local_qwen7b", "local_glm6b"):
        from .local_llama_client import LocalLlamaClient
        return LocalLlamaClient(
            model=PROVIDER_CAPS[provider]["model"],
            base_url=os.getenv("MYHOME_LOCAL_LLM_URL", "http://localhost:11434"),
            **kwargs,
        )

    raise ValueError(f"未知 provider: {provider}")