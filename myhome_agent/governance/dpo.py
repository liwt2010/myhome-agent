"""DPO 任命 + 仪表盘（v1.0.1）

商业化必做：任命 DPO + 公开联系方式 + 季度审计 + 应急流程。
开源版家庭 DPO：admin 兼任 / 家庭成员中独立第三方。

用法：
    from myhome_agent.governance.dpo import DPORegistry, DPORole
    dpo = DPORegistry(store)
    dpo.appoint(member_id=99, name="王律师", contact="dpo@myhome.local",
                independent=True, certified=True)
    dpo.quarterly_audit()
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DPORole:
    """DPO 角色定义"""

    member_id: int
    name: str
    contact: str  # email / phone
    appointed_at: int
    independent: bool  # 独立性（不受业务 KPI 影响）
    certified: bool  # IAPP CIPP/E 或等同
    certifications: list = field(default_factory=list)  # ['CIPP/E', 'CIPM']
    scope: str = "all"  # 'all' / 'eu' / 'asia' / 'americas'
    active: bool = True
    last_quarterly_audit: int | None = None
    notes: str = ""


class DPORegistry:
    """v1.0.1 DPO 注册表"""

    def __init__(self, store: Any):
        self.store = store

    def _table_ddl(self):
        return """
        CREATE TABLE IF NOT EXISTS dpo_registry (
          id INTEGER PRIMARY KEY,
          member_id INTEGER NOT NULL UNIQUE,
          name TEXT NOT NULL,
          contact TEXT NOT NULL,
          appointed_at INTEGER NOT NULL,
          independent INTEGER NOT NULL DEFAULT 1,
          certified INTEGER NOT NULL DEFAULT 0,
          certifications TEXT,
          scope TEXT DEFAULT 'all',
          active INTEGER DEFAULT 1,
          last_quarterly_audit INTEGER,
          notes TEXT
        );
        CREATE TABLE IF NOT EXISTS dpo_quarterly_audit (
          id INTEGER PRIMARY KEY,
          dpo_id INTEGER NOT NULL,
          audit_at INTEGER NOT NULL,
          period TEXT,             -- '2026-Q3'
          issues_found TEXT,        -- JSON
          resolved TEXT,
          next_audit_due INTEGER
        );
        """

    def _ensure_tables(self):
        """v1.0.1 启动建表"""
        try:
            with self.store._conn() as c:
                c.executescript(self._table_ddl())
        except Exception as e:
            logger.error(f"DPO 建表失败: {e}")

    def appoint(
        self,
        member_id: int,
        name: str,
        contact: str,
        *,
        independent: bool = True,
        certified: bool = False,
        certifications: list | None = None,
        scope: str = "all",
        notes: str = "",
    ) -> DPORole:
        """v1.0.1 任命 DPO"""
        self._ensure_tables()
        role = DPORole(
            member_id=member_id,
            name=name,
            contact=contact,
            appointed_at=int(time.time()),
            independent=independent,
            certified=certified,
            certifications=certifications or [],
            scope=scope,
            active=True,
            notes=notes,
        )
        try:
            with self.store._conn() as c:
                c.execute(
                    """INSERT OR REPLACE INTO dpo_registry
                       (member_id, name, contact, appointed_at, independent, certified, certifications, scope, active, notes)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        role.member_id, role.name, role.contact, role.appointed_at,
                        1 if role.independent else 0, 1 if role.certified else 0,
                        json.dumps(role.certifications), role.scope,
                        1 if role.active else 0, role.notes,
                    ),
                )
            logger.info(f"DPO 已任命: {role.name} <{role.contact}>")
        except Exception as e:
            logger.error(f"任命 DPO 失败: {e}")
        return role

    def get_active_dpo(self, scope: str = "all") -> DPORole | None:
        """取当前活跃 DPO"""
        self._ensure_tables()
        try:
            with self.store._conn() as c:
                row = c.execute(
                    "SELECT * FROM dpo_registry WHERE active = 1 AND (scope = ? OR scope = 'all') LIMIT 1",
                    (scope,),
                ).fetchone()
            if not row:
                return None
            return DPORole(
                member_id=row["member_id"],
                name=row["name"],
                contact=row["contact"],
                appointed_at=row["appointed_at"],
                independent=bool(row["independent"]),
                certified=bool(row["certified"]),
                certifications=json.loads(row["certifications"] or "[]"),
                scope=row["scope"],
                active=bool(row["active"]),
                last_quarterly_audit=row["last_quarterly_audit"],
                notes=row["notes"],
            )
        except Exception:
            return None

    def quarterly_audit(self, period: str | None = None) -> dict:
        """v1.0.1 季度审计（强制触发）"""
        dpo = self.get_active_dpo()
        if not dpo:
            logger.warning("无活跃 DPO，跳过季度审计")
            return {"skipped": "no_dpo"}

        period = period or time.strftime("%Y-Q") + str((int(time.strftime("%m")) - 1) // 3 + 1)

        # 自动检查项
        issues = []

        # 1. 治理决策异常
        try:
            with self.store._conn() as c:
                recent = c.execute(
                    "SELECT COUNT(*) as cnt FROM governance_decisions WHERE created_at > ? AND risk_score > 0.7",
                    (int(time.time()) - 90 * 86400,),
                ).fetchone()
                if recent["cnt"] > 50:
                    issues.append(f"过去 90 天有 {recent['cnt']} 条高风险决策，需复查")
        except Exception:
            pass

        # 2. 规则误报率
        try:
            with self.store._conn() as c:
                fp_rate = c.execute(
                    """SELECT
                       SUM(CASE WHEN feedback='false_positive' THEN 1 ELSE 0 END) * 1.0 / NULLIF(COUNT(*), 0) as fp_rate
                       FROM rule_feedback WHERE created_at > ?""",
                    (int(time.time()) - 90 * 86400,),
                ).fetchone()
                if fp_rate["fp_rate"] and fp_rate["fp_rate"] > 0.3:
                    issues.append(f"误报率 {fp_rate['fp_rate']:.1%} 超阈值 30%")
        except Exception:
            pass

        # 3. DPIA 报告缺失
        try:
            with self.store._conn() as c:
                dpia_count = c.execute(
                    "SELECT COUNT(*) as cnt FROM dpia_reports WHERE generated_at > ?",
                    (int(time.time()) - 365 * 86400,),
                ).fetchone()
                if dpia_count["cnt"] < 4:
                    issues.append(f"过去 1 年只生成 {dpia_count['cnt']} 份 DPIA 报告（建议 ≥ 4）")
        except Exception:
            pass

        # 4. 应急流程演练
        # （需 v1.0.1 演练跟踪）

        # 存档审计记录
        next_due = int(time.time()) + 90 * 86400
        try:
            with self.store._conn() as c:
                c.execute(
                    """INSERT INTO dpo_quarterly_audit
                       (dpo_id, audit_at, period, issues_found, next_audit_due)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        dpo.member_id,
                        int(time.time()),
                        period,
                        json.dumps(issues),
                        next_due,
                    ),
                )
                # 更新 DPO 最后审计时间
                c.execute(
                    "UPDATE dpo_registry SET last_quarterly_audit = ? WHERE member_id = ?",
                    (int(time.time()), dpo.member_id),
                )
        except Exception as e:
            logger.error(f"审计存档失败: {e}")

        # 通知 DPO
        self._notify_dpo(dpo, period, issues)

        return {
            "dpo": dpo.name,
            "period": period,
            "issues_count": len(issues),
            "issues": issues,
            "next_audit_due": next_due,
        }

    def _notify_dpo(self, dpo: DPORole, period: str, issues: list[str]):
        """v1.0.1 DPO 通知（邮件 + 控制台）"""
        logger.info(
            f"[DPO 季度审计] {dpo.name} <{dpo.contact}> "
            f"周期 {period}: {len(issues)} 项问题"
        )
        # 真实实现：smtplib / SendGrid / Slack webhook

    def get_dashboard_data(self) -> dict:
        """v1.0.1 DPO 仪表盘数据"""
        dpo = self.get_active_dpo()
        if not dpo:
            return {"has_dpo": False}

        stats = {
            "has_dpo": True,
            "dpo_name": dpo.name,
            "dpo_contact": dpo.contact,
            "appointed_at": dpo.appointed_at,
            "independent": dpo.independent,
            "certified": dpo.certified,
            "certifications": dpo.certifications,
            "last_audit": dpo.last_quarterly_audit,
            "next_audit_due": (dpo.last_quarterly_audit or int(time.time())) + 90 * 86400,
            "stats": {},
        }

        # 实时统计
        try:
            with self.store._conn() as c:
                stats["stats"]["decisions_30d"] = c.execute(
                    "SELECT COUNT(*) as cnt FROM governance_decisions WHERE created_at > ?",
                    (int(time.time()) - 30 * 86400,),
                ).fetchone()["cnt"]
                stats["stats"]["high_risk_30d"] = c.execute(
                    "SELECT COUNT(*) as cnt FROM governance_decisions WHERE created_at > ? AND risk_score > 0.7",
                    (int(time.time()) - 30 * 86400,),
                ).fetchone()["cnt"]
                stats["stats"]["dpia_reports_ytd"] = c.execute(
                    "SELECT COUNT(*) as cnt FROM dpia_reports WHERE generated_at > ?",
                    (int(time.time()) - 365 * 86400,),
                ).fetchone()["cnt"]
                stats["stats"]["fp_rate_30d"] = c.execute(
                    """SELECT
                       CAST(SUM(CASE WHEN feedback='false_positive' THEN 1 ELSE 0 END) AS REAL) /
                       NULLIF(COUNT(*), 0) as rate
                       FROM rule_feedback WHERE created_at > ?""",
                    (int(time.time()) - 30 * 86400,),
                ).fetchone()["rate"] or 0.0
        except Exception as e:
            logger.error(f"DPO 统计失败: {e}")

        return stats


# ============================================================
# DPO 应急响应
# ============================================================


class DPOIncidentResponse:
    """v1.0.1 DPO 应急响应流程

    触发场景：数据泄露 / GDPR 违规 / 用户投诉
    """

    INCIDENT_LEVELS = {
        "low": 72,        # 通知 72h 内
        "medium": 48,      # 48h
        "high": 24,        # 24h
        "critical": 1,     # 1h
    }

    def __init__(self, dpo_registry: DPORegistry):
        self.dpo = dpo_registry

    def trigger(
        self,
        incident_type: str,
        description: str,
        affected_households: list[int],
        severity: str = "medium",
    ) -> dict:
        """触发应急响应"""
        deadline_hours = self.INCIDENT_LEVELS.get(severity, 48)
        incident_id = f"INC-{int(time.time())}"

        dpo = self.dpo.get_active_dpo()
        if not dpo:
            return {"error": "无 DPO"}

        # 记录事件
        incident = {
            "id": incident_id,
            "type": incident_type,
            "description": description,
            "affected_households": affected_households,
            "severity": severity,
            "deadline_hours": deadline_hours,
            "created_at": int(time.time()),
            "dpo_notified_at": int(time.time()),
            "dpo_contact": dpo.contact,
            "status": "investigating",
        }

        # 通知 DPO
        logger.critical(
            f"[DPO 应急] {incident_id} type={incident_type} severity={severity} "
            f"deadline={deadline_hours}h DPO={dpo.contact}"
        )

        # GDPR Article 33：72h 内通知监管机构
        if severity in ("high", "critical"):
            logger.warning(
                f"[GDPR] Article 33: 必须在 72h 内通知监管机构（CNIL等）"
            )

        return incident