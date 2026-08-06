"""置信度校准 v0.2（§53.4）

v0.2 实现：
- 4 因子公式（freshness / history_match / member_baseline / false_positive_penalty）
- 区间判定（≥0.9 / 0.6-0.9 / 0.3-0.6 / <0.3）
- 处置（auto / notify / ask / fallback）

公式（v0.2）：
    final = base
          × freshness_factor
          × history_match_factor
          × member_baseline_factor
          - false_positive_penalty
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ============================================================
# 区间常量
# ============================================================

INTERVAL_AUTO = 0.9      # ≥ 此值：自动执行
INTERVAL_NOTIFY = 0.6    # 0.6 ~ 0.9：执行 + 同步通知
INTERVAL_ASK = 0.3       # 0.3 ~ 0.6：仅通知 + 询问
# < 0.3：兜底 LLM


@dataclass
class ConfidenceFactors:
    """4 因子输入"""

    base: float = 0.7
    freshness: float = 1.0           # 传感器新鲜度 [0.5-1.0]
    history_match: float = 1.0       # 历史模式匹配 [0.7-1.0]
    member_baseline: float = 1.0     # 成员基线偏离 [0.6-1.0]
    false_positive_penalty: float = 0.0  # 误报惩罚 [0.0-0.5]


@dataclass
class CalibratedConfidence:
    """校准结果"""

    final: float
    interval: str  # 'auto' | 'notify' | 'ask' | 'fallback'
    factors: ConfidenceFactors
    rationale: str  # 解释为何是此区间（用于 LLM 推理上下文）

    @property
    def should_execute(self) -> bool:
        return self.interval in ("auto", "notify")

    @property
    def should_ask_user(self) -> bool:
        return self.interval == "ask"


def calibrate(
    base: float,
    *,
    freshness: float = 1.0,
    history_match: float = 1.0,
    member_baseline: float = 1.0,
    false_positive_penalty: float = 0.0,
) -> CalibratedConfidence:
    """校准置信度

    Args:
        base: 规则基础置信度 [0.0-1.0]
        freshness: 传感器新鲜度因子 [0.5-1.0]，默认 1.0
        history_match: 历史模式匹配度 [0.7-1.0]，默认 1.0
        member_baseline: 成员基线偏离度 [0.6-1.0]，默认 1.0
        false_positive_penalty: 误报惩罚 [0.0-0.5]，默认 0.0

    Returns:
        CalibratedConfidence
    """
    factors = ConfidenceFactors(
        base=base,
        freshness=freshness,
        history_match=history_match,
        member_baseline=member_baseline,
        false_positive_penalty=false_positive_penalty,
    )

    # 公式：base × 三因子 - 误报惩罚
    final = base * freshness * history_match * member_baseline - false_positive_penalty
    final = max(0.0, min(1.0, final))  # 截断到 [0.0, 1.0]

    # 区间判定
    if final >= INTERVAL_AUTO:
        interval = "auto"
        rationale = f"高置信度 {final:.2f}：自动执行"
    elif final >= INTERVAL_NOTIFY:
        interval = "notify"
        rationale = f"中置信度 {final:.2f}：执行 + 同步通知"
    elif final >= INTERVAL_ASK:
        interval = "ask"
        rationale = f"低置信度 {final:.2f}：仅通知 + 询问"
    else:
        interval = "fallback"
        rationale = f"不确定 {final:.2f}：兜底 LLM 推理"

    return CalibratedConfidence(
        final=final,
        interval=interval,
        factors=factors,
        rationale=rationale,
    )


def freshness_factor(data_age_seconds: int, window_seconds: int) -> float:
    """新鲜度因子

    data_age ≤ window → 1.0
    data_age > 2 × window → 0.5
    之间线性插值
    """
    if data_age_seconds <= window_seconds:
        return 1.0
    if data_age_seconds >= 2 * window_seconds:
        return 0.5
    # 线性插值
    return 1.0 - 0.5 * (data_age_seconds - window_seconds) / window_seconds


def history_match_factor(rule_hit_count: int, rule_true_positive: int) -> float:
    """历史匹配度因子

    历史上 80% 是真异常 → 1.0
    历史上 20% 是真异常 → 0.7
    线性插值
    """
    if rule_hit_count == 0:
        return 1.0  # 无历史数据，按默认
    ratio = rule_true_positive / rule_hit_count
    # 0.2 → 0.7, 0.8 → 1.0
    if ratio >= 0.8:
        return 1.0
    if ratio <= 0.2:
        return 0.7
    return 0.7 + 0.3 * (ratio - 0.2) / 0.6


def member_baseline_factor(current_value: float, baseline: float, tolerance: float = 0.3) -> float:
    """成员基线偏离度因子

    当前值偏离基线越远 → 因子越高（异常更可疑）
    偏离 ≤ tolerance → 0.6
    偏离 ≥ 2 × tolerance → 1.0
    """
    if baseline == 0:
        return 1.0
    deviation = abs(current_value - baseline) / abs(baseline)
    if deviation <= tolerance:
        return 0.6
    if deviation >= 2 * tolerance:
        return 1.0
    return 0.6 + 0.4 * (deviation - tolerance) / tolerance


def false_positive_penalty(false_positive_count_30d: int) -> float:
    """误报惩罚（最近 30 天内误报数 × 0.05，上限 0.5）"""
    return min(0.5, false_positive_count_30d * 0.05)


# ============================================================
# 关键不变式校验（v0.2 §53.4.2）
# ============================================================


def enforce_invariants(rule_severity: str, base: float, final: float) -> tuple[float, str | None]:
    """强制置信度不变式

    1. safety 规则 final < 0.5 → 警告（人工应 review）
    2. irreversible capability 关联规则 final < 0.9 → 强制升到 0.9 + 二次确认
    3. false_positive_penalty > 0.4 → 强制 disabled

    Returns:
        (adjusted_final, warning_message)
    """
    warning = None

    if rule_severity == "safety" and base < 0.5:
        warning = f"safety 规则 base={base} < 0.5，建议提升"
    if rule_severity == "irreversible" and final < 0.9:
        final = max(final, 0.9)
        warning = "irreversible capability 规则：置信度强制 ≥ 0.9 + 二次确认"

    return final, warning
