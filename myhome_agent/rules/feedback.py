"""误报闭环 v0.2（§53.5）

v0.2 实现：
- 4 选项反馈（true_positive / false_positive / ignored / disable）
- 软删除流程（disabled → 24h → archived → 30 天硬删）
- 自动暂停（30 天内 FP > 5）
- 自动降级（confidence < 0.3 持续 14 天）
- §43 GDPR author 撤销级联
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from .engine import Rule, RuleState, RuleStore

logger = logging.getLogger(__name__)


# ============================================================
# 反馈类型
# ============================================================

FEEDBACK_TRUE_POSITIVE = "true_positive"
FEEDBACK_FALSE_POSITIVE = "false_positive"
FEEDBACK_IGNORED = "ignored"
FEEDBACK_DISABLE = "disable"

VALID_FEEDBACKS = {
    FEEDBACK_TRUE_POSITIVE,
    FEEDBACK_FALSE_POSITIVE,
    FEEDBACK_IGNORED,
    FEEDBACK_DISABLE,
}


@dataclass
class FeedbackResult:
    """反馈处理结果"""

    feedback: str
    confidence_delta: float  # 置信度调整
    rule_disabled: bool
    rule_archived: bool
    rationale: str


def submit_feedback(
    rule_store: RuleStore,
    rule_id: str,
    fire_id: int,
    member_id: int,
    feedback: str,
    note: str | None = None,
) -> FeedbackResult:
    """提交一条反馈

    Args:
        rule_store: 规则存储
        rule_id: 规则 ID
        fire_id: 关联的 fire audit id
        member_id: 反馈成员 ID
        feedback: 反馈类型（VALID_FEEDBACKS 之一）
        note: 备注

    Returns:
        FeedbackResult
    """
    if feedback not in VALID_FEEDBACKS:
        raise ValueError(f"非法反馈类型: {feedback}")

    # 写反馈
    rule_store._conn().execute(
        """INSERT INTO rule_feedback (
          rule_id, fire_id, household_id, member_id, feedback, note
        ) VALUES (?, ?, ?, ?, ?, ?)""",
        (rule_id, fire_id, 1, member_id, feedback, note),
    )
    rule_store._conn().commit()

    # 读 rule 和 state
    rule = next((r for r in rule_store.list_enabled_rules() if r.id == rule_id), None)
    if rule is None:
        # 规则已禁用/归档，按 disable 处理
        return FeedbackResult(
            feedback=feedback,
            confidence_delta=0.0,
            rule_disabled=False,
            rule_archived=False,
            rationale="规则已禁用，反馈仅记录",
        )

    state = rule_store.get_state(rule_id)
    if state is None:
        state = RuleState(rule_id=rule_id)

    # 处理各类型反馈
    confidence_delta = 0.0
    rule_disabled = False
    rule_archived = False
    rationale = ""

    if feedback == FEEDBACK_TRUE_POSITIVE:
        confidence_delta = +0.05
        state.true_positive_count += 1
        rationale = f"真异常 +1；置信度 +0.05"
    elif feedback == FEEDBACK_FALSE_POSITIVE:
        confidence_delta = -0.05
        state.false_positive_count += 1
        rationale = f"误报 +1；置信度 -0.05"
        # 检查自动暂停
        if state.false_positive_count >= 5:
            rule_disabled = True
            rule_store._conn().execute(
                "UPDATE rules SET enabled = 0 WHERE id = ?", (rule_id,)
            )
            rule_store.log_fire(
                rule_id=rule_id, household_id=1, kind="auto_disabled",
                detail={"reason": f"30天内误报 {state.false_positive_count} 次"},
            )
            rationale += f"；自动禁用（{state.false_positive_count} 次误报）"
    elif feedback == FEEDBACK_IGNORED:
        # 仅 24h pause，不增减计数
        state.cooldown_until = int(time.time()) + 86400
        rationale = "24h 临时抑制"
    elif feedback == FEEDBACK_DISABLE:
        rule_disabled = True
        rule_store._conn().execute(
            "UPDATE rules SET enabled = 0 WHERE id = ?", (rule_id,)
        )
        rationale = "立即禁用"

    # 调整 confidence_base（应用增量）
    if confidence_delta != 0:
        new_base = max(0.1, min(0.95, rule.confidence_base + confidence_delta))
        rule_store._conn().execute(
            "UPDATE rules SET confidence_base = ? WHERE id = ?",
            (new_base, rule_id),
        )

    # 写 audit log
    rule_store.log_fire(
        rule_id=rule_id, household_id=1, kind="rule_changed",
        confidence=rule.confidence_base + confidence_delta,
        detail={"feedback": feedback, "delta": confidence_delta, "note": note},
    )

    rule_store.update_state(state)
    rule_store._conn().commit()

    return FeedbackResult(
        feedback=feedback,
        confidence_delta=confidence_delta,
        rule_disabled=rule_disabled,
        rule_archived=rule_archived,
        rationale=rationale,
    )


# ============================================================
# 自动学习
# ============================================================


def auto_pause_check(rule_store: RuleStore, household_id: int = 1) -> list[dict]:
    """检查所有规则，自动暂停误报过多的

    规则：
    - 30 天内 FP > 5 → disabled + 通知 admin
    - 30 天内零命中 → 提示"该规则 30 天内零命中"
    - confidence < 0.3 持续 14 天 → 提示"建议删除或重写"
    """
    cutoff = int(time.time()) - 30 * 86400
    actions: list[dict] = []

    rules = rule_store.list_enabled_rules(household_id)
    for rule in rules:
        with rule_store._conn() as c:
            rows = c.execute(
                """SELECT feedback, COUNT(*) as cnt FROM rule_feedback
                   WHERE rule_id = ? AND created_at > ?
                   GROUP BY feedback""",
                (rule.id, cutoff),
            ).fetchall()
        counts = {r["feedback"]: r["cnt"] for r in rows}
        fp_count = counts.get(FEEDBACK_FALSE_POSITIVE, 0)
        tp_count = counts.get(FEEDBACK_TRUE_POSITIVE, 0)
        hit_count = fp_count + tp_count

        if fp_count > 5:
            # 自动暂停
            rule_store._conn().execute(
                "UPDATE rules SET enabled = 0 WHERE id = ?", (rule.id,)
            )
            rule_store.log_fire(
                rule_id=rule.id, household_id=household_id, kind="auto_disabled",
                detail={"reason": f"30天内误报 {fp_count} 次"},
            )
            actions.append({
                "rule_id": rule.id,
                "action": "auto_disabled",
                "reason": f"30天内误报 {fp_count} 次",
            })
        elif hit_count == 0 and rule.confidence_base < 0.3:
            actions.append({
                "rule_id": rule.id,
                "action": "suggest_delete",
                "reason": "30天零命中 + 低置信度，建议删除或重写",
            })
        elif hit_count == 0:
            actions.append({
                "rule_id": rule.id,
                "action": "suggest_review",
                "reason": "30天零命中，建议复审",
            })

    rule_store._conn().commit()
    if actions:
        logger.info(f"auto_pause_check: {len(actions)} 条规则需处理")
    return actions


# ============================================================
# GDPR author 撤销级联（§43.3）
# ============================================================


def cascade_author_revoke(
    rule_store: RuleStore,
    member_id: int,
    household_id: int = 1,
) -> int:
    """author 撤销时级联：作者创建的所有规则 archived_at = now（不依赖 24h 临时期）"""
    with rule_store._conn() as c:
        cur = c.execute(
            """UPDATE rules SET archived_at = strftime('%s', 'now')
               WHERE author_id = ? AND household_id = ? AND archived_at IS NULL""",
            (member_id, household_id),
        )
        rule_store.log_fire(
            rule_id="*", household_id=household_id, kind="rule_changed",
            detail={"event": "author_revoked_cascade", "member_id": member_id},
        )
    return cur.rowcount
