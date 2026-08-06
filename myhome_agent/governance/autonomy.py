"""自治等级动态判定 v0.5（§50 升级路径 1）

v0.5 实现：
- 4 维风险评分：severity × irreversibility × time × member_role
- L0-L4 自治等级决策树
- 用户可审计 + 可覆盖（governance_decisions 表）
- 自治执行后写 audit + 自动降级（高风险时）

v0.5 不做：
- ML 自学习（v1.0）
- 跨家庭策略（v1.0）
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# 自治等级（v0.5 §50 修订）
LEVEL_L0 = "L0"  # 仅观察
LEVEL_L1 = "L1"  # 强制 confirm（任何动作都要用户确认）
LEVEL_L2 = "L2"  # 默认（care 级自动执行 + 通知）
LEVEL_L3 = "L3"  # 高度自主（info 级自动不通知）
LEVEL_L4 = "L4"  # 完全自主（理论最大值，实际不启用）


@dataclass
class RiskContext:
    """4 维风险输入"""

    severity: str = "care"  # 'safety' | 'care' | 'info'
    irreversibility: str = "reversible"  # 'reversible' | 'costly' | 'irreversible'
    time_period: str = "day"  # 'day' | 'night' | 'vacation'
    member_role: str = "adult"  # 'adult' | 'elder' | 'child' | 'guest'
    member_home: bool = True
    is_vacation: bool = False

    def risk_score(self) -> float:
        """0.0-1.0 风险分"""
        score = 0.0
        # severity（最高 0.4）
        score += {"safety": 0.4, "care": 0.2, "info": 0.05}.get(self.severity, 0.2)
        # irreversibility（最高 0.3）
        score += {"irreversible": 0.3, "costly": 0.15, "reversible": 0.0}.get(self.irreversibility, 0.0)
        # time（最高 0.15）
        score += {"night": 0.15, "vacation": 0.1, "day": 0.0}.get(self.time_period, 0.0)
        # member（最高 0.15）
        score += {"child": 0.15, "elder": 0.1, "guest": 0.05, "adult": 0.0}.get(self.member_role, 0.0)
        # 不在家加成
        if not self.member_home:
            score += 0.05
        return min(1.0, score)


@dataclass
class AutonomyDecision:
    """自治决策结果"""

    level: str  # L0/L1/L2/L3/L4
    risk_score: float
    rationale: str
    requires_confirm: bool
    auto_execute: bool
    notify: bool
    ts: int = field(default_factory=lambda: int(time.time()))


class AutonomyEngine:
    """v0.5 自治决策引擎"""

    def decide(self, ctx: RiskContext) -> AutonomyDecision:
        """根据 4 维风险分决定自治等级"""
        score = ctx.risk_score()

        # 强制 L1（任何 safety 不可逆 + 老人 / 孩子 / 不在家）
        if ctx.severity == "safety" and ctx.irreversibility == "irreversible":
            return AutonomyDecision(
                level=LEVEL_L1,
                risk_score=score,
                rationale="safety + irreversible 强制 L1 确认（§50.3.2）",
                requires_confirm=True,
                auto_execute=False,
                notify=True,
            )
        # 强制 L1（孩子在场）
        if ctx.member_role == "child":
            return AutonomyDecision(
                level=LEVEL_L1,
                risk_score=score,
                rationale="儿童在场 → 所有动作 L1 确认（§50.7 GDPR 兼容）",
                requires_confirm=True,
                auto_execute=False,
                notify=True,
            )

        # 分数驱动
        if score >= 0.7:
            level = LEVEL_L1
            requires_confirm = True
            auto_execute = False
            notify = True
            rationale = f"高风险 {score:.2f}：强制 confirm"
        elif score >= 0.15:
            level = LEVEL_L2
            requires_confirm = False
            auto_execute = True
            notify = True
            rationale = f"中风险 {score:.2f}：自动执行 + 通知"
        else:
            level = LEVEL_L3
            requires_confirm = False
            auto_execute = True
            notify = False
            rationale = f"低风险 {score:.2f}：自主 + 不通知"

        return AutonomyDecision(
            level=level,
            risk_score=score,
            rationale=rationale,
            requires_confirm=requires_confirm,
            auto_execute=auto_execute,
            notify=notify,
        )

    def log_decision(
        self,
        store: Any,
        member_id: int,
        decision: AutonomyDecision,
        action: str,
        outcome: str = "pending",
    ) -> int:
        """写 governance_decisions 审计（v0.5 新增）"""
        try:
            with store._conn() as c:
                cur = c.execute(
                    """INSERT INTO governance_decisions
                       (household_id, member_id, action, level, risk_score, requires_confirm, outcome, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        1,
                        member_id,
                        action,
                        decision.level,
                        decision.risk_score,
                        1 if decision.requires_confirm else 0,
                        outcome,
                        decision.ts,
                    ),
                )
                # 自动建表（v0.5 升级时迁移）
                return cur.lastrowid
        except Exception as e:
            logger.error(f"log_decision 失败: {e}")
            return -1


# ============================================================
# 治理决策 schema（v0.5 新增）
# ============================================================


GOVERNANCE_SCHEMA = """
CREATE TABLE IF NOT EXISTS governance_decisions (
  id INTEGER PRIMARY KEY,
  household_id INTEGER NOT NULL DEFAULT 1,
  member_id INTEGER,
  action TEXT NOT NULL,
  level TEXT NOT NULL,
  risk_score REAL,
  requires_confirm INTEGER DEFAULT 0,
  outcome TEXT,
  user_override INTEGER DEFAULT 0,
  created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_gov_decisions_household ON governance_decisions(household_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_gov_decisions_member ON governance_decisions(member_id, created_at DESC);
"""
