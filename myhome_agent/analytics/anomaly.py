"""异常检测：硬规则 + 作息基线偏离。

硬规则（config/default.yaml 的 hard_alerts）在采集时即触发；
本模块负责周期性的软异常评估：
- 长时间无活动（对比 first_activity 基线，适合独居老人看护）
- 传感器数据越界（温度过高等，可扩展）
"""
from __future__ import annotations

import ast
import logging
from datetime import datetime, timedelta

from ..memory.store import Store

logger = logging.getLogger(__name__)


# 硬规则条件只允许访问 value/hour 两个变量，且仅限比较/布尔/常量表达式
_ALLOWED_NAMES = frozenset({"value", "hour"})


def _validate_condition(node: ast.AST) -> None:
    if isinstance(node, ast.Expression):
        _validate_condition(node.body)
        return
    if isinstance(node, ast.Constant):
        return
    if isinstance(node, ast.Name):
        if node.id not in _ALLOWED_NAMES:
            raise ValueError(f"disallowed name: {node.id}")
        return
    if isinstance(node, ast.Compare):
        _validate_condition(node.left)
        for comparator in node.comparators:
            _validate_condition(comparator)
        for op in node.ops:
            if not isinstance(op, (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn)):
                raise ValueError(f"disallowed operator: {type(op).__name__}")
        return
    if isinstance(node, ast.BoolOp):
        for value in node.values:
            _validate_condition(value)
        return
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.Not, ast.USub)):
        _validate_condition(node.operand)
        return
    raise ValueError(f"disallowed expression: {type(node).__name__}")


def safe_eval_condition(condition: str, value, hour: int) -> bool:
    """在受限 AST 上求值硬规则条件，失败时返回 False。"""
    try:
        tree = ast.parse(condition, mode="eval")
        _validate_condition(tree)
        return bool(
            eval(compile(tree, "<hard_rule>", "eval"), {"__builtins__": {}}, {"value": value, "hour": hour})
        )
    except Exception:
        return False


def check_hard_rules(store: Store, rules: list[dict], device_id: str,
                     metric: str, value) -> None:
    """采集时逐条对照硬规则，命中即写告警。"""
    hour = datetime.now().hour
    for rule in rules:
        if rule.get("metric") != metric:
            continue
        hit = safe_eval_condition(rule.get("condition", ""), value, hour)
        if not hit:
            continue
        if hit:
            dev = store.get_device(device_id)
            name = dev["name"] if dev else device_id
            store.add_alert(rule.get("level", "warning"),
                            f"{rule.get('message', metric)}（{name}）",
                            detail=f"metric={metric} value={value}", source="hard_rule")
            logger.warning("硬规则告警: %s %s=%s", name, metric, value)


def check_inactivity(store: Store, grace_minutes: int = 180) -> None:
    """今天应该有活动了却一直没有活动 → 告警（看护场景）。"""
    routines = {r["kind"]: r for r in store.get_routines()
                if r["kind"] in ("first_activity",) and r["weekday"] is None}
    baseline = routines.get("first_activity")
    if not baseline or baseline["confidence"] < 0.2:
        return

    now = datetime.now()
    expected = now.replace(hour=int(baseline["value"]), minute=0, second=0, microsecond=0)
    deadline = expected + timedelta(minutes=grace_minutes)
    if now < deadline:
        return

    today = now.strftime("%Y-%m-%d")
    recent = store.query_events(since_hours=now.hour + 1, limit=5)
    today_activity = [e for e in recent
                      if e["ts"].startswith(today)
                      and e["kind"] in ("motion", "door_open", "control", "button")]
    if today_activity:
        return

    # 避免同一天重复告警
    for a in store.list_alerts(status="open"):
        if a["title"].startswith("今日无活动") and a["ts"].startswith(today):
            return

    store.add_alert(
        "warning",
        "今日无活动异常",
        detail=(f"家庭典型起床时间约 {baseline['value']:.0f} 点，"
                f"现已 {now.strftime('%H:%M')} 仍未检测到任何活动，请确认家人是否安好。"),
        source="baseline",
    )
    logger.warning("软异常: 今日无活动")


def run_all(store: Store, config: dict) -> None:
    check_inactivity(store, int(config.get("analytics", {}).get("inactivity_grace_minutes", 180)))
