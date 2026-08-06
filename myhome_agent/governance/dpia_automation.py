"""DPIA 自动化（v1.0.1）

每次发布 / 上架 / 重大变更时自动跑 DPIA 检查：
1. 数据流图自动生成（matplotlib）
2. 风险评分
3. 治理审批自动通知
4. DPO 必审触发（safety 类）
5. 报告归档到 dpia_reports/

用法：
    python -m myhome_agent.governance.dpia_automation \
        --module "vision" \
        --change "新增 YOLOv8n 推理" \
        --version "v1.0.1"
"""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================
# DPIA 数据结构
# ============================================================


@dataclass
class DPIAReport:
    """v1.0.1 DPIA 报告"""

    module: str  # 'vision' / 'rules' / 'channels' / ...
    change: str  # 本次变更描述
    version: str  # 版本号
    data_flows: list = field(default_factory=list)
    issues: list = field(default_factory=list)
    risk_score: float = 0.0
    passed: bool = True
    requires_dpo: bool = False
    generated_at: int = field(default_factory=lambda: int(time.time()))
    recommendations: list = field(default_factory=list)


# ============================================================
# DPIA 检查引擎
# ============================================================


class DPIAEngine:
    """v1.0.1 DPIA 自动化引擎"""

    def __init__(self, store: Any | None = None):
        self.store = store

    def assess_module(self, module: str, change: str, version: str = "v1.0.1") -> DPIAReport:
        """对单个模块跑 DPIA"""
        report = DPIAReport(module=module, change=change, version=version)

        # 1. 数据流识别
        flows = self._identify_data_flows(module)
        report.data_flows = flows

        # 2. 5 维评分
        score, issues = self._score_dimensions(module, flows)
        report.risk_score = score
        report.issues = issues
        report.passed = score < 0.5

        # 3. DPO 必审判定
        report.requires_dpo = self._requires_dpo(module, score, issues)

        # 4. 建议
        report.recommendations = self._recommend(report)

        # 5. 持久化
        if self.store:
            self._save_report(report)

        # 6. DPO 通知
        if report.requires_dpo:
            self._notify_dpo(report)

        return report

    def _identify_data_flows(self, module: str) -> list[dict]:
        """v1.0.1 简化：每个模块的固定数据流描述"""
        FLOWS = {
            "vision": [
                {"name": "camera_to_pipeline", "src": "摄像头", "dst": "视觉管线", "encryption": "LAN"},
                {"name": "pipeline_to_events", "src": "视觉管线", "dst": "vision_events 表", "encryption": "Fernet"},
                {"name": "snapshot_to_storage", "src": "视觉管线", "dst": "data/snapshots/", "encryption": "Fernet"},
                {"name": "events_to_rule_engine", "src": "vision_events", "dst": "rules engine", "encryption": "SQLite"},
            ],
            "rules": [
                {"name": "yaml_to_db", "src": "用户", "dst": "rules 表", "encryption": "SQLite"},
                {"name": "audit_to_db", "src": "规则引擎", "dst": "rule_audit_log", "encryption": "SQLite"},
                {"name": "fallback_to_llm", "src": "规则引擎", "dst": "DeepSeek", "encryption": "redactor + TLS"},
            ],
            "channels": [
                {"name": "tg_to_server", "src": "Telegram", "dst": "server", "encryption": "TLS"},
                {"name": "server_to_tg", "src": "server", "dst": "Telegram", "encryption": "TLS"},
            ],
            "auth": [
                {"name": "user_to_2fa", "src": "用户", "dst": "member_2fa", "encryption": "Fernet"},
                {"name": "webauthn_register", "src": "浏览器", "dst": "member_webauthn", "encryption": "FIDO2"},
            ],
            "governance": [
                {"name": "decision_to_db", "src": "AutonomyEngine", "dst": "governance_decisions", "encryption": "SQLite"},
                {"name": "dpia_to_dpo", "src": "DPIA Engine", "dst": "DPO", "encryption": "Email"},
            ],
            "marketplace": [
                {"name": "template_upload", "src": "作者", "dst": "marketplace", "encryption": "TLS + DPIA"},
                {"name": "template_download", "src": "marketplace", "dst": "家庭", "encryption": "TLS"},
            ],
        }
        return FLOWS.get(module, [])

    def _score_dimensions(self, module: str, flows: list[dict]) -> tuple[float, list[str]]:
        """5 维评分"""
        score = 0.0
        issues = []

        # 1. 数据量
        if module in ("vision", "marketplace"):
            score += 0.15
            issues.append(f"{module}: 高数据量（视频/模板）")

        # 2. 跨境
        if any("云端" in str(flow) or "LLM" in str(flow) for flow in flows):
            score += 0.2
            issues.append(f"{module}: 含跨境传输（云端）")

        # 3. 第三方
        if module in ("channels", "marketplace"):
            score += 0.15
            issues.append(f"{module}: 涉及第三方（Telegram/作者）")

        # 4. 个人画像
        if module in ("auth", "governance"):
            score += 0.1
            issues.append(f"{module}: 含成员画像数据")

        # 5. safety 影响
        if module == "rules" and any("fallback" in str(flow) for flow in flows):
            score += 0.15
            issues.append(f"rules: LLM 兜底含 safety 影响")

        return min(1.0, score), issues

    def _requires_dpo(self, module: str, score: float, issues: list[str]) -> bool:
        """判定 DPO 必审

        规则：
        - safety 模块（rules/vision）→ 必审
        - 跨境（云端）→ 必审
        - 风险分 ≥ 0.6 → 必审
        """
        if module in ("rules", "vision"):
            return True
        if "跨境" in str(issues):
            return True
        if score >= 0.6:
            return True
        return False

    def _recommend(self, report: DPIAReport) -> list[str]:
        """v1.0.1 风险对应建议"""
        recs = []
        if report.risk_score >= 0.5:
            recs.append("需要 §50 治理 review")
        if report.requires_dpo:
            recs.append("需要 DPO 双签")
        if "跨境" in str(report.issues):
            recs.append("需要 SCC 协议 + 数据驻留声明")
        if "个人画像" in str(report.issues):
            recs.append("确认 consent_flags 字段 + 用户可见开关")
        if not recs:
            recs.append("无需额外动作")
        return recs

    def _save_report(self, report: DPIAReport):
        """v1.0.1 持久化到 dpia_reports/"""
        try:
            import os
            report_dir = "data/dpia_reports"
            os.makedirs(report_dir, exist_ok=True)
            path = f"{report_dir}/{report.module}_{report.version}_{report.generated_at}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(report.__dict__, f, ensure_ascii=False, indent=2)
            logger.info(f"DPIA 报告存档: {path}")
        except Exception as e:
            logger.error(f"DPIA 存档失败: {e}")

    def _notify_dpo(self, report: DPIAReport):
        """v1.0.1 DPO 通知（邮件 / 控制台）"""
        # 真实实现：调邮件 API / SendGrid / DPO 仪表盘 webhook
        logger.warning(
            f"[DPO 通知] 模块 {report.module} 风险 {report.risk_score:.2f} "
            f"需要 DPO 审（{report.change}）"
        )

    def generate_data_flow_diagram(self, report: DPIAReport, output_path: str | None = None) -> str:
        """v1.0.1 生成数据流图（matplotlib）

        可选依赖 matplotlib + graphviz。
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches
        except ImportError:
            logger.warning("matplotlib 未装；v1.0.1 跳过图生成")
            return ""

        if not report.data_flows:
            return ""

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, len(report.data_flows) + 1)
        ax.axis("off")
        ax.set_title(f"DPIA 数据流图 - {report.module} ({report.version})")

        for i, flow in enumerate(report.data_flows):
            y = len(report.data_flows) - i
            # 源节点
            ax.add_patch(patches.FancyBboxPatch(
                (0.5, y - 0.3), 1.5, 0.6,
                boxstyle="round,pad=0.1", facecolor="#4CAF50", alpha=0.7
            ))
            ax.text(1.25, y, flow["src"], ha="center", va="center", fontsize=9)

            # 箭头
            ax.annotate("", xy=(4, y), xytext=(2, y),
                       arrowprops=dict(arrowstyle="->", color="gray", lw=1.5))

            # 目标节点
            ax.add_patch(patches.FancyBboxPatch(
                (4, y - 0.3), 1.5, 0.6,
                boxstyle="round,pad=0.1", facecolor="#FF9800", alpha=0.7
            ))
            ax.text(4.75, y, flow["dst"], ha="center", va="center", fontsize=9)

            # 加密标签
            ax.text(3, y + 0.4, flow.get("encryption", ""), ha="center", fontsize=7, color="blue")

        out_path = output_path or f"data/dpia_reports/{report.module}_{report.version}_diagram.png"
        try:
            plt.savefig(out_path, dpi=100, bbox_inches="tight")
            plt.close()
            logger.info(f"数据流图保存: {out_path}")
            return out_path
        except Exception as e:
            logger.error(f"保存图失败: {e}")
            return ""


# ============================================================
# CLI 入口
# ============================================================


def main():
    """v1.0.1 DPIA 自动化 CLI"""
    import argparse
    parser = argparse.ArgumentParser(description="DPIA 自动化")
    parser.add_argument("--module", required=True, help="模块名")
    parser.add_argument("--change", required=True, help="变更描述")
    parser.add_argument("--version", default="v1.0.1")
    parser.add_argument("--diagram", action="store_true", help="生成数据流图")
    args = parser.parse_args()

    engine = DPIAEngine()
    report = engine.assess_module(args.module, args.change, args.version)

    print(f"=== DPIA 评估 {args.module} {args.version} ===")
    print(f"风险分: {report.risk_score:.2f}")
    print(f"通过: {'✅' if report.passed else '❌'}")
    print(f"DPO 必审: {'🔴 是' if report.requires_dpo else '🟢 否'}")
    print(f"\n数据流 ({len(report.data_flows)} 条):")
    for f in report.data_flows:
        print(f"  {f['src']} → {f['dst']} ({f['encryption']})")
    print(f"\n问题 ({len(report.issues)} 项):")
    for issue in report.issues:
        print(f"  ⚠️ {issue}")
    print(f"\n建议:")
    for r in report.recommendations:
        print(f"  → {r}")

    if args.diagram:
        path = engine.generate_data_flow_diagram(report)
        if path:
            print(f"\n数据流图: {path}")


if __name__ == "__main__":
    main()