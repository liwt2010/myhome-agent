-- MiHome Agent 数据库 schema
-- 详见 ARCHITECTURE.md 第 5 节

PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS devices (
    id          TEXT PRIMARY KEY,          -- 米家 did 或自定义 id
    name        TEXT NOT NULL,
    model       TEXT,                      -- 如 zhimi.airpurifier.ma2
    type        TEXT,                      -- 归一化类型: light/sensor_ht/lock/plug/...
    room        TEXT,
    ip          TEXT,
    token       TEXT,                      -- 本地控制 token
    source      TEXT DEFAULT 'cloud',      -- local | cloud | import
    online      INTEGER DEFAULT 0,
    extra       TEXT,                      -- JSON 扩展字段
    updated_at  TEXT DEFAULT (datetime('now', 'localtime'))
);

-- 设备状态时序（数值/状态采样）
CREATE TABLE IF NOT EXISTS readings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id  TEXT NOT NULL,
    metric     TEXT NOT NULL,              -- temperature/humidity/power/illumination/...
    value      REAL,
    value_text TEXT,                       -- 非数值状态
    ts         TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX IF NOT EXISTS idx_readings_dev_ts ON readings(device_id, metric, ts);

-- 家庭离散事件（开门/人体移动/按键/回家离家/告警...）
CREATE TABLE IF NOT EXISTS events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id  TEXT,
    member_id  INTEGER,
    kind       TEXT NOT NULL,              -- motion/door_open/button/arrive/leave/...
    detail     TEXT,                       -- JSON
    ts         TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
CREATE INDEX IF NOT EXISTS idx_events_kind_ts ON events(kind, ts);

-- 家庭成员档案
CREATE TABLE IF NOT EXISTS members (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    role        TEXT,                      -- 爸爸/妈妈/爷爷/孩子...
    preferences TEXT,                      -- JSON: {"睡觉时间": "23:00", "空调温度": 26}
    devices     TEXT,                      -- JSON: 关联设备(手机MAC/手环)用于在场推断
    created_at  TEXT DEFAULT (datetime('now', 'localtime'))
);

-- 成员在场状态
CREATE TABLE IF NOT EXISTS presence (
    member_id  INTEGER PRIMARY KEY,
    at_home    INTEGER DEFAULT 0,
    room       TEXT,
    since      TEXT,
    evidence   TEXT                        -- 判定依据
);

-- 学习到的作息模式
CREATE TABLE IF NOT EXISTS routines (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id  INTEGER,                    -- NULL 表示全家
    weekday    INTEGER,                    -- 0=周一 ... 6=周日, NULL=每天
    hour       INTEGER NOT NULL,
    kind       TEXT NOT NULL,              -- first_activity/last_activity/motion_density...
    value      REAL,
    confidence REAL DEFAULT 0,
    updated_at TEXT DEFAULT (datetime('now', 'localtime')),
    UNIQUE(member_id, weekday, hour, kind)
);

-- 异常告警
CREATE TABLE IF NOT EXISTS alerts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    level      TEXT NOT NULL,              -- info/warning/critical
    title      TEXT NOT NULL,
    detail     TEXT,
    source     TEXT,                       -- hard_rule/baseline/agent
    status     TEXT DEFAULT 'open',        -- open/acked/resolved
    ts         TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- 智能体长期记忆
CREATE TABLE IF NOT EXISTS memories (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    content    TEXT NOT NULL,
    tags       TEXT,                       -- 逗号分隔，便于 recall 过滤
    member_id  INTEGER,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

-- 对话历史（按会话）
CREATE TABLE IF NOT EXISTS chat_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role       TEXT NOT NULL,              -- user/assistant
    content    TEXT NOT NULL,              -- JSON 序列化的 content
    ts         TEXT DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_history(session_id, id);

-- v2.19 §53 跨信号推理规则引擎（4 张表）
-- 迁移脚本编号：004_rules_engine.sql（v0.1 起步，v0.2 扩）

-- 规则定义
CREATE TABLE IF NOT EXISTS rules (
  id TEXT PRIMARY KEY,                -- kebab-case 唯一标识
  household_id INTEGER NOT NULL DEFAULT 1,  -- 多家庭隔离（v0.1 简化默认 1）
  description TEXT NOT NULL,
  yaml_body TEXT NOT NULL,
  confidence_base REAL DEFAULT 0.7,
  enabled INTEGER DEFAULT 1,
  archived_at INTEGER,
  created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
  updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
  author_type TEXT NOT NULL DEFAULT 'system',  -- 'system' | 'doctor' | 'family' | 'llm_suggested'
  author_id INTEGER,
  validated_by INTEGER,
  category TEXT,
  severity TEXT DEFAULT 'care',
  version INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_rules_household ON rules(household_id) WHERE archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_rules_severity ON rules(household_id, severity);

-- 规则状态
CREATE TABLE IF NOT EXISTS rule_state (
  rule_id TEXT PRIMARY KEY,
  household_id INTEGER NOT NULL DEFAULT 1,
  state TEXT NOT NULL DEFAULT 'cold_start',  -- 'disabled'|'cold_start'|'armed'|'firing'|'cooldown'
  last_fire_at INTEGER,
  last_eval_at INTEGER,
  cooldown_until INTEGER,
  true_positive_count INTEGER DEFAULT 0,
  false_positive_count INTEGER DEFAULT 0,
  updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
  CHECK (state IN ('disabled','cold_start','armed','firing','cooldown'))
);

CREATE INDEX IF NOT EXISTS idx_rule_state_household ON rule_state(household_id);

-- 规则审计日志
CREATE TABLE IF NOT EXISTS rule_audit_log (
  id INTEGER PRIMARY KEY,
  rule_id TEXT NOT NULL,
  household_id INTEGER NOT NULL DEFAULT 1,
  fired_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
  finished_at INTEGER,
  kind TEXT NOT NULL,  -- 'fire'|'stale_data'|'eval_error'|'cooldown_suppressed'|'auto_disabled'|'invalid_predicate'|'rule_changed'
  confidence REAL,
  matched_predicates TEXT,
  evidence_snapshot TEXT,
  detail TEXT,
  ack_at INTEGER,
  ack_by INTEGER
);

CREATE INDEX IF NOT EXISTS idx_rule_audit_rule ON rule_audit_log(rule_id, fired_at DESC);
CREATE INDEX IF NOT EXISTS idx_rule_audit_household ON rule_audit_log(household_id, fired_at DESC);
CREATE INDEX IF NOT EXISTS idx_rule_audit_kind ON rule_audit_log(household_id, kind, fired_at DESC);

-- 规则反馈
CREATE TABLE IF NOT EXISTS rule_feedback (
  id INTEGER PRIMARY KEY,
  rule_id TEXT NOT NULL,
  fire_id INTEGER NOT NULL,
  household_id INTEGER NOT NULL DEFAULT 1,
  member_id INTEGER NOT NULL,
  feedback TEXT NOT NULL,  -- 'true_positive'|'false_positive'|'ignored'|'disable'
  note TEXT,
  created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
  CHECK (feedback IN ('true_positive','false_positive','ignored','disable'))
);

CREATE INDEX IF NOT EXISTS idx_rule_feedback_rule ON rule_feedback(rule_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_rule_feedback_member ON rule_feedback(member_id, created_at DESC);

-- schema_meta（v0.1 起步版本号）
CREATE TABLE IF NOT EXISTS schema_meta (
  key TEXT PRIMARY KEY,
  value TEXT
);

INSERT OR REPLACE INTO schema_meta(key, value) VALUES('version', '0.7.0');
INSERT OR REPLACE INTO schema_meta(key, value) VALUES('rule_engine', 'v0.1.0');
