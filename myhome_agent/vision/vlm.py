"""VLM 多模态视觉（v3.0 国产优先）

v3.0 实现：
- VLMAnalyzer（Qwen2-VL-Max 国产首选 / 智谱 GL-4V 备选 / GPT-4o / Claude 4 Sonnet Vision 国外补充）
- YOLO 快速初筛（每秒 5 帧）+ VLM 精细判断（事件驱动）双层架构
- 限流 5/小时/家（避免成本爆）
- §54 视觉规则升级（VLM 替 YOLO 部分场景）

双层架构：
- Layer 1：YOLO（每秒 5 帧，毫秒级）→ 检测到事件 / 抽样
- Layer 2：VLM（秒级）→ 自然语言描述 + 语义判断
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================
# VLM 后端（v3.0 国产优先）
# ============================================================


class VLMBackend:
    """v3.0 多模态 LLM 后端抽象"""

    async def describe(
        self,
        image_b64: str,
        prompt: str,
        max_tokens: int = 500,
    ) -> str:
        raise NotImplementedError


class Qwen2VLBackend(VLMBackend):
    """v3.0 国产视觉首选：Qwen2-VL-Max（阿里云）"""

    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY", "")

    async def describe(self, image_b64: str, prompt: str, max_tokens: int = 500) -> str:
        if not self.api_key:
            return "（Qwen2-VL 未配置 DASHSCOPE_API_KEY）"
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
                    json={
                        "model": "qwen-vl-max",
                        "input": {
                            "messages": [
                                {
                                    "role": "user",
                                    "content": [
                                        {"image": f"data:image/jpeg;base64,{image_b64}"},
                                        {"text": prompt},
                                    ],
                                }
                            ]
                        },
                        "parameters": {"max_tokens": max_tokens},
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30,
                ) as resp:
                    data = await resp.json()
                    return data.get("output", {}).get("text", "（VLM 无响应）")
        except Exception as e:
            logger.error(f"Qwen2-VL 失败: {e}")
            return f"（VLM 错误：{e}）"


class GL4VBackend(VLMBackend):
    """v3.0 智谱 GL-4V（视觉）"""

    def __init__(self):
        self.api_key = os.getenv("ZHIPU_API_KEY", "")

    async def describe(self, image_b64: str, prompt: str, max_tokens: int = 500) -> str:
        if not self.api_key:
            return "（GL-4V 未配置 ZHIPU_API_KEY）"
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                    json={
                        "model": "glm-4v",
                        "messages": [{
                            "role": "user",
                            "content": [
                                {"type": "image_url",
                                 "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                                {"type": "text", "text": prompt},
                            ],
                        }],
                        "max_tokens": max_tokens,
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30,
                ) as resp:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"GL-4V 失败: {e}")
            return f"（VLM 错误：{e}）"


class GPT4oVisionBackend(VLMBackend):
    """OpenAI GPT-4o vision（v3.0 国外补充）"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")

    async def describe(self, image_b64: str, prompt: str, max_tokens: int = 500) -> str:
        if not self.api_key:
            return "（GPT-4o 未配置 OPENAI_API_KEY）"
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    json={
                        "model": "gpt-4o",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "image_url",
                                     "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                                    {"type": "text", "text": prompt},
                                ],
                            }
                        ],
                        "max_tokens": max_tokens,
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30,
                ) as resp:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"GPT-4o 失败: {e}")
            return f"（VLM 错误：{e}）"


class Claude4VisionBackend(VLMBackend):
    """Anthropic Claude 4 Sonnet Vision（v3.0 国外补充）"""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")

    async def describe(self, image_b64: str, prompt: str, max_tokens: int = 500) -> str:
        if not self.api_key:
            return "（Claude 4 Vision 未配置 ANTHROPIC_API_KEY）"
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    json={
                        "model": "claude-4-sonnet",
                        "max_tokens": max_tokens,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "image",
                                     "source": {"type": "base64", "media_type": "image/jpeg",
                                                 "data": image_b64}},
                                    {"type": "text", "text": prompt},
                                ],
                            }
                        ],
                    },
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                    },
                    timeout=30,
                ) as resp:
                    data = await resp.json()
                    return data["content"][0]["text"]
        except Exception as e:
            logger.error(f"Claude 4 失败: {e}")
            return f"（VLM 错误：{e}）"


# ============================================================
# VLM 分析器
# ============================================================


@dataclass
class VLMResult:
    """VLM 分析结果"""
    description: str
    should_fire: bool
    severity: str  # 'safety' | 'care' | 'info' | 'no_action'
    confidence: float
    model_used: str
    latency_ms: int
    cost_usd: float


# v3.0 限流
VLM_RATE_LIMIT_PER_HOUR = 5


class VLMAnalyzer:
    """v3.0 VLM 视觉分析器（国产优先）

    YOLO 快速初筛（每秒 5 帧）→ 事件触发 → VLM 精细分析（国产 Qwen2-VL 优先）
    """

    def __init__(self, llm_router=None, vision_pipeline=None):
        from ..agent.llm_router import LLMRouter
        self.router = llm_router or LLMRouter()
        self.pipeline = vision_pipeline
        # 国产 2 个 + 国外 2 个
        self.backends: dict[str, VLMBackend] = {
            "qwen2_vl": Qwen2VLBackend(),       # 国产首选
            "glm4v": GL4VBackend(),              # 国产备选
            "gpt4o": GPT4oVisionBackend(),       # 国外补充
            "claude4": Claude4VisionBackend(),   # 国外补充
        }
        self._call_count: dict[str, int] = {}
        self._last_call: dict[str, float] = {}

    def _rate_limit_check(self, household_id: int) -> bool:
        """限流：单家庭 5 次/小时"""
        now = time.time()
        hour_key = (household_id, int(now // 3600))
        count = self._call_count.get(hour_key, 0)
        if count >= VLM_RATE_LIMIT_PER_HOUR:
            logger.warning(f"VLM 限流：{household_id} 已达 {VLM_RATE_LIMIT_PER_HOUR}/h")
            return False
        return True

    def _record_call(self, household_id: int):
        hour_key = (household_id, int(time.time() // 3600))
        self._call_count[hour_key] = self._call_count.get(hour_key, 0) + 1

    def _encode_image(self, frame) -> str:
        """numpy frame → base64"""
        import base64
        import cv2
        _, buf = cv2.imencode('.jpg', frame)
        return base64.b64encode(buf.tobytes()).decode()

    async def analyze(
        self,
        frame,
        context: dict | None = None,
        household_id: int = 1,
        force: bool = False,
    ) -> VLMResult | None:
        if not force and not self._rate_limit_check(household_id):
            return None

        image_b64 = self._encode_image(frame)
        prompt = self._build_prompt(context or {})

        # 路由（v3.0 国产优先）
        decision = self.router.route(
            task="vision",
            context_size=len(prompt) // 4 + 800,
            privacy=context.get("privacy", "public") if context else "public",
        )

        backend_key = self._provider_to_backend(decision.provider)
        backend = self.backends.get(backend_key)
        if not backend:
            logger.warning(f"VLM backend 不可用: {decision.provider}")
            # 国产降级
            for fallback in ("qwen2_vl", "glm4v"):
                backend = self.backends[fallback]
                backend_key = fallback
                break

        start = time.time()
        try:
            description = await backend.describe(image_b64, prompt)
        except Exception as e:
            logger.error(f"VLM 错误: {e}")
            return None
        latency_ms = int((time.time() - start) * 1000)

        self._record_call(household_id)

        should_fire, severity, confidence = self._classify(description, context or {})
        cost = self._estimate_cost(decision.provider, len(prompt) // 4 + len(description) // 4)

        return VLMResult(
            description=description,
            should_fire=should_fire,
            severity=severity,
            confidence=confidence,
            model_used=decision.model,
            latency_ms=latency_ms,
            cost_usd=cost,
        )

    def _provider_to_backend(self, provider: str) -> str | None:
        """v3.0 国产优先映射"""
        MAP = {
            "qwen_vl": "qwen2_vl",        # 国产首选
            "qwen": "qwen2_vl",            # 文字 Qwen 失败 → 视觉 Qwen
            "zhipu": "glm4v",              # 智谱文字失败 → 视觉
            "deepseek": None,              # 无 vision
            "kimi": None,
            "wenxin": None,
            "openai_gpt4o": "gpt4o",       # 国外补充
            "openai_gpt5": "gpt4o",
            "anthropic_claude4": "claude4",
            "gemini_15": "claude4",         # Gemini 无 backend → Claude fallback
            "local_qwen7b": None,
            "local_glm6b": None,
            "stub": None,
        }
        return MAP.get(provider)

    def _build_prompt(self, context: dict) -> str:
        """v3.0 VLM prompt：基于 context 智能定制"""
        base = "你是一个家庭安全管家。请用中文简要描述这张图片。"

        if "yolo_result" in context:
            base += f"\n\nYOLO 初步检测：{context['yolo_result']}"
        if "rule_id" in context:
            base += f"\n触发规则：{context['rule_id']}"
        if "question" in context:
            base += f"\n特别关注：{context['question']}"

        base += "\n\n如果发现异常（摔倒 / 火灾 / 陌生人 / 老人异常行为等），请明确指出。"
        return base

    def _classify(self, description: str, context: dict) -> tuple[bool, str, float]:
        """解析 VLM 描述 → (should_fire, severity, confidence)"""
        desc_lower = description.lower()
        safety_keywords = ["摔倒", "求救", "火灾", "燃烧", "冒烟", "无法", "严重"]
        care_keywords = ["不舒服", "异常", "困惑", "挣扎", "老年人", "虚弱"]
        if any(kw in desc_lower for kw in safety_keywords):
            return True, "safety", 0.85
        if any(kw in desc_lower for kw in care_keywords):
            return True, "care", 0.7
        return False, "no_action", 0.9

    def _estimate_cost(self, provider: str, tokens: int) -> float:
        from ..agent.llm_router import PROVIDER_CAPS
        caps = PROVIDER_CAPS.get(provider, {})
        return (caps.get("cost_per_1m_input", 0)
                + caps.get("cost_per_1m_output", 0)) * tokens / 1_000_000


# ============================================================
# 集成到 §54 视觉规则（升级 v3.0）
# ============================================================


VLM_ENHANCED_RULES = {
    "elderly_fall_living_room_v1": {
        "yolo_check": "fall_detected",
        "vlm_question": "这个人是否真的摔倒？姿态如何？是否痛苦？",
        "severity": "safety",
    },
    "elderly_dementia_outdoor_v1": {
        "yolo_check": "person",
        "vlm_question": "这个人是否迷茫？是否在找路？是否带着行李？",
        "severity": "safety",
    },
    "smoke_detector_v1": {
        "yolo_check": "fire_detected",
        "vlm_question": "是否真有火灾？是否有人在附近？危险程度？",
        "severity": "safety",
    },
}