"""LLM 兜底推理 v0.3（§53.4.3）

v0.3 实现：
- 触发条件：final_confidence < 0.3 + ≥2 条同时低可信 + 信号矛盾
- 调用 LLMClient.analyze 拿结构化建议
- **不直接执行动作**——必须经 §5.3 高危确认（safety）或 §52 通知（care）
- 限流：单家庭 ≤10 次/天
- §36 household_id 强制隔离（防止跨家庭上下文泄漏）
- 降级：DeepSeek key 缺 → 静默（不调 mock；mock 不适合做"兜底"）

为什么不用 MockLLMClient：
- 兜底的本质是"我确定不了，调 LLM 帮忙"
- mock 会"假装推理"，对真实情况没帮助
- v0.3 行为：无 api_key 时 fallback 静默跳过，规则回到"低置信度，不执行"
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from ..agent.llm import DeepSeekLLMClient, LLMResponse

if TYPE_CHECKING:
    from .engine import Rule, RuleStore

logger = logging.getLogger(__name__)


# 限流：单家庭 10 次/天
FALLBACK_DAILY_LIMIT = 10
# 触发阈值
FALLBACK_CONFIDENCE_THRESHOLD = 0.3
# 多规则同时低可信（触发条件之一）
FALLBACK_MULTI_RULE_THRESHOLD = 2


# ============================================================
# 兜底结果
# ============================================================


@dataclass
class FallbackResult:
    """兜底推理结果"""

    triggered: bool
    reason: str
    suggestion: str = ""
    confidence_after: float = 0.0
    suggested_action: str = ""  # 'ask_user' | 'fire_safety' | 'fire_care' | 'no_action'
    rationale: str = ""
    ts: int = field(default_factory=lambda: int(time.time()))


# ============================================================
# 兜底推理
# ============================================================


class FallbackReasoner:
    """v0.3 兜底推理器

    触发判定 → 限流检查 → 构造 prompt → 调 LLM → 解析响应
    """

    def __init__(
        self,
        rule_store: "RuleStore",
        llm_client: Any | None = None,
    ):
        self.rule_store = rule_store
        # v0.3 默认尝试 DeepSeek
        if llm_client is None:
            llm_client = self._try_get_deepseek()
        self.llm_client = llm_client
        # 每日计数
        self._daily_count: dict[tuple[int, str], int] = {}  # (household_id, day_str) → count

    @staticmethod
    def _try_get_deepseek():
        """尝试获取 DeepSeek 客户端；失败返回 None（静默降级）"""
        try:
            return DeepSeekLLMClient()  # 用环境变量
        except Exception as e:
            logger.info(f"LLM 兜底：DeepSeek 不可用 ({e})，降级到静默")
            return None

    def should_trigger(
        self,
        rule: "Rule",
        current_confidence: float,
        low_confidence_rules_count: int,
        has_contradiction: bool,
        household_id: int = 1,
    ) -> tuple[bool, str]:
        """判定是否触发兜底

        Returns:
            (should_trigger, reason)
        """
        if current_confidence >= FALLBACK_CONFIDENCE_THRESHOLD:
            return False, f"置信度 {current_confidence:.2f} ≥ {FALLBACK_CONFIDENCE_THRESHOLD}，不触发"

        if low_confidence_rules_count < FALLBACK_MULTI_RULE_THRESHOLD:
            return False, f"仅 {low_confidence_rules_count} 条低可信规则，不触发"

        if not has_contradiction:
            return False, "信号无矛盾，不触发"

        # 限流检查
        if self._is_over_limit(household_id):
            return False, f"今日兜底次数已达上限 {FALLBACK_DAILY_LIMIT}"

        if self.llm_client is None:
            return False, "无 LLM 客户端可用，兜底静默"

        return True, "满足全部触发条件"

    def reason(
        self,
        rule: "Rule",
        evidence: dict,
        household_id: int = 1,
    ) -> FallbackResult:
        """执行兜底推理"""
        should, reason = self.should_trigger(
            rule=rule,
            current_confidence=evidence.get("confidence", 0.0),
            low_confidence_rules_count=evidence.get("low_confidence_count", 1),
            has_contradiction=evidence.get("has_contradiction", False),
            household_id=household_id,
        )

        if not should:
            return FallbackResult(triggered=False, reason=reason)

        prompt = self._build_prompt(rule, evidence)

        try:
            response: LLMResponse = self.llm_client.messages(
                system=self._build_system_prompt(),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
            )
        except Exception as e:
            logger.error(f"LLM 兜底调用失败: {e}")
            return FallbackResult(
                triggered=True,
                reason=f"LLM 调用失败: {e}",
                suggestion="规则无法判定，请人工核查",
                suggested_action="ask_user",
                rationale=str(e),
            )

        result = self._parse_response(response.text)
        result.triggered = True
        result.reason = reason
        result.ts = int(time.time())

        self._increment_count(household_id)

        self.rule_store.log_fire(
            rule_id=rule.id,
            household_id=household_id,
            kind="llm_fallback",
            confidence=result.confidence_after,
            detail={
                "llm_model": self.llm_client.model,
                "llm_answer": result.suggestion[:200],
                "suggested_action": result.suggested_action,
                "tokens": response.usage,
            },
        )

        logger.info(
            f"[fallback] {rule.id} → action={result.suggested_action} conf={result.confidence_after:.2f}"
        )
        return result

    def _build_prompt(self, rule, evidence: dict) -> str:
        """构造 LLM 兜底 prompt"""
        attrs = evidence.get("attributes", {})
        return f"""# 家庭规则触发，但置信度不足

## 触发的规则
- ID: {rule.id}
- 描述: {rule.description}
- 严重度: {rule.severity}
- 基础置信度: {rule.confidence_base}

## 当前证据
{json.dumps(evidence, ensure_ascii=False, indent=2)}

## 你的任务
分析以上证据，给出：
1. **建议动作**：fire_safety（紧急）/ fire_care（关注）/ ask_user（询问用户）/ no_action（不行动）
2. **置信度** [0.0-1.0]：你对这个判断的确信程度
3. **简短理由**（1-2 句）

## 输出格式（严格遵守）
```json
{{
  "action": "fire_safety|fire_care|ask_user|no_action",
  "confidence": 0.85,
  "rationale": "客厅摄像头检测到人形 + 床压未离床 + 持续 5 分钟 → 可能是访客，建议 fire_care 并通知"
}}
```

**安全约束**：
- 不要执行实际动作（你只做判断）
- 不要臆造数据（基于 evidence）
- 不要给出法律/医疗建议（转人工）
"""

    def _build_system_prompt(self) -> str:
        return """你是 myhome-agent 家庭管家的"兜底推理"模块。

你的职责：当规则引擎置信度不足时，做最终判断。

## 严格约束
- 不执行任何动作（不调设备、不发通知）
- 只输出结构化 JSON 建议
- 涉及 safety（紧急/急救）时建议 fire_safety
- 涉及 care（关注/异常）时建议 fire_care
- 拿不准时建议 ask_user
- 显然无异常时建议 no_action

## 数据安全
- 不外发 token、密码、API key
- 不臆造证据
"""

    def _parse_response(self, text: str) -> FallbackResult:
        """解析 LLM JSON 响应（带容错）"""
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"LLM 兜底响应非 JSON: {text[:100]}")
            return FallbackResult(
                triggered=True,
                reason="LLM 响应非 JSON，降级为 ask_user",
                suggestion=text[:200],
                confidence_after=0.3,
                suggested_action="ask_user",
                rationale="LLM 响应格式异常",
            )

        action = data.get("action", "ask_user")
        if action not in ("fire_safety", "fire_care", "ask_user", "no_action"):
            action = "ask_user"

        return FallbackResult(
            triggered=False,
            reason="",
            suggestion=data.get("rationale", ""),
            confidence_after=float(data.get("confidence", 0.3)),
            suggested_action=action,
            rationale=data.get("rationale", ""),
        )

    def _is_over_limit(self, household_id: int) -> bool:
        day = time.strftime("%Y-%m-%d")
        key = (household_id, day)
        return self._daily_count.get(key, 0) >= FALLBACK_DAILY_LIMIT

    def _increment_count(self, household_id: int) -> None:
        day = time.strftime("%Y-%m-%d")
        key = (household_id, day)
        self._daily_count[key] = self._daily_count.get(key, 0) + 1

    def get_daily_count(self, household_id: int = 1) -> int:
        day = time.strftime("%Y-%m-%d")
        return self._daily_count.get((household_id, day), 0)


# ============================================================
# 兜底结果
# ============================================================


@dataclass
class FallbackResult:
    """兜底推理结果"""

    triggered: bool
    reason: str
    suggestion: str = ""
    confidence_after: float = 0.0
    suggested_action: str = ""  # 'ask_user' | 'fire_safety' | 'fire_care' | 'no_action'
    rationale: str = ""
    ts: int = field(default_factory=lambda: int(time.time()))


# ============================================================
# 兜底推理
# ============================================================


class FallbackReasoner:
    """v0.3 兜底推理器

    触发判定 → 限流检查 → 构造 prompt → 调 LLM → 解析响应
    """

    def __init__(
        self,
        rule_store: RuleStore,
        llm_client: Any | None = None,
    ):
        self.rule_store = rule_store
        # v0.3 默认尝试 DeepSeek
        if llm_client is None:
            llm_client = self._try_get_deepseek()
        self.llm_client = llm_client
        # 每日计数
        self._daily_count: dict[tuple[int, str], int] = {}  # (household_id, day_str) → count

    @staticmethod
    def _try_get_deepseek():
        """尝试获取 DeepSeek 客户端；失败返回 None（静默降级）"""
        try:
            return DeepSeekLLMClient()  # 用环境变量
        except Exception as e:
            logger.info(f"LLM 兜底：DeepSeek 不可用 ({e})，降级到静默")
            return None

    def should_trigger(
        self,
        rule: Rule,
        current_confidence: float,
        low_confidence_rules_count: int,
        has_contradiction: bool,
        household_id: int = 1,
    ) -> tuple[bool, str]:
        """判定是否触发兜底

        Returns:
            (should_trigger, reason)
        """
        if current_confidence >= FALLBACK_CONFIDENCE_THRESHOLD:
            return False, f"置信度 {current_confidence:.2f} ≥ {FALLBACK_CONFIDENCE_THRESHOLD}，不触发"

        if low_confidence_rules_count < FALLBACK_MULTI_RULE_THRESHOLD:
            return False, f"仅 {low_confidence_rules_count} 条低可信规则，不触发"

        if not has_contradiction:
            return False, "信号无矛盾，不触发"

        # 限流检查
        if self._is_over_limit(household_id):
            return False, f"今日兜底次数已达上限 {FALLBACK_DAILY_LIMIT}"

        if self.llm_client is None:
            return False, "无 LLM 客户端可用，兜底静默"

        return True, "满足全部触发条件"

    def reason(
        self,
        rule: Rule,
        evidence: dict,
        household_id: int = 1,
    ) -> FallbackResult:
        """执行兜底推理

        Args:
            rule: 触发的规则
            evidence: 当前证据（matched predicates + 传感器数据）
            household_id: 多家庭隔离
        """
        should, reason = self.should_trigger(
            rule=rule,
            current_confidence=evidence.get("confidence", 0.0),
            low_confidence_rules_count=evidence.get("low_confidence_count", 1),
            has_contradiction=evidence.get("has_contradiction", False),
            household_id=household_id,
        )

        if not should:
            return FallbackResult(
                triggered=False,
                reason=reason,
            )

        # 构造 prompt（v0.3 简化版）
        prompt = self._build_prompt(rule, evidence)

        try:
            response: LLMResponse = self.llm_client.messages(
                system=self._build_system_prompt(),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
            )
        except Exception as e:
            logger.error(f"LLM 兜底调用失败: {e}")
            return FallbackResult(
                triggered=True,
                reason=f"LLM 调用失败: {e}",
                suggestion="规则无法判定，请人工核查",
                suggested_action="ask_user",
                rationale=str(e),
            )

        # 解析响应
        result = self._parse_response(response.text)
        result.triggered = True
        result.reason = reason
        result.ts = int(time.time())

        # 计数
        self._increment_count(household_id)

        # 写 audit log
        self.rule_store.log_fire(
            rule_id=rule.id,
            household_id=household_id,
            kind="llm_fallback",
            confidence=result.confidence_after,
            detail={
                "llm_model": self.llm_client.model,
                "llm_answer": result.suggestion[:200],
                "suggested_action": result.suggested_action,
                "tokens": response.usage,
            },
        )

        logger.info(
            f"[fallback] {rule.id} → action={result.suggested_action} conf={result.confidence_after:.2f}"
        )
        return result

    def _build_prompt(self, rule: Rule, evidence: dict) -> str:
        """构造 LLM 兜底 prompt"""
        attrs = evidence.get("attributes", {})
        return f"""# 家庭规则触发，但置信度不足

## 触发的规则
- ID: {rule.id}
- 描述: {rule.description}
- 严重度: {rule.severity}
- 基础置信度: {rule.confidence_base}

## 当前证据
{json.dumps(evidence, ensure_ascii=False, indent=2)}

## 你的任务
分析以上证据，给出：
1. **建议动作**：fire_safety（紧急）/ fire_care（关注）/ ask_user（询问用户）/ no_action（不行动）
2. **置信度** [0.0-1.0]：你对这个判断的确信程度
3. **简短理由**（1-2 句）

## 输出格式（严格遵守）
```json
{{
  "action": "fire_safety|fire_care|ask_user|no_action",
  "confidence": 0.85,
  "rationale": "客厅摄像头检测到人形 + 床压未离床 + 持续 5 分钟 → 可能是访客，建议 fire_care 并通知"
}}
```

**安全约束**：
- 不要执行实际动作（你只做判断）
- 不要臆造数据（基于 evidence）
- 不要给出法律/医疗建议（转人工）
"""

    def _build_system_prompt(self) -> str:
        return """你是 myhome-agent 家庭管家的"兜底推理"模块。

你的职责：当规则引擎置信度不足时，做最终判断。

## 严格约束
- 不执行任何动作（不调设备、不发通知）
- 只输出结构化 JSON 建议
- 涉及 safety（紧急/急救）时建议 fire_safety
- 涉及 care（关注/异常）时建议 fire_care
- 拿不准时建议 ask_user
- 显然无异常时建议 no_action

## 数据安全
- 不外发 token、密码、API key
- 不臆造证据
"""

    def _parse_response(self, text: str) -> FallbackResult:
        """解析 LLM JSON 响应（带容错）"""
        # 尝试提取 JSON
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # fallback：自然语言解析
            logger.warning(f"LLM 兜底响应非 JSON: {text[:100]}")
            return FallbackResult(
                triggered=True,
                reason="LLM 响应非 JSON，降级为 ask_user",
                suggestion=text[:200],
                confidence_after=0.3,
                suggested_action="ask_user",
                rationale="LLM 响应格式异常",
            )

        action = data.get("action", "ask_user")
        if action not in ("fire_safety", "fire_care", "ask_user", "no_action"):
            action = "ask_user"

        return FallbackResult(
            triggered=False,  # 由 caller 决定
            reason="",
            suggestion=data.get("rationale", ""),
            confidence_after=float(data.get("confidence", 0.3)),
            suggested_action=action,
            rationale=data.get("rationale", ""),
        )

    def _is_over_limit(self, household_id: int) -> bool:
        day = time.strftime("%Y-%m-%d")
        key = (household_id, day)
        return self._daily_count.get(key, 0) >= FALLBACK_DAILY_LIMIT

    def _increment_count(self, household_id: int) -> None:
        day = time.strftime("%Y-%m-%d")
        key = (household_id, day)
        self._daily_count[key] = self._daily_count.get(key, 0) + 1

    def get_daily_count(self, household_id: int = 1) -> int:
        day = time.strftime("%Y-%m-%d")
        return self._daily_count.get((household_id, day), 0)
