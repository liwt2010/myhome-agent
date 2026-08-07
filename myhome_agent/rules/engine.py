"""规则引擎 v0.2（v2.19 §53 跨信号推理 + v0.2 §53.4 完整置信度）

v0.2 范围：
- DSL 解析（YAML → Rule）
- 谓词白名单 25 个
- 窗口聚合（1min/5min/60min）
- 周期扫描（10s）
- 状态机（cold_start → armed → firing → cooldown）
- 完整置信度校准（4 因子）
- 误报闭环（4 选项 + 自动暂停）
- 5 条 P0 + 3 条视觉 P1 种子（v0.2 补）

v0.2 不做：
- LLM 兜底推理（v0.3）
- 自动学习（v0.3）
"""
from __future__ import annotations

import json
import logging
import re
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator

import yaml

from .confidence import CalibratedConfidence
from .fallback import FALLBACK_CONFIDENCE_THRESHOLD, FallbackReasoner

logger = logging.getLogger(__name__)


# ============================================================
# 谓词白名单（v2.19 §53.2.2，25 个）
# ============================================================

PREDICATE_REGISTRY: dict[str, str] = {
    # 数值类（6）
    "eq": "field == value",
    "ne": "field != value",
    "gt": "field > value",
    "gte": "field >= value",
    "lt": "field < value",
    "lte": "field <= value",
    # 时序类（3）
    "away_minutes": "duration > N (minutes)",
    "since_minutes": "since_event > N (minutes)",
    "duration_minutes": "in_state > N (minutes)",
    # 时窗类（3）
    "time.in_window": "time in [start, end]",
    "weekday.in": "weekday in [day, ...]",
    "date.in": "date in [from, to]",
    # 成员类（3）
    "member.is_alone_at_home": "true/false",
    "member.role": "== 'elder'/'adult'/...",
    "member.count_at_home": ">N",
    # 传感器类（3）
    "sensor.fresh": "data age <= N seconds",
    "sensor.value": "== 'on'/'off'/...",
    "sensor.changed": "changed within window",
    # 家庭上下文（3）
    "household.in_mode": "== 'day'/'night'/'away'",
    "weather.condition": "== 'rain'/'sun'/...",
    "calendar.has_event": "== 'school_day'/...",
    # 组合子（3）
    "all": "all sub-predicates match",
    "any": "any sub-predicate matches",
    "none": "no sub-predicate matches",
}


# ============================================================
# 规则对象
# ============================================================


@dataclass
class Rule:
    id: str
    description: str
    yaml_body: dict
    confidence_base: float = 0.7
    cooldown: int = 3600
    window: str = "1min"
    severity: str = "care"
    category: str | None = None
    author_type: str = "system"
    enabled: bool = True
    household_id: int = 1


@dataclass
class RuleState:
    rule_id: str
    state: str = "cold_start"  # disabled|cold_start|armed|firing|cooldown
    last_fire_at: int | None = None
    last_eval_at: int | None = None
    cooldown_until: int | None = None
    true_positive_count: int = 0
    false_positive_count: int = 0


# ============================================================
# DSL 解析器
# ============================================================


class DSLError(Exception):
    pass


def parse_rule_yaml(yaml_text: str) -> Rule:
    """解析单条规则 YAML → Rule 对象"""
    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        raise DSLError(f"YAML 解析失败: {e}")

    if not isinstance(data, dict):
        raise DSLError("规则根必须是 dict")

    # 必填字段
    for required in ("id", "description", "when", "then"):
        if required not in data:
            raise DSLError(f"缺少必填字段: {required}")

    rule_id = data["id"]
    if not isinstance(rule_id, str) or not rule_id.replace("-", "").replace("_", "").isalnum():
        raise DSLError(f"id 必须是 kebab-case: {rule_id}")

    # 校验嵌套深度
    _validate_nesting(data["when"], depth=0, max_depth=4)
    _validate_predicates(data["when"])

    return Rule(
        id=rule_id,
        description=data["description"],
        yaml_body=data,
        confidence_base=float(data.get("confidence_base", 0.7)),
        cooldown=int(data.get("cooldown", 3600)),
        window=data.get("window", "1min"),
        severity=data.get("severity", "care"),
        category=data.get("category"),
        author_type=data.get("author_type", data.get("meta", {}).get("author_type", "system")),
        enabled=bool(data.get("enabled", True)),
    )


def _validate_nesting(node: Any, depth: int, max_depth: int) -> None:
    """校验嵌套深度"""
    if depth > max_depth:
        raise DSLError(f"规则嵌套超过 {max_depth} 层")
    if isinstance(node, dict):
        for v in node.values():
            _validate_nesting(v, depth + 1, max_depth)
    elif isinstance(node, list):
        for v in node:
            _validate_nesting(v, depth + 1, max_depth)


def _validate_predicates(node: Any) -> None:
    """校验谓词白名单（粗校验：检查 all/any/none 与字段名前缀）"""
    if isinstance(node, dict):
        for k, v in node.items():
            # 顶层 key 是 all/any/none 时不强校验（这是组合子）
            if k in ("all", "any", "none"):
                _validate_predicates(v)
            elif "." in k or k in PREDICATE_REGISTRY:
                # 字段引用（sensor.xxx / member.xxx 等）
                _validate_predicates(v)
            elif isinstance(v, (int, float, str, bool, type(None))):
                # 叶子值（如阈值）—允许
                pass
            else:
                # 可能是子结构
                _validate_predicates(v)
    elif isinstance(node, list):
        for v in node:
            _validate_predicates(v)


# ============================================================
# 窗口聚合（v0.1 简化版：内存版，v0.2 接 readings 表）
# ============================================================


class WindowStore:
    """v0.1 窗口聚合（内存 mock）

    v0.2 替换：从 readings 表实时聚合
    """

    def __init__(self):
        self._data: dict[str, list[tuple[int, Any]]] = {}

    def record(self, sensor: str, value: Any, ts: int | None = None) -> None:
        """记录一条数据点"""
        ts = ts or int(time.time())
        self._data.setdefault(sensor, []).append((ts, value))

    def get(self, sensor: str, since_seconds: int = 60) -> list[tuple[int, Any]]:
        """取最近 N 秒数据"""
        cutoff = int(time.time()) - since_seconds
        return [(t, v) for t, v in self._data.get(sensor, []) if t >= cutoff]

    def latest(self, sensor: str) -> tuple[int, Any] | None:
        """取最近一条"""
        items = self._data.get(sensor, [])
        return items[-1] if items else None

    def value(self, sensor: str, default: Any = None) -> Any:
        """取当前值（v0.1 mock 用）"""
        latest = self.latest(sensor)
        return latest[1] if latest else default


# ============================================================
# 谓词求值器（v0.1 简化版：仅支持核心谓词）
# ============================================================


def evaluate_predicate(pred: Any, ctx: "EvalContext") -> bool:
    """求值一条谓词

    v0.1 支持的最小集（13 个核心谓词）：
    - 数值: gt, lt, eq, gte, lte
    - 时序: away_minutes, duration_minutes
    - 时窗: time.in_window
    - 成员: member.is_alone_at_home, member.role
    - 传感器: sensor.fresh, sensor.value
    - 组合: all, any
    """
    if isinstance(pred, bool):
        return pred
    if isinstance(pred, (int, float)):
        return bool(pred)
    if isinstance(pred, str):
        return _eval_string_predicate(pred, ctx)
    if not isinstance(pred, dict):
        return False

    # 组合子
    if "all" in pred:
        return all(evaluate_predicate(p, ctx) for p in pred["all"])
    if "any" in pred:
        return any(evaluate_predicate(p, ctx) for p in pred["any"])
    if "none" in pred:
        return not any(evaluate_predicate(p, ctx) for p in pred["none"])

    # 谓词：形如 {field: value, op?: 'gt'/'eq'/'in_window'/...}
    for key, value in pred.items():
        # 数值比较：field > value 形式 → {field: value, op: 'gt'}
        # v0.1 简化：直接 key=value 比较 + 几种扩展
        if key == "time.in_window":
            return _eval_time_window(value, ctx)
        if key == "weekday.in":
            return ctx.now_weekday in value
        if key == "date.in":
            return value[0] <= ctx.now_date <= value[1]
        if key == "member.is_alone_at_home":
            return ctx.member_alone == value
        if key == "member.role":
            return ctx.member_role == value
        if key == "member.count_at_home":
            return ctx.member_count > value
        if key == "sensor.fresh":
            return _eval_sensor_fresh(key, value, ctx)
        if key == "sensor.value":
            return _eval_sensor_value(value, ctx)
        if key == "household.in_mode":
            return ctx.household_mode == value
        if key == "weather.condition":
            return ctx.weather == value
        if key == "calendar.has_event":
            return value in ctx.calendar_events
        # 数值比较（默认 eq）
        if key.endswith(".gt") or key == "gt":
            return _eval_field_gt(pred, value, ctx)
        if key.endswith(".lt") or key == "lt":
            return _eval_field_lt(pred, value, ctx)
        # 字段直接等于值
        if isinstance(value, (int, float, str, bool)):
            return ctx.field_value(key) == value

    return False


def _eval_time_window(value: list, ctx: "EvalContext") -> bool:
    """time.in_window: ['22:00', '06:00']"""
    if not isinstance(value, list) or len(value) != 2:
        return False
    start, end = value
    now = ctx.now_time  # "HH:MM"
    if start <= end:
        return start <= now <= end
    # 跨夜（如 22:00-06:00）
    return now >= start or now <= end


def _eval_sensor_fresh(key: str, value: Any, ctx: "EvalContext") -> bool:
    """sensor.fresh: <=60s → True if data age <= 60s"""
    age = ctx.field_value("sensor.age")
    if age is None:
        return True
    try:
        return float(age) <= float(value)
    except (TypeError, ValueError):
        return False


_STRING_PREDICATE_RE = re.compile(r"^\s*([A-Za-z0-9_.]+)\s*(==|!=|>=|<=|>|<)\s*(.+?)\s*$")


def _eval_string_predicate(expr: str, ctx: "EvalContext") -> bool:
    """支持 YAML 叶子写法：field > 30 / sensor.value == 'on'"""
    m = _STRING_PREDICATE_RE.match(expr)
    if not m:
        return False
    field, op, raw = m.group(1), m.group(2), m.group(3)
    actual = ctx.field_value(field)
    if actual is None:
        return False
    try:
        target: Any = float(raw)
    except ValueError:
        target = raw.strip().strip("'\"")

    if op == "==":
        return actual == target
    if op == "!=":
        return actual != target
    try:
        actual_num = float(actual)
    except (TypeError, ValueError):
        return False
    if not isinstance(target, (int, float)):
        return False
    if op == ">":
        return actual_num > target
    if op == ">=":
        return actual_num >= target
    if op == "<":
        return actual_num < target
    if op == "<=":
        return actual_num <= target
    return False


def _eval_sensor_value(value: Any, ctx: "EvalContext") -> bool:
    """sensor.value: 'on'/'off'/..."""
    return ctx.field_value("__sensor__") == value


def _eval_field_gt(pred: dict, value: Any, ctx: "EvalContext") -> bool:
    """形如 {away_minutes.gt: 30}"""
    for k, v in pred.items():
        if isinstance(v, (int, float)) and (k.endswith(".gt") or k == "gt"):
            actual = ctx.field_value(k.replace(".gt", "").replace("gt", ""))
            return actual is not None and actual > v
    return False


def _eval_field_lt(pred: dict, value: Any, ctx: "EvalContext") -> bool:
    for k, v in pred.items():
        if isinstance(v, (int, float)) and (k.endswith(".lt") or k == "lt"):
            actual = ctx.field_value(k.replace(".lt", "").replace("lt", ""))
            return actual is not None and actual < v
    return False


@dataclass
class EvalContext:
    """求值上下文"""

    now: int = field(default_factory=lambda: int(time.time()))
    now_time: str = field(default_factory=lambda: time.strftime("%H:%M"))
    now_weekday: str = field(default_factory=lambda: time.strftime("%a").lower())
    now_date: str = field(default_factory=lambda: time.strftime("%Y-%m-%d"))
    member_alone: bool = True
    member_role: str = "adult"
    member_count: int = 1
    household_mode: str = "day"
    weather: str = "clear"
    calendar_events: list = field(default_factory=list)
    window: WindowStore = field(default_factory=WindowStore)
    fields: dict = field(default_factory=dict)

    def field_value(self, key: str) -> Any:
        """从 fields 字典取字段值"""
        if key in self.fields:
            return self.fields[key]
        # 尝试从 window store 取
        if key.startswith("sensor."):
            sensor = key[len("sensor."):]
            return self.window.value(sensor)
        return None


# ============================================================
# 规则存储
# ============================================================


class RuleStore:
    """SQLite 规则存储"""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """确保 4 张表存在（依赖 memory.schema.sql 已加载）"""
        with self._conn() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS rules (
                  id TEXT PRIMARY KEY,
                  household_id INTEGER NOT NULL DEFAULT 1,
                  description TEXT NOT NULL,
                  yaml_body TEXT NOT NULL,
                  confidence_base REAL DEFAULT 0.7,
                  cooldown INTEGER DEFAULT 3600,
                  window TEXT DEFAULT '1min',
                  enabled INTEGER DEFAULT 1,
                  archived_at INTEGER,
                  created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
                  updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
                  author_type TEXT NOT NULL DEFAULT 'system',
                  author_id INTEGER,
                  validated_by INTEGER,
                  category TEXT,
                  severity TEXT DEFAULT 'care',
                  version INTEGER DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS rule_state (
                  rule_id TEXT PRIMARY KEY,
                  household_id INTEGER NOT NULL DEFAULT 1,
                  state TEXT NOT NULL DEFAULT 'cold_start',
                  last_fire_at INTEGER,
                  last_eval_at INTEGER,
                  cooldown_until INTEGER,
                  true_positive_count INTEGER DEFAULT 0,
                  false_positive_count INTEGER DEFAULT 0,
                  updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
                );
                CREATE TABLE IF NOT EXISTS rule_audit_log (
                  id INTEGER PRIMARY KEY,
                  rule_id TEXT NOT NULL,
                  household_id INTEGER NOT NULL DEFAULT 1,
                  fired_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
                  finished_at INTEGER,
                  kind TEXT NOT NULL,
                  confidence REAL,
                  matched_predicates TEXT,
                  evidence_snapshot TEXT,
                  detail TEXT,
                  ack_at INTEGER,
                  ack_by INTEGER
                );
                CREATE TABLE IF NOT EXISTS rule_feedback (
                  id INTEGER PRIMARY KEY,
                  rule_id TEXT NOT NULL,
                  fire_id INTEGER NOT NULL,
                  household_id INTEGER NOT NULL DEFAULT 1,
                  member_id INTEGER NOT NULL,
                  feedback TEXT NOT NULL,
                  note TEXT,
                  created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
                );
                """
            )
            # 兼容旧库：补 cooldown/window 列
            cols = {row["name"] for row in c.execute("PRAGMA table_info(rules)").fetchall()}
            if "cooldown" not in cols:
                c.execute("ALTER TABLE rules ADD COLUMN cooldown INTEGER DEFAULT 3600")
            if "window" not in cols:
                c.execute("ALTER TABLE rules ADD COLUMN window TEXT DEFAULT '1min'")

    def upsert_rule(self, rule: Rule) -> None:
        with self._conn() as c:
            c.execute(
                """INSERT OR REPLACE INTO rules (
                  id, household_id, description, yaml_body, confidence_base,
                  cooldown, window, enabled, severity, category, author_type, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    rule.id,
                    rule.household_id,
                    rule.description,
                    yaml.dump(rule.yaml_body, allow_unicode=True),
                    rule.confidence_base,
                    rule.cooldown,
                    rule.window,
                    1 if rule.enabled else 0,
                    rule.severity,
                    rule.category,
                    rule.author_type,
                    int(time.time()),
                ),
            )
            # 初始化 state
            c.execute(
                """INSERT OR IGNORE INTO rule_state (rule_id, household_id, state)
                   VALUES (?, ?, 'cold_start')""",
                (rule.id, rule.household_id),
            )

    def list_enabled_rules(self, household_id: int = 1) -> list[Rule]:
        with self._conn() as c:
            rows = c.execute(
                """SELECT * FROM rules
                   WHERE enabled = 1 AND archived_at IS NULL AND household_id = ?
                   ORDER BY id""",
                (household_id,),
            ).fetchall()
        return [self._row_to_rule(r) for r in rows]

    def get_state(self, rule_id: str) -> RuleState | None:
        with self._conn() as c:
            row = c.execute(
                "SELECT * FROM rule_state WHERE rule_id = ?", (rule_id,)
            ).fetchone()
        if not row:
            return None
        return RuleState(
            rule_id=row["rule_id"],
            state=row["state"],
            last_fire_at=row["last_fire_at"],
            last_eval_at=row["last_eval_at"],
            cooldown_until=row["cooldown_until"],
            true_positive_count=row["true_positive_count"],
            false_positive_count=row["false_positive_count"],
        )

    def update_state(self, state: RuleState) -> None:
        with self._conn() as c:
            c.execute(
                """UPDATE rule_state SET
                  state = ?, last_fire_at = ?, last_eval_at = ?,
                  cooldown_until = ?, true_positive_count = ?,
                  false_positive_count = ?, updated_at = ?
                  WHERE rule_id = ?""",
                (
                    state.state,
                    state.last_fire_at,
                    state.last_eval_at,
                    state.cooldown_until,
                    state.true_positive_count,
                    state.false_positive_count,
                    int(time.time()),
                    state.rule_id,
                ),
            )

    def log_fire(
        self,
        rule_id: str,
        household_id: int,
        kind: str,
        confidence: float | None = None,
        matched: list | None = None,
        evidence: dict | None = None,
        detail: dict | str | None = None,
    ) -> int:
        with self._conn() as c:
            cur = c.execute(
                """INSERT INTO rule_audit_log (
                  rule_id, household_id, kind, confidence, matched_predicates, evidence_snapshot, detail
                ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    rule_id,
                    household_id,
                    kind,
                    confidence,
                    json.dumps(matched or [], ensure_ascii=False),
                    json.dumps(evidence or {}, ensure_ascii=False),
                    json.dumps(detail, ensure_ascii=False) if detail is not None else None,
                ),
            )
            return cur.lastrowid

    def _row_to_rule(self, row: sqlite3.Row) -> Rule:
        return Rule(
            id=row["id"],
            description=row["description"],
            yaml_body=yaml.safe_load(row["yaml_body"]) or {},
            confidence_base=row["confidence_base"],
            cooldown=row["cooldown"],
            window=row["window"],
            severity=row["severity"],
            category=row["category"],
            author_type=row["author_type"],
            enabled=bool(row["enabled"]),
            household_id=row["household_id"],
        )


# ============================================================
# 规则扫描器（v0.1 无置信度版）
# ============================================================


class RuleScanner:
    """v0.2 规则扫描器（含置信度校准 + v0.3 兜底推理）

    周期（默认 10s）扫所有 armed 规则，评估谓词：
    - 命中 → 置信度校准 → 按区间处置（auto/notify/ask/fallback）
    - 命中 + 置信度 ≥ ask → fire + 调 then
    - 命中 + 置信度 < ask → 仅 audit + 询问用户
    - 兜底：多规则低可信 + 矛盾 → 调 FallbackReasoner
    - 未命中 → 仍 armed
    - cooldown 中 → 命中只记 audit 不执行
    """

    def __init__(
        self,
        store: RuleStore,
        on_fire: Callable[[Rule, dict, CalibratedConfidence], None] | None = None,
        fallback_reasoner: "FallbackReasoner | None" = None,
        alert_store: Any | None = None,
        notifier: Any | None = None,
    ):
        self.store = store
        self.on_fire = on_fire or self._default_on_fire
        self.fallback = fallback_reasoner
        self.alert_store = alert_store
        self.notifier = notifier
        self.window = WindowStore()
        self.eval_ctx = EvalContext(window=self.window)
        self._last_scan = 0.0
        # 注入 confidence 模块
        from .confidence import (
            calibrate, freshness_factor, history_match_factor,
            member_baseline_factor, false_positive_penalty, enforce_invariants,
        )
        self._calibrate = calibrate
        self._freshness_factor = freshness_factor
        self._history_match_factor = history_match_factor
        self._member_baseline_factor = member_baseline_factor
        self._fp_penalty = false_positive_penalty
        self._enforce_invariants = enforce_invariants
        # v0.3 追踪低可信规则数（用于兜底触发判定）
        self._low_confidence_count = 0
        self._last_low_confidence_rules: list[str] = []

    def _default_on_fire(
        self, rule: Rule, evidence: dict, conf: CalibratedConfidence
    ) -> None:
        """默认 fire 处理：v0.2 含置信度 + 区间处置"""
        if conf.interval == "fallback":
            # 兜底 LLM 推理（v0.3 接入）
            if self.fallback:
                fb_result = self.fallback.reason(
                    rule=rule,
                    evidence={
                        **evidence,
                        "confidence": conf.final,
                        "low_confidence_count": self._low_confidence_count,
                        "has_contradiction": self._has_signal_contradiction(evidence),
                    },
                )
                if fb_result.triggered:
                    logger.warning(
                        "[fallback-fire] %s action=%s conf=%.2f",
                        rule.id, fb_result.suggested_action, fb_result.confidence_after,
                    )
                    # 兜底结果 + 原始规则 fire 一起执行
                    # 注意：兜底 LLM 不直接执行，标记为"ask_user"等用户决定
            else:
                logger.info(
                    "[rule-fallback-noop] %s conf=%.2f → 无兜底推理器",
                    rule.id, conf.final,
                )
        else:
            logger.warning(
                "[rule-fire] %s severity=%s conf=%.2f interval=%s",
                rule.id, rule.severity, conf.final, conf.interval,
            )
        # 写 audit log
        self.store.log_fire(
            rule_id=rule.id,
            household_id=rule.household_id,
            kind="fire",
            confidence=conf.final,
            matched=list(evidence.get("matched", [])),
            evidence=evidence,
        )

        # 安全/关怀级规则：写开放告警 + 投递通知（Telegram / 站内）
        if self.alert_store is not None and rule.severity in ("safety", "care"):
            title = f"[{rule.severity}] {rule.description}"
            alert_id = self.alert_store.add_alert(
                rule.severity,
                title,
                detail=f"rule={rule.id} confidence={conf.final:.2f}",
                source="rule_engine",
            )
            if self.notifier is not None:
                self.notifier.notify_rule_fire(alert_id=alert_id, rule=rule, confidence=conf.final)

        # then.control 动作：进入待确认队列，绝不自动执行
        then_actions = rule.yaml_body.get("then", []) or []
        for item in then_actions:
            if not isinstance(item, dict):
                continue
            control = item.get("control")
            if not isinstance(control, dict):
                continue
            device_id = control.get("device_id") or control.get("device")
            action = control.get("action")
            if self.alert_store is None or not device_id or not action:
                continue
            try:
                token = self.alert_store.create_pending_action(
                    rule.id, device_id, action, control.get("params")
                )
            except Exception as e:
                logger.error("创建待确认动作失败: %s", e)
                continue
            alert_id = self.alert_store.add_alert(
                "care",
                f"[confirm] {rule.description}",
                detail=f"pending_action={token} device={device_id} action={action}",
                source="rule_engine",
            )
            if self.notifier is not None:
                self.notifier.notify_alert(
                    alert_id=alert_id,
                    title="需确认操作",
                    body=f"规则 {rule.id}：{device_id} {action}；确认: /api/actions/{token}/confirm",
                )

    def _has_signal_contradiction(self, evidence: dict) -> bool:
        """检测证据中是否有矛盾（v0.3 简化：检查 attributes.has_contradiction 标记）"""
        return evidence.get("attributes", {}).get("has_contradiction", False)

    def _calc_confidence(self, rule: Rule, state: RuleState) -> CalibratedConfidence:
        """计算 4 因子置信度（v0.2 完整版）"""
        # v0.2 简化版：freshness/history_match 用合理默认；member_baseline 用 1.0；
        # false_positive_penalty 读 state.false_positive_count
        freshness = self._freshness_factor(0, 60)  # v0.2 mock：永远新鲜
        history_match = self._history_match_factor(
            rule_hit_count=state.true_positive_count + state.false_positive_count,
            rule_true_positive=state.true_positive_count,
        )
        member_baseline = 1.0  # v0.2 mock
        fp_penalty = self._fp_penalty(state.false_positive_count)

        conf = self._calibrate(
            base=rule.confidence_base,
            freshness=freshness,
            history_match=history_match,
            member_baseline=member_baseline,
            false_positive_penalty=fp_penalty,
        )

        # 强制不变式
        adjusted, warning = self._enforce_invariants(rule.severity, rule.confidence_base, conf.final)
        if warning:
            logger.warning(f"[rule-invariant] {rule.id}: {warning}")
            conf.final = adjusted
            if warning.startswith("irreversible"):
                conf.rationale += f"（{warning}）"

        return conf

    def scan_once(self, household_id: int = 1) -> list[dict]:
        """扫一次所有启用的规则。返回本周期触发的规则列表（含置信度）"""
        now = int(time.time())
        fired: list[dict] = []
        rules = self.store.list_enabled_rules(household_id)

        # v0.3 本周期低可信规则计数（用于兜底触发判定）
        self._low_confidence_count = 0
        self._last_low_confidence_rules = []

        for rule in rules:
            state = self.store.get_state(rule.id)
            if state is None:
                state = RuleState(rule_id=rule.id, state="cold_start")

            # 状态机：cold_start → armed 至少经过 1 个窗口
            if state.state == "cold_start":
                state.state = "armed"
                state.last_eval_at = now
                self.store.update_state(state)
                continue

            # disabled / cooldown 检查
            if state.state == "disabled":
                continue
            if state.state == "cooldown" and state.cooldown_until and now < state.cooldown_until:
                continue
            if state.state == "cooldown" and state.cooldown_until and now >= state.cooldown_until:
                # cooldown 到期后复位为 armed，允许再次触发
                state.state = "armed"
                state.cooldown_until = None

            # armed / cooldown 已结束 → 评估谓词
            try:
                matched = evaluate_predicate(rule.yaml_body.get("when"), self.eval_ctx)
            except Exception as e:
                self.store.log_fire(
                    rule_id=rule.id, household_id=household_id,
                    kind="eval_error", detail=str(e),
                )
                continue

            state.last_eval_at = now
            evidence = {"matched": self._collect_matched(rule, self.eval_ctx), "ts": now}

            if matched:
                # v0.2 计算置信度
                conf = self._calc_confidence(rule, state)

                if state.state == "cooldown":
                    # cooldown 期间命中，只记不执行
                    self.store.log_fire(
                        rule_id=rule.id, household_id=household_id,
                        kind="cooldown_suppressed",
                        confidence=conf.final,
                    )
                elif conf.should_execute:
                    # armed 命中 + 置信度足够 → fire
                    state.state = "firing"
                    state.last_fire_at = now
                    self.store.update_state(state)

                    self.on_fire(rule, evidence, conf)
                    fired.append({
                        "rule_id": rule.id,
                        "confidence": conf.final,
                        "interval": conf.interval,
                        "evidence": evidence,
                    })

                    # 进入 cooldown
                    state.state = "cooldown"
                    state.cooldown_until = now + rule.cooldown
                    self.store.update_state(state)
                else:
                    # 命中但置信度不够（ask / fallback）→ 仅 audit + 不执行
                    self.store.log_fire(
                        rule_id=rule.id, household_id=household_id,
                        kind="low_confidence",
                        confidence=conf.final,
                        detail={"interval": conf.interval, "rationale": conf.rationale},
                    )
                    # v0.3 统计低可信规则
                    if conf.final < FALLBACK_CONFIDENCE_THRESHOLD:
                        self._low_confidence_count += 1
                        self._last_low_confidence_rules.append(rule.id)
            else:
                self.store.update_state(state)

        self._last_scan = time.time()
        return fired

    def _collect_matched(self, rule: Rule, ctx: EvalContext) -> list[str]:
        """收集本次命中的叶子谓词"""
        matched: list[str] = []

        def walk(node: Any) -> None:
            if isinstance(node, list):
                for item in node:
                    walk(item)
            elif isinstance(node, dict):
                for key, value in node.items():
                    if key in ("all", "any", "none"):
                        walk(value)
                    else:
                        try:
                            if evaluate_predicate({key: value}, ctx):
                                matched.append(f"{key}: {value}")
                        except Exception:
                            pass
            elif isinstance(node, str):
                try:
                    if evaluate_predicate(node, ctx):
                        matched.append(node)
                except Exception:
                    pass

        walk(rule.yaml_body.get("when"))
        return matched

    def run_forever(self, household_id: int = 1, interval: float = 10.0) -> None:
        """永久循环（供后台线程）"""
        logger.info("规则扫描器启动 interval=%.1fs", interval)
        while True:
            try:
                self.scan_once(household_id)
            except Exception as e:
                logger.error("扫描异常: %s", e)
            time.sleep(interval)


# ============================================================
# 5 条 P0 种子规则（v0.1）
# ============================================================


SEED_RULES_P0: list[str] = [
    # 1. elderly_fall_suspect_v1
    """
id: elderly_fall_suspect_v1
description: 独居老人夜间起夜后长时间未归床，疑似摔倒
severity: safety
category: elderly_care
confidence_base: 0.7
cooldown: 3600
window: 1min
when:
  all:
    - bed_pressure.away_minutes > 30
    - motion.living_room.duration_minutes > 30
    - time.in_window: ["22:00", "06:00"]
    - member.is_alone_at_home: true
then:
  - escalate:
      ladder: [primary_caregiver, secondary_caregiver]
      level: safety
""",
    # 2. water_microleak_night_v1
    """
id: water_microleak_night_v1
description: 凌晨无人时段水表持续小流量，疑似漏水
severity: care
category: water_safety
confidence_base: 0.85
cooldown: 7200
window: 5min
when:
  all:
    - water_meter.flow > 0.5
    - water_meter.flow < 5.0
    - water_meter.duration_minutes > 60
    - time.in_window: ["02:00", "05:00"]
    - member.is_alone_at_home: false
then:
  - escalate:
      ladder: [primary_caregiver]
      level: care
""",
    # 3. stranger_porch_loiter_v1
    """
id: stranger_porch_loiter_v1
description: 门口摄像头检测到陌生人停留 >3 分钟，全家都在外
severity: safety
category: security
confidence_base: 0.75
cooldown: 1800
window: 1min
when:
  all:
    - camera.porch.duration_minutes > 3
    - any_family_at_home: false
    - front_door.lock.opened_10min: false
then:
  - escalate:
      ladder: [primary_caregiver]
      level: safety
""",
    # 4. elderly_no_activity_v1
    """
id: elderly_no_activity_v1
description: 老人 12 小时无活动迹象
severity: safety
category: elderly_care
confidence_base: 0.65
cooldown: 7200
window: 60min
when:
  all:
    - motion.last_change_ago > 720
    - water_meter.last_use_ago > 720
    - member.role: elder
then:
  - escalate:
      ladder: [primary_caregiver, secondary_caregiver]
      level: safety
""",
    # 5. smoke_detector_v1
    """
id: smoke_detector_v1
description: 烟雾传感器触发
severity: safety
category: fire_safety
confidence_base: 0.95
cooldown: 0
window: 1min
when:
  all:
    - smoke_detector.triggered: true
then:
  - escalate:
      ladder: [primary_caregiver, 119]
      level: safety
      sos_bypass: true
""",
]


def seed_default_rules(rule_store: RuleStore, household_id: int = 1) -> int:
    """种子 5 条 P0 规则（v0.1）"""
    seeded = 0
    for yaml_text in SEED_RULES_P0:
        try:
            rule = parse_rule_yaml(yaml_text)
            rule.household_id = household_id
            rule_store.upsert_rule(rule)
            seeded += 1
        except DSLError as e:
            logger.error("种子规则解析失败: %s", e)
    logger.info("已种子 %d 条 P0 规则", seeded)
    return seeded
