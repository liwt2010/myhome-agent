# Schema 详细字段定义

> **同步状态（2026-08-07）**：本文档已纳入整体同步；与当前实现的差异以 [ARCHITECTURE.md](../ARCHITECTURE.md) 状态表和 `tests/` 为准。


> `ARCHITECTURE.md` §5.0b 给的是 ER 概览。本文件给到工程级的全字段定义：列名、类型、是否可空、默认值、用途说明、来源/去向。
>
> Schema 版本由 `schema_meta.version` 追踪，所有变更都通过 `myhome_agent/migrations/NNN_*.sql` 走（见 MIGRATION.md §7）。本文件不直接对应 SQL 脚本，而是文档的工程契约。

---

## 1. devices（设备目录）

设备一行的字段：

| 列 | 类型 | 非空 | 默认 | 用途 | 来源 |
|----|------|-----|------|------|------|
| `id` | TEXT PK | ✅ | — | 设备主键（米家 did 或本地 UUID） | sync_from_cloud |
| `name` | TEXT | ✅ | — | 设备名（米家给的名字） | sync_from_cloud |
| `type` | TEXT | ✅ | — | 设备类型：`light` / `ac` / `plug` / `lock` / `sensor` / `camera` / ... | spec_normalizer |
| `room` | TEXT | ❌ | NULL | 用户在 PWA 设置的房间（如 `卧室`/`客厅`） | PWA 编辑 |
| `user_label` | TEXT | ❌ | NULL | 用户自定义的别名（身份匹配优先级 1） | PWA 编辑 |
| `brand` | TEXT | ✅ | `myhome` | 品牌：`myhome` / `tuya` / ... | sync_from_cloud |
| `mac` | TEXT | ❌ | NULL | 物理 MAC（身份匹配优先级 2） | sync_from_cloud |
| `online` | INTEGER | ❌ | 0 | 最近一次轮询是否通：`1` / `0` | collectors |
| `ip` | TEXT | ❌ | NULL | 上次成功局域网直连的 IP | collectors |
| `token` | TEXT | ❌ | NULL | miio 用的 16 字节密钥 | sync_from_cloud / miio dump |
| `first_seen` | TEXT | ❌ | UTC ISO8601 | 首次发现时间 | collectors |
| `last_seen` | TEXT | ❌ | UTC ISO8601 | 最近一次成功响应时间 | collectors |
| `replaced_by` | TEXT | ❌ | NULL | 替换为新 did（`replaced_by=`），旧设备标记 | collectors |
| `spec_cache` | TEXT (JSON) | ❌ | NULL | spec 自动归一化的能力对象（见 §5.7b） | spec_normalizer |
| `control_confirm_required` | INTEGER | ❌ | NULL | 强制二次确认（NULL=按 type 默认） | config |
| `extra` | TEXT (JSON) | ❌ | NULL | 自由扩展字段；新字段进 JSON 而不开列（MIGRATION §2b） | user/plugin |

**索引**：
- `idx_devices_mac (mac)` — 设备替换匹配
- `idx_devices_room (room)` — PWA 房间过滤
- `idx_devices_user_label (user_label)` — 用户别名优先匹配

**`spec_cache` 内容 schema**（JSON 内嵌）：

```json
{
  "transport": "wifi" | "bluetooth_mesh" | "zigbee",
  "local_controllable": true | false,
  "metrics": [{"name": "temperature", "unit": "℃", "access": "r"}, ...],
  "events":  [{"name": "unlock", "has_actor_id": true}, ...],
  "actions": [{"name": "set_power", "params": [{"name": "on", "type": "bool"}]}]
}
```

**`extra` 用途举例**（不强制）：

```json
{
  "vendor_id": "lumi.plug.m1",
  "firmware": "1.5.0_0000",
  "notes": "客厅 TV 旁边那台"
}
```

---

## 2. readings（时序采集）

| 列 | 类型 | 非空 | 默认 | 用途 |
|----|------|-----|------|------|
| `id` | INTEGER PK AUTOINCREMENT | ✅ | — | rowid |
| `device_id` | TEXT FK→devices.id | ✅ | — | 关联设备 |
| `metric` | TEXT | ✅ | — | 指标名（如 `temperature` / `humidity` / `power`） |
| `value` | REAL | ❌ | NULL | 数值 |
| `value_str` | TEXT | ❌ | NULL | 字符串值（少数设备用） |
| `ts` | TEXT | ✅ | — | UTC ISO8601（见 ARCH §7b） |

**索引**：
- `idx_readings_dev_metric_ts (device_id, metric, ts)` — 时间范围主查询路径
- `idx_readings_ts (ts)` — 全局时序扫描

**分桶聚合（保留 ≥30 天后）**：见 MIGRATION §2 / RETENTION 计划。

---

## 3. events（事件流）

| 列 | 类型 | 非空 | 默认 | 用途 |
|----|------|-----|------|------|
| `id` | INTEGER PK AUTOINCREMENT | ✅ | — | rowid |
| `kind` | TEXT | ✅ | — | 事件类型：`motion` / `door_open` / `unlock` / `control` / `arrive` / `leave` / `alert` / `chat` |
| `device_id` | TEXT FK→devices.id | ❌ | NULL | 关联设备（设备事件必有；家庭级事件可空） |
| `member_id` | INTEGER FK→members.id | ❌ | NULL | 关联成员（成员事件必有） |
| `detail` | TEXT (JSON) | ❌ | NULL | 自由 JSON：原始字段、payload 等 |
| `ts` | TEXT | ✅ | — | UTC ISO8601 |

**索引**：
- `idx_events_kind_ts (kind, ts)` — 按事件类型扫时间窗
- `idx_events_ts (ts)` — 全局时间窗
- `idx_events_member_ts (member_id, ts)` — 成员事件流

**生命周期**：永久保留（家庭级事件不删除；可用 `events.ts < ...` 后台归档到 `events_archive`）。

---

## 4. members（成员档案）

| 列 | 类型 | 非空 | 默认 | 用途 |
|----|------|-----|------|------|
| `id` | INTEGER PK AUTOINCREMENT | ✅ | — | |
| `name` | TEXT | ✅ | — | 真实姓名 |
| `display_name` | TEXT | ❌ | NULL | 脱敏后别名（如"爸爸""妈妈"），上云/DLNM 用 |
| `role` | TEXT | ✅ | — | `admin` / `adult` / `child` / `guest` |
| `devices` | TEXT (JSON array) | ✅ | `[]` | 关联设备列表，如 `["dev_123"]`（手机/手环等） |
| `channels` | TEXT (JSON object) | ❌ | NULL | 渠道身份：telegram user_id、企微 openid、PWA token 等 |
| `lock_key_map` | TEXT (JSON object) | ❌ | NULL | 门锁 actor_id → member_id 映射：PWA 可编辑 |
| `preferences` | TEXT (JSON object) | ❌ | NULL | 个人偏好（关心的指标、显示别名、阈值） |
| `created_at` | TEXT | ✅ | UTC ISO8601 | 创建时间 |
| `notes` | TEXT | ❌ | NULL | 用户备注 |

**索引**：
- `idx_members_role (role)` — 按角色快速筛

**`lock_key_map` 例子**（来自 §5.4）：

```json
{
  "fingerprint_1": "爸爸",
  "password_2": "妈妈",
  "key_id_face_a": "奶奶"
}
```

---

## 5. presence（在场状态）

| 列 | 类型 | 非空 | 默认 | 用途 |
|----|------|-----|------|------|
| `member_id` | INTEGER PK FK→members.id | ✅ | — | 一成员一行 |
| `at_home` | INTEGER | ❌ | NULL | `1`=在家，`0`=外出，`NULL`=未知 |
| `evidence` | TEXT | ❌ | NULL | 推断依据说明（如"手机 A 在线""指纹 1 触发"） |
| `since` | TEXT | ✅ | UTC ISO8601 | 当前状态起始时间 |
| `updated_at` | TEXT | ✅ | UTC ISO8601 | 最近一次变化 |

**写入**：presence.py/registry 推断时 upsert。

---

## 6. routines（作息基线）

| 列 | 类型 | 非空 | 默认 | 用途 |
|----|------|-----|------|------|
| `id` | INTEGER PK AUTOINCREMENT | ✅ | — | |
| `kind` | TEXT | ✅ | — | `first_activity` / `last_activity` / `motion_density` |
| `weekday` | INTEGER | ❌ | NULL | 0-6 / NULL=全周聚合 |
| `hour` | INTEGER | ❌ | NULL | 0-23 |
| `value` | REAL | ✅ | — | 学到的值（小时/密度） |
| `confidence` | REAL | ✅ | — | 0.0-1.0（样本天数/总天数） |
| `updated_at` | TEXT | ✅ | UTC ISO8601 | |

**索引**：`idx_routines_kind (kind)`、`idx_routines_kind_weekday (kind, weekday)`

---

## 7. alerts（告警）

| 列 | 类型 | 非空 | 默认 | 用途 |
|----|------|-----|------|------|
| `id` | INTEGER PK AUTOINCREMENT | ✅ | — | |
| `level` | TEXT | ✅ | — | `info` / `warning` / `critical` |
| `title` | TEXT | ✅ | — | 告警标题（PWA 推送用） |
| `detail` | TEXT | ❌ | NULL | 详细描述（脱敏后） |
| `source` | TEXT | ✅ | — | `hard_rule` / `baseline` / `feedback_loop` / `redactor` / `system` |
| `status` | TEXT | ✅ | `open` | `open` / `acknowledged` / `resolved` |
| `ts` | TEXT | ✅ | UTC ISO8601 | 触发时间 |
| `acked_at` | TEXT | ❌ | NULL | 确认时间 |
| `acked_by` | INTEGER FK→members.id | ❌ | NULL | 谁确认 |
| `device_id` | TEXT FK→devices.id | ❌ | NULL | 关联设备 |

**索引**：`idx_alerts_status_ts (status, ts)`、`idx_alerts_level (level)`

**去重规则**：OBSERVABILITY §5.3，30 分钟内同 title 不重复，recovery 后自动清。

---

## 8. pending_confirm（高危操作待确认）

| 列 | 类型 | 非空 | 默认 | 用途 |
|----|------|-----|------|------|
| `id` | INTEGER PK AUTOINCREMENT | ✅ | — | |
| `request_id` | TEXT | ✅ | — | 关联本次请求（OBSERVABILITY §7 链路追踪 id） |
| `member_id` | INTEGER FK→members.id | ✅ | — | 发起人（防 B 替 A 确认） |
| `channel` | TEXT | ✅ | — | `pwa` / `telegram` / `wechat` / `voice` |
| `device_id` | TEXT FK→devices.id | ✅ | — | 目标设备 |
| `action` | TEXT | ✅ | — | 要执行的动作（`on`/`off`/...） |
| `params` | TEXT (JSON) | ❌ | NULL | 动作参数 |
| `ttl` | TEXT | ✅ | UTC ISO8601 | 过期时间（默认 `created_at + 2min`） |
| `created_at` | TEXT | ✅ | UTC ISO8601 | |

**索引**：`idx_pending_confirm_member_ttl (member_id, ttl)`

**校验规则**（执行前）：
1. `ttl > now`（未过期）
2. 发起人 ID = 确认人 ID（§5.3 发起=确认原则）
3. 渠道等级允许该操作（§5.3 渠道分级）
4. 设备 `control_confirm_required` = true

---

## 9. task_queue（持久任务队列）

| 列 | 类型 | 非空 | 默认 | 用途 |
|----|------|-----|------|------|
| `id` | INTEGER PK AUTOINCREMENT | ✅ | — | |
| `kind` | TEXT | ✅ | — | `poll_device` / `send_notify` / `llm_call` / `sync_from_cloud` |
| `payload` | TEXT (JSON) | ✅ | — | |
| `priority` | INTEGER | ✅ | 5 | 越小越高 |
| `retry_count` | INTEGER | ✅ | 0 | |
| `next_attempt_at` | TEXT | ✅ | UTC ISO8601 | |
| `created_at` | TEXT | ✅ | UTC ISO8601 | |
| `started_at` | TEXT | ❌ | NULL | |
| `finished_at` | TEXT | ❌ | NULL | |
| `status` | TEXT | ✅ | `pending` | `pending` / `running` / `done` / `failed` / `dlq` |
| `error` | TEXT | ❌ | NULL | 失败原因 |

**索引**：`idx_task_queue_pick (status, next_attempt_at, priority, id)`（worker 拉取用）

**清扫策略**（worker 配置）：
- 单 task `started_at` 超过 5 分钟未结束 → 视为僵尸 → 重置 status=pending, retry_count+=1
- 单 task retry_count > 5 → status=dlq, 触发 alerts

---

## 10. chat_history（对话历史）

| 列 | 类型 | 非空 | 默认 | 用途 |
|----|------|-----|------|------|
| `id` | INTEGER PK AUTOINCREMENT | ✅ | — | |
| `session_id` | TEXT | ✅ | — | `(channel, channel_user_id)` 派生，跨会话隔离 |
| `member_id` | INTEGER FK→members.id | ❌ | NULL | |
| `role` | TEXT | ✅ | — | `user` / `assistant` / `system` / `tool` |
| `content` | TEXT | ✅ | — | 已脱敏的内容 |
| `tool_calls` | TEXT (JSON) | ❌ | NULL | |
| `tool_call_id` | TEXT | ❌ | NULL | |
| `ts` | TEXT | ✅ | UTC ISO8601 | |

**索引**：
- `idx_chat_session_id (session_id, id)` — 按会话顺序读取
- `idx_chat_ts (ts)` — 全局时间窗（保留清理用，90 天）

---

## 11. memories（agent 长期记忆）

| 列 | 类型 | 非空 | 默认 | 用途 |
|----|------|-----|------|------|
| `id` | INTEGER PK AUTOINCREMENT | ✅ | — | |
| `category` | TEXT | ✅ | — | `preference` / `fact` / `rule` |
| `key` | TEXT | ✅ | — | |
| `value` | TEXT | ✅ | — | |
| `source` | TEXT | ❌ | NULL | `user` / `agent` / `inferred` |
| `created_at` | TEXT | ✅ | UTC ISO8601 | |
| `updated_at` | TEXT | ✅ | UTC ISO8601 | |

**索引**：`idx_memories_category_key (category, key)`

**约束**：写库前调 redactor（避免把已脱敏的记忆再次外发）。

---

## 12. readings_hourly（小时聚合，30 天之后）

| 列 | 类型 | 非空 | 默认 | 用途 |
|----|------|-----|------|------|
| `id` | INTEGER PK AUTOINCREMENT | ✅ | — | |
| `device_id` | TEXT FK | ✅ | — | |
| `metric` | TEXT | ✅ | — | |
| `hour` | TEXT | ✅ | — | UTC `YYYY-MM-DD HH:00:00` |
| `avg` | REAL | ✅ | — | |
| `min` | REAL | ✅ | — | |
| `max` | REAL | ✅ | — | |
| `count` | INTEGER | ✅ | — | 采样点数 |

**索引**：`idx_readings_hourly_dev_metric_hour (device_id, metric, hour)`

---

## 13. schema_meta（schema 版本）

| 列 | 类型 | 非空 | 默认 | 用途 |
|----|------|-----|------|------|
| `key` | TEXT PK | ✅ | — | |
| `value` | TEXT | ✅ | — | |

**初始行**：
- `('version', '0.5.0')`
- `('migrated_at', '<utcnow>')`
- `('app_version', '<代码当前版本>')`

---

## 14. 视图（agent 用的便利查询，未来添加）

agent 不直接连表搞 join；所有 join 走视图：

```sql
-- 家庭最新状态快读视图
CREATE VIEW v_home_latest AS
SELECT d.id, d.name, d.type, d.room, d.user_label,
       m.value AS last_value, m.ts AS last_ts,
       m.metric
FROM devices d
LEFT JOIN readings m ON m.id = (
  SELECT id FROM readings WHERE device_id = d.id
  ORDER BY ts DESC LIMIT 1
);
```

更多视图按需加。

---

## 15. 字段扩展决策（MIGRATION §2b 摘要）

- 经常过滤/聚合/排序 → 加列建索引
- 展示/调试/导出 → `extra` JSON
- 行为开关 → 加列（要可索引）
- 元数据 → JSON

---

## 18. rules（v2.19 §53 新增）

规则引擎的主表。每条规则是一个 YAML 主体 + 元数据。

| 列 | 类型 | 非空 | 默认 | 用途 | 来源 |
|----|------|-----|------|------|------|
| `id` | TEXT PK | ✅ | — | 规则唯一标识（kebab-case） | 人工 / LLM 建议 |
| `household_id` | INTEGER | ✅ | — | 多家庭隔离（§36 强制） | 系统 |
| `description` | TEXT | ✅ | — | 一句话描述 | 人工 |
| `yaml_body` | TEXT | ✅ | — | 完整 YAML 主体 | 人工 / LLM 草案 |
| `confidence_base` | REAL | ❌ | 0.7 | 基础置信度 [0.0-1.0] | 人工 |
| `enabled` | INTEGER | ❌ | 1 | 启用状态：1/0 | 人工 / 系统 |
| `archived_at` | INTEGER | ❌ | NULL | 软删除时间戳（NULL = 未删） | 系统 |
| `created_at` | INTEGER | ✅ | — | 创建时间（epoch） | 系统 |
| `updated_at` | INTEGER | ✅ | — | 最后更新时间 | 系统 |
| `author_type` | TEXT | ✅ | — | `system` / `doctor` / `family` / `llm_suggested` | 人工 |
| `author_id` | INTEGER | ❌ | NULL | 具体成员 ID（系统规则 NULL） | 系统 |
| `validated_by` | INTEGER | ❌ | NULL | LLM 规则必须有人确认 | 系统 |
| `category` | TEXT | ❌ | NULL | 分类标签：`elderly_care` / `water_safety` / `child_care` / `security` / ... | 人工 |
| `severity` | TEXT | ❌ | `care` | `safety` / `care` / `info` | 人工 |
| `version` | INTEGER | ❌ | 1 | 规则版本（每次编辑 +1） | 系统 |

**索引**：
- `idx_rules_household (household_id) WHERE archived_at IS NULL` — 多家庭隔离 + 软删除过滤
- `idx_rules_author (author_type, author_id)` — 规则来源查询
- `idx_rules_severity (household_id, severity)` — 高风险规则快速查询

**关键约束**（v2.19 §53.6.3）：
- `household_id` 强制隔离（§36）
- `author_type='llm_suggested'` 时 `validated_by` 必须非 NULL
- 任何规则变更写 `rule_audit_log`
- 删除 = 软删除（`archived_at` 设值）

---

## 19. rule_state（v2.19 §53 新增）

规则运行时状态。每次扫描更新。

| 列 | 类型 | 非空 | 默认 | 用途 | 来源 |
|----|------|-----|------|------|------|
| `rule_id` | TEXT PK | ✅ | — | 关联 rules.id | 系统 |
| `household_id` | INTEGER | ✅ | — | 多家庭隔离 | 系统 |
| `state` | TEXT | ✅ | `cold_start` | `disabled` / `cold_start` / `armed` / `firing` / `cooldown` | 系统 |
| `last_fire_at` | INTEGER | ❌ | NULL | 最近一次 fire 的时间戳 | 系统 |
| `last_eval_at` | INTEGER | ❌ | NULL | 最近一次评估时间 | 系统 |
| `cooldown_until` | INTEGER | ❌ | NULL | cooldown 结束时间（epoch） | 系统 |
| `true_positive_count` | INTEGER | ❌ | 0 | 用户反馈"真异常"次数 | 系统 |
| `false_positive_count` | INTEGER | ❌ | 0 | 用户反馈"误报"次数 | 系统 |
| `updated_at` | INTEGER | ✅ | — | 状态最后更新时间 | 系统 |

**索引**：
- `idx_rule_state_household (household_id)` — 多家庭隔离
- `idx_rule_state_cooldown (cooldown_until) WHERE state='cooldown'` — cooldown 推进

**关键约束**：
- `state` 必为 5 选 1（CHECK 约束数据库层加）
- `cooldown_until` 与 `state='cooldown'` 一致性由应用层保证
- 30 天未触发 + `state='armed'` → 提示"该规则长期未命中"

---

## 20. rule_audit_log（v2.19 §53 新增）

规则审计日志。每次 fire / 误报 / 调参都进。**不分表**（用 household_id 索引）。

| 列 | 类型 | 非空 | 默认 | 用途 | 来源 |
|----|------|-----|------|------|------|
| `id` | INTEGER PK | ✅ | — | 自增主键 | 系统 |
| `rule_id` | TEXT | ✅ | — | 关联 rules.id | 系统 |
| `household_id` | INTEGER | ✅ | — | 多家庭隔离 | 系统 |
| `fired_at` | INTEGER | ✅ | — | 触发时间（epoch） | 系统 |
| `finished_at` | INTEGER | ❌ | NULL | 动作完成时间 | 系统 |
| `kind` | TEXT | ✅ | — | `fire` / `stale_data` / `eval_error` / `cooldown_suppressed` / `auto_disabled` / `invalid_predicate` / `rule_changed` | 系统 |
| `confidence` | REAL | ❌ | NULL | 触发时计算的置信度 | 系统 |
| `matched_predicates` | TEXT (JSON) | ❌ | NULL | 命中的谓词列表（JSON 数组） | 系统 |
| `evidence_snapshot` | TEXT (JSON) | ❌ | NULL | 证据快照（30 天后自动清理） | 系统 |
| `detail` | TEXT (JSON) | ❌ | NULL | 其他结构化信息 | 系统 |
| `ack_at` | INTEGER | ❌ | NULL | 人工 ack 时间 | 系统 |
| `ack_by` | INTEGER | ❌ | NULL | ack 成员 ID | 系统 |

**索引**：
- `idx_rule_audit_rule (rule_id, fired_at DESC)` — 规则触发历史
- `idx_rule_audit_household (household_id, fired_at DESC)` — 多家庭 + 时间过滤
- `idx_rule_audit_kind (household_id, kind, fired_at DESC)` — 误报分析

**关键约束**：
- `household_id` 强制隔离
- `evidence_snapshot` 30 天自动清理（保留结构化字段）
- 写入频率：每条规则每 10s 一次扫描，hit 率 1% → 100 条规则每天 8640 行
- 容量：30 天保留 100 万行（v2.19 §53.9 容量边界）

---

## 21. rule_feedback（v2.19 §53 新增）

用户对规则触发的反馈。用于置信度校准。

| 列 | 类型 | 非空 | 默认 | 用途 | 来源 |
|----|------|-----|------|------|------|
| `id` | INTEGER PK | ✅ | — | 自增主键 | 系统 |
| `rule_id` | TEXT | ✅ | — | 关联 rules.id | 系统 |
| `fire_id` | INTEGER | ✅ | — | 关联 rule_audit_log.id | 系统 |
| `household_id` | INTEGER | ✅ | — | 多家庭隔离 | 系统 |
| `member_id` | INTEGER | ✅ | — | 反馈成员 ID | 系统 |
| `feedback` | TEXT | ✅ | — | `true_positive` / `false_positive` / `ignored` / `disable` | 人工 |
| `note` | TEXT | ❌ | NULL | 用户备注 | 人工 |
| `created_at` | INTEGER | ✅ | — | 反馈时间 | 系统 |

**索引**：
- `idx_rule_feedback_rule (rule_id, created_at DESC)` — 规则反馈历史
- `idx_rule_feedback_member (member_id, created_at DESC)` — 成员反馈历史

**关键约束**：
- `feedback` 必为 4 选 1
- 反馈只能由 admin 或 fire 时涉及的成员给出（应用层校验）
- 反馈**不可撤销**——v2.19 行为：admin 可手动调 `rule.confidence_base` 撤回效果
- 反馈数据用于 v2.20 训练"规则可信度 ML 模型"（v2.19 不做）

---

## 22. 规则引擎表与 §5.0b ER 的关系

```
rules ──┬── 1:N ──> rule_state                (1 条规则 1 个状态)
        ├── 1:N ──> rule_audit_log             (1 条规则 N 次审计)
        └── 1:N ──> rule_feedback              (1 条规则 N 次反馈)

所有表 ──> household_id (FK 隐式，应用层隔离 §36)
```

**ER 图位置**：ARCHITECTURE.md §5.0b 后续修订需新增"规则引擎" 4 张表；v2.19 已在新章节 §53.6.3 给出完整 SQL，便于后续迁移脚本生成。

---

## 23. 迁移脚本（v2.19 第 4 批次）

**v2.19 审计 B 修复**：v2.10-v2.18 期间的 schema 变更通过以下脚本占位（占位不代表有真实 schema 变更，仅补足 version 链路）：

| 脚本 | 升级到 | 关联版本 |
|------|--------|---------|
| `001_init.sql` | 0.1.0 | v1 初版 |
| `002_*.sql` | 0.5.0 | v2.10 |
| `003_*.sql` | 0.6.0 | v2.16 + v2.18（占位；本期不引入 schema 变更，version 推进到 0.6.0） |
| `004_rules_engine.sql` | 0.7.0 | v2.19（**新增**：4 张规则表） |

```sql
-- migrations/003_placeholder_v2_16_v2_18.sql
-- v2.16 + v2.18 期间仅字段调整（capabilities 加 domain / irreversibility_tier / firmware_state 等），
-- 不新增/删除表。version 推进到 0.6.0 占位，避免 v2.19 一次跳号。
UPDATE schema_meta SET value = '0.6.0' WHERE key = 'version';
```

```sql
-- migrations/004_rules_engine.sql
CREATE TABLE rules (
  id TEXT PRIMARY KEY,
  household_id INTEGER NOT NULL,
  description TEXT NOT NULL,
  yaml_body TEXT NOT NULL,
  confidence_base REAL DEFAULT 0.7,
  enabled INTEGER DEFAULT 1,
  archived_at INTEGER,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  author_type TEXT NOT NULL,
  author_id INTEGER,
  validated_by INTEGER,
  category TEXT,
  severity TEXT DEFAULT 'care',
  version INTEGER DEFAULT 1
);

CREATE INDEX idx_rules_household ON rules(household_id) WHERE archived_at IS NULL;
CREATE INDEX idx_rules_author ON rules(author_type, author_id);
CREATE INDEX idx_rules_severity ON rules(household_id, severity);

CREATE TABLE rule_state (
  rule_id TEXT PRIMARY KEY,
  household_id INTEGER NOT NULL,
  state TEXT NOT NULL DEFAULT 'cold_start',
  last_fire_at INTEGER,
  last_eval_at INTEGER,
  cooldown_until INTEGER,
  true_positive_count INTEGER DEFAULT 0,
  false_positive_count INTEGER DEFAULT 0,
  updated_at INTEGER NOT NULL,
  CHECK (state IN ('disabled','cold_start','armed','firing','cooldown'))
);

CREATE INDEX idx_rule_state_household ON rule_state(household_id);
CREATE INDEX idx_rule_state_cooldown ON rule_state(cooldown_until) WHERE state='cooldown';

CREATE TABLE rule_audit_log (
  id INTEGER PRIMARY KEY,
  rule_id TEXT NOT NULL,
  household_id INTEGER NOT NULL,
  fired_at INTEGER NOT NULL,
  finished_at INTEGER,
  kind TEXT NOT NULL,
  confidence REAL,
  matched_predicates TEXT,
  evidence_snapshot TEXT,
  detail TEXT,
  ack_at INTEGER,
  ack_by INTEGER
);

CREATE INDEX idx_rule_audit_rule ON rule_audit_log(rule_id, fired_at DESC);
CREATE INDEX idx_rule_audit_household ON rule_audit_log(household_id, fired_at DESC);
CREATE INDEX idx_rule_audit_kind ON rule_audit_log(household_id, kind, fired_at DESC);

CREATE TABLE rule_feedback (
  id INTEGER PRIMARY KEY,
  rule_id TEXT NOT NULL,
  fire_id INTEGER NOT NULL,
  household_id INTEGER NOT NULL,
  member_id INTEGER NOT NULL,
  feedback TEXT NOT NULL,
  note TEXT,
  created_at INTEGER NOT NULL,
  CHECK (feedback IN ('true_positive','false_positive','ignored','disable'))
);

CREATE INDEX idx_rule_feedback_rule ON rule_feedback(rule_id, created_at DESC);
CREATE INDEX idx_rule_feedback_member ON rule_feedback(member_id, created_at DESC);

-- 升级 schema_meta
UPDATE schema_meta SET value = '0.7.0' WHERE key = 'version';  -- v2.19 + 规则引擎
```

---

## 24. 文档变更日志

- v2.19：新增 §18-§21 规则引擎 4 张表 + §22 ER 关系 + §23 迁移脚本
- v2.18：§17 events 表 + chats/channels 表变更
- v2.10：§1-§16 完整字段定义建立
- v2.7：§14-§16 增加服务代办 + 家务领域

---

## 25. cameras（v0.2 §54 视觉管线新增）

摄像头注册表。每台摄像头一个 row。

| 列 | 类型 | 非空 | 默认 | 用途 | 来源 |
|----|------|-----|------|------|------|
| `id` | TEXT PK | ✅ | — | 内部 ID（如 `cam_porch`） | 人工 / ONVIF 发现 |
| `household_id` | INTEGER | ✅ | 1 | 多家庭隔离（§36 强制） | 系统 |
| `name` | TEXT | ✅ | — | 用户友好名（"门口"） | 人工 |
| `rtsp_url` | TEXT | ✅ | — | rtsp://user:pass@ip:554/... | 人工 / ONVIF |
| `location` | TEXT | ❌ | NULL | 房间（客厅/门口/厨房） | 人工 |
| `capabilities` | TEXT (JSON) | ✅ | `{}` | 能力声明：`{person, face, fall, fire, cry, package}` | 人工（v0.2）；自动（v0.3） |
| `enabled` | INTEGER | ❌ | 1 | 启用状态 | 人工 |
| `last_seen_at` | INTEGER | ❌ | NULL | 最近一次拉流成功时间 | 系统 |
| `created_at` | INTEGER | ✅ | now | 创建时间 | 系统 |

**索引**：
- `idx_cameras_household (household_id)` — 多家庭隔离

**关键约束**：
- `rtsp_url` 凭证 v0.3+ 加密存储；v0.2 暂用 .env 明文
- 必须选 ONVIF/RTSP 协议（§54.2.1）
- `capabilities` 受限枚举：v0.2 列 7 种（motion / person / pose / face / fire / cry / package）

---

## 26. vision_events（v0.2 §54 视觉管线新增）

视觉事件流。每次检测器输出 → 一条 row。

| 列 | 类型 | 非空 | 默认 | 用途 | 来源 |
|----|------|-----|------|------|------|
| `id` | INTEGER PK | ✅ | — | 自增 | 系统 |
| `camera_id` | TEXT | ✅ | — | 关联 cameras.id | 系统 |
| `household_id` | INTEGER | ✅ | 1 | 多家庭隔离 | 系统 |
| `kind` | TEXT | ✅ | — | `motion`/`person`/`face_recognized`/`fall_detected`/`fire_detected`/`cry_detected`/`stranger`/`package` | 系统 |
| `confidence` | REAL | ❌ | NULL | 检测器置信度 [0.0-1.0] | 系统 |
| `bbox` | TEXT (JSON) | ❌ | NULL | 归一化坐标 `{x, y, w, h}` | 系统 |
| `attributes` | TEXT (JSON) | ❌ | NULL | 额外属性（如人脸 ID、声音分贝） | 系统 |
| `snapshot_path` | TEXT | ❌ | NULL | 截图本地路径（仅 fire 时保留） | 系统 |
| `started_at` | INTEGER | ✅ | — | 事件开始时间 | 系统 |
| `ended_at` | INTEGER | ❌ | NULL | 事件结束时间（持续事件） | 系统 |
| `ts` | INTEGER | ✅ | now | 写入时间 | 系统 |

**索引**：
- `idx_vision_events_camera (camera_id, ts DESC)` — 单摄像头历史
- `idx_vision_events_household (household_id, ts DESC)` — 多家庭 + 时间
- `idx_vision_events_kind (household_id, kind, ts DESC)` — 按种类查询

**关键约束**：
- 30 天自动清理（§54.8.2 原始视频不持久化）
- §43 GDPR 兼容：删成员 / 删摄像头 → 关联 vision_events 立即清理
- `snapshot_path` 文件系统同步清理

**与 events 表关系**：
- `events`（设备事件）来源：米家云 / miio，**单点**
- `vision_events`（视觉事件）来源：摄像头本地推理，**时段**
- 两者**不合并**（结构差异大），但 §53 规则引擎统一消费

---

## 27. 视觉管线 ER 关系（v0.2）

```
cameras (1) ──< (N) vision_events
                │
                ↓
        §53 规则引擎（sensor.vision.kind 谓词）
                │
                ↓
        §52 通知路由
```

**§36.6 多家庭隔离白名单修订**（v0.2）：
- `cameras` 加入 DIRECT_TABLES
- `vision_events` 加入 DIRECT_TABLES

---

## 28. 视觉管线迁移脚本（v0.2 第 5 批次）

```sql
-- migrations/005_vision_pipeline.sql
CREATE TABLE cameras (
  id TEXT PRIMARY KEY,
  household_id INTEGER NOT NULL DEFAULT 1,
  name TEXT NOT NULL,
  rtsp_url TEXT NOT NULL,
  location TEXT,
  capabilities TEXT NOT NULL DEFAULT '{}',
  enabled INTEGER DEFAULT 1,
  last_seen_at INTEGER,
  created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

CREATE INDEX idx_cameras_household ON cameras(household_id);

CREATE TABLE vision_events (
  id INTEGER PRIMARY KEY,
  camera_id TEXT NOT NULL,
  household_id INTEGER NOT NULL DEFAULT 1,
  kind TEXT NOT NULL,
  confidence REAL,
  bbox TEXT,
  attributes TEXT,
  snapshot_path TEXT,
  started_at INTEGER NOT NULL,
  ended_at INTEGER,
  ts INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

CREATE INDEX idx_vision_events_camera ON vision_events(camera_id, ts DESC);
CREATE INDEX idx_vision_events_household ON vision_events(household_id, ts DESC);
CREATE INDEX idx_vision_events_kind ON vision_events(household_id, kind, ts DESC);

-- 升级 schema_meta
UPDATE schema_meta SET value = '0.8.0' WHERE key = 'version';
```

---

## 29. v0.2 文档变更日志

- v0.2：§25 cameras + §26 vision_events + §27 ER + §28 迁移脚本
