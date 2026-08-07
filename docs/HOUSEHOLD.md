# 家务领域（Household）

> **同步状态（2026-08-07）**：本文档已纳入整体同步；与当前实现的差异以 [ARCHITECTURE.md](../ARCHITECTURE.md) 状态表和 `tests/` 为准。


> ARCHITECTURE.md §22 的工程级领域模型。本文件给到表的完整字段、隐私分级、P1 最小可行。

---

## 1. 领域全景

| 领域 | 进 P1 | 说明 |
|------|------|------|
| `household.items`（家居物品） | ✅ | 默认开启 |
| `household.calendar`（家事日历） | ✅ | 默认开启 |
| `household.health`（健康档案） | ❌ | 显式开启；P2+ |
| `household.finance`（家庭账本） | ❌ | 显式开启；P2+ |
| `household.relations`（关系图） | ❌ | P2 |
| `household.pets`（宠物） | ❌ | P3+ |
| `household.vehicles`（车辆） | ❌ | P3+ |

管家一次只看一类领域，每类有独立数据模型 + 独立 API + 独立 PWA 入口。

## 2. household.items（家居物品）

### 2.1 主表与事件表

```sql
CREATE TABLE household_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,                -- 鸡蛋 / 阿莫西林 / 充电宝
  category TEXT NOT NULL,             -- food / medicine / electronic / clothing / other
  location TEXT,                      -- 冰箱 / 药箱 / 车库 / 客厅
  quantity REAL,                      -- 6 / 2 (盒) / 1
  unit TEXT,                          -- 个 / 盒 / 升
  brand TEXT,
  expires_at TEXT,                    -- UTC ISO8601
  source TEXT NOT NULL,               -- manual / device / scan / conversation
  owner_member_id INT,                -- 谁负责（默认 nullable = 共享）
  notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  archived_at TEXT                    -- 用完或扔掉不删，只归档
);

CREATE INDEX idx_items_category ON household_items(category);
CREATE INDEX idx_items_expires_at ON household_items(expires_at);
CREATE INDEX idx_items_owner ON household_items(owner_member_id);

CREATE TABLE household_item_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id INT NOT NULL,
  event_type TEXT NOT NULL,           -- added / used / expired / discarded / restocked
  delta_quantity REAL,                -- 变化数量（消耗为负）
  ts TEXT NOT NULL,
  member_id INT,                      -- 谁触发的
  source TEXT,                        -- manual / agent / device
  detail TEXT                         -- JSON
);
```

### 2.2 P1 行为

**录入路径**（三种方式互备）：
1. PWA 扫条码（camera + ZXing）
2. PWA 搜名字（auto-complete）
3. 与管家对话："管家，我买了 6 颗鸡蛋放冰箱，6 月到期" → agent NLU 解析写入

**过期告警**：
- 调度每 6 小时跑：检查 `expires_at <= now + 3 days AND expires_at > now AND archived_at IS NULL`
- 命中 → 写 alerts（标题"X 即将过期"，WARNING 级别）
- 真过期：自动标 `archived_at = now` + 不计入活跃

**消耗更新**：
- PWA 长按物品 → "消耗 1"
- 与管家对话："管家我们早上吃了 2 颗鸡蛋" → 自动扣减
- 冰箱传感器（后续）：自动根据开门/关门推断（避免误扣）

### 2.3 接入第三方（v2.7 后期）

- 京东/天猫 API：在指定品类定期爬用户购买历史 → 自动归入（用户授权）
- 食材识别图像模型：拍照识别食物，写入 items（隐私敏感，需显式开启）

## 3. household.calendar（家事日历）

### 3.1 主表 + 实例表

```sql
CREATE TABLE household_calendar (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  kind TEXT NOT NULL,                  -- bill / pickup / birthday / medical / maintenance / social / reminder
  at TEXT NOT NULL,                    -- UTC ISO8601（首次发生时间）
  recurrence_rrule TEXT,               -- iCalendar RRULE（每周一/每月 25/每年 X 月 X 日）
  end_at TEXT,                         -- 终止时间
  owner_member_ids TEXT,               -- JSON 数组，谁相关
  related_devices TEXT,                -- JSON 数组（设备 id，与 §5.0b devices.id 解绑）
  reminder_minutes_before TEXT,        -- JSON 数组，如 [60, 1440, 10080] 表示提前 1h/1d/1w
  notes TEXT,
  source TEXT NOT NULL,                -- manual / conversation / service_adapter
  enabled INTEGER DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE household_calendar_occurrences (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  calendar_id INT NOT NULL,
  occurrence_at TEXT NOT NULL,         -- 该实例的时间
  status TEXT NOT NULL DEFAULT 'pending',  -- pending / reminded / done / skipped / missed
  ack_by INT,
  ack_at TEXT,
  notes TEXT
);

CREATE INDEX idx_calendar_at ON household_calendar(at);
CREATE INDEX idx_occurrences_at ON household_calendar_occurrences(occurrence_at, status);
```

### 3.2 P1 行为

**录入**：
- PWA "+" 弹窗：选日期 + 时间 + 类型 + 重复规则
- 与管家对话："管家，下周三下午 3 点接娃放学" → 自动解析写入

**重复展开**：每 6 小时跑一次（与 items 同时），把未来 30 天内的发生展开到 `occurrences`（幂等）。

**提醒推送**：
- occurrences `occurrence_at - reminder_minutes_before` 到期 → 推送给 owner_member_ids 中的成人
- 通知渠道：默认 PWA + 所有已配对渠道
- 推送内容："🚸 接娃放学 1 小时前"
- 家庭共同事件：用家庭聚合 channel（不指定成员）

**完成/跳过**：
- PWA 长按事件 → "完成" / "跳过（本周）/ 全部跳过"
- 与管家对话："管家娃已经接到了" → 自动标 done

### 3.3 与设备关联

某些家事可关联设备触发条件（如"出门前检查窗户关没"），但**领域独立**：calendar 不直接管设备，规则通过 §15 场景表达：

```yaml
# scenes.yaml 引用
- name: 检查窗户
  trigger:
    event: calendar.occurrence
    calendar_id: 123
    when: minutes_before == 30
  steps:
    - { check: 所有窗户, action: 提醒 }
```

## 4. household.health（健康档案，P2+，预留架构）

> **不实现具体功能，但留好接口**。健康数据高度敏感，进了隐私红线。

### 4.1 设计原则

1. **默认不启用**——管理员显式开关
2. **不离开本地**——所有 health_* 表数据不参与 §5.11 redactor 流程的上云摘要
3. **加密存储**——沿用 §RELIABILITY §5.1b SQLite 加密
4. **删除不留底**——成员可一键清除自己全部健康数据（GDPR-style）

### 4.2 数据模型（按需实现）

```sql
CREATE TABLE household_health_members (
  member_id INT PRIMARY KEY,
  birth_year INT,
  blood_type TEXT,
  allergies TEXT,                     -- JSON ["花生", "海鲜"]
  chronic_conditions TEXT,            -- JSON ["高血压", "II 型糖尿病"]
  emergency_contact TEXT              -- JSON {name, phone, relation}
);

CREATE TABLE household_health_metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  member_id INT NOT NULL,
  kind TEXT NOT NULL,                 -- bp / glucose / weight / sleep_hours / steps
  value REAL,
  unit TEXT,
  ts TEXT NOT NULL,
  source TEXT                         -- manual / wearable
);
```

## 5. household.finance（家庭账本，P2+，预留架构）

### 5.1 设计原则

1. 默认不启用
2. 不上云（除非用户显式开启"分摊给会计师"功能）
3. 不连银行 API 做自动入库（避免合规风险）
4. 录入以手动 + 截屏 OCR（用户拍照）为主

### 5.2 表骨架（按需实现）

```sql
CREATE TABLE household_finance_entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  amount REAL NOT NULL,
  direction TEXT NOT NULL,            -- income / expense / transfer
  category TEXT,                      -- 餐饮 / 水电 / 教育 / 医疗
  account TEXT,                       -- 现金 / 微信 / 银行卡
  merchant TEXT,
  member_id INT,                      -- 谁花的
  source TEXT,                        -- manual / ocr / bank_api_opt_in
  notes TEXT,
  reconciled INTEGER DEFAULT 0        -- 是否已对账
);
```

## 6. household.relations（关系图，P2）

```sql
CREATE TABLE household_relations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  from_member_id INT NOT NULL,
  to_name TEXT NOT NULL,              -- 不是成员的也允许（如朋友/外婆/继父）
  to_member_id INT,                   -- 如果是已知成员
  relation TEXT NOT NULL,             -- parent / child / spouse / sibling / grandparent / friend / pet
  notes TEXT
);
```

管家用这个图：
- 推送"奶奶"生日提醒（你知道奶奶是谁的妈）
- 看见"继父"在场时主动告知"今天有两家人"
- 校准称呼（"小明的爸爸"≠ "小明的爷爷"）

## 7. 数据隔离与 RBAC

| 数据类别 | admin | adult | child | guest |
|---------|-------|-------|-------|-------|
| 物品（公共） | 全 | 全 | 受限 | ❌ |
| 物品（自己 owner） | ✅ 编辑 | ✅ 编辑 | ✅ 查看 | ❌ |
| 日历（参与成员） | ✅ | ✅ | 部分 | ❌ |
| 日历（自己创建） | 全 | 全 | 全 | ❌ |
| 健康（自己） | ✅ 编辑 | ✅ 编辑 | ❌ | ❌ |
| 健康（他人） | 仅看紧急 | 仅看紧急 | ❌ | ❌ |
| 账本 | ✅ | ✅ | ❌ | ❌ |
| 关系图 | ✅ 编辑 | 受限 | ❌ | ❌ |

## 8. 对外接口设计

PWA "家庭账本"区（PWA 七大区扩展）：

| 子页 | 路径 |
|------|------|
| 物品库 | `/household/items` |
| 物品详情 | `/household/items/{id}` |
| 加物品 | `/household/items/new` |
| 家事日历 | `/household/calendar` |
| 日历详情 | `/household/calendar/{id}` |
| 健康档案 | `/household/health`（默认灰） |
| 家庭账本 | `/household/finance`（默认灰） |
| 关系图 | `/household/relations` |

## 9. 隐私红线（再次强调）

| 类别 | 上云 | 默认状态 | 加密 | 二次确认 |
|------|------|---------|------|---------|
| 物品 | 摘要 | 开 | 可选 | 无 |
| 日历 | 摘要 | 开 | 可选 | 无 |
| 健康 | 仅本地 | 关闭 | 必选 | 启用时需 adult+ |
| 账本 | 仅本地 | 关闭 | 必选 | 启用时需 admin |
| 关系图 | 摘要 | 开 | 可选 | 无 |

**关键不变式**：**健康/账本即使本地也加密**，因为 §RELIABILITY §5.1b 的全局 SQLite 加密已经保护了。

## 10. 实现位置

```
myhome_agent/household/
├── __init__.py
├── base.py          # 通用基类（每个领域继承）
├── items.py         # 家务物品领域
├── calendar.py      # 家事日历领域
├── health.py        # 健康领域（按需启用）
├── finance.py       # 账本领域
├── relations.py     # 关系图领域
├── recurring.py     # 重复规则展开
├── guard.py         # 领域数据访问控制（继承 §14 RBAC + 自身领域规则）
└── privacy.py       # 上云摘要脱敏（继承 §5.11 + 领域特化）

tests/household/
├── test_items.py
├── test_calendar_recurrence.py
├── test_calendar_reminder.py
└── ...

web/pages/household/  # PWA 七个领域子页面
├── items.js
├── calendar.js
├── health.js  （默认禁用）
├── finance.js  （默认禁用）
└── relations.js
```
