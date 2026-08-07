# 规则引擎 DSL 与示例库（v2.19 §53 配套）

> **同步状态（2026-08-07）**：本文档已纳入整体同步；与当前实现的差异以 [ARCHITECTURE.md](../ARCHITECTURE.md) 状态表和 `tests/` 为准。


> ARCHITECTURE.md §53 给的是架构规则与执行模型；本文件是**工程手册**——给开发者 / 高级用户 / 医生 / 家庭成员编写规则的完整指南。
>
> **阅读路径**：
> - 想写规则的家属 → §1 概念 → §2 DSL 速查 → §3 系统预设 → §4 复制改写
> - 想扩展 DSL 的开发者 → §5 谓词实现 → §6 evaluator 架构 → §7 自定义谓词
> - LLM 自动生成规则 → §8 提示词模板 → §9 校验流程
> - 调试误报 → §10 常见误报模式 → §11 调参技巧

---

## 1. 规则是什么？能做什么？

### 1.1 一句话定义

**规则 = 条件 + 动作 + 置信度**。当家庭的多传感器信号联合满足条件时，规则触发执行动作，并按置信度决定是否需要人工确认。

### 1.2 规则 vs 场景 vs 通知

| 概念 | 触发 | 输出 | 表达力 |
|------|------|------|--------|
| **规则** | 多信号状态 | 判定 + 升级 + 通知 | 中（YAML 谓词） |
| **场景**（§42） | 单一事件 / cron / 手动 | 设备动作序列 | 高（步骤序列） |
| **通知**（§52） | 任何来源 | 渠道分发 | 路由策略 |

**协作关系**：
```
[传感器] → 规则引擎判定 → 触发场景编排 → 走通知路由 → 送达用户
                  ↓
            误报闭环（用户反馈）
```

### 1.3 谁能写规则？

| 用户 | 权限 | 入口 |
|------|------|------|
| 系统开发者 | 创建系统预设 | 代码仓库 |
| 医生 | 创建建议（需 admin 审） | PWA 高级设置 |
| 家庭 admin | 创建规则 | PWA 规则编辑器 |
| 家庭 caregiver | 创建规则 | PWA 规则编辑器 |
| LLM | 生成建议（必须人工确认） | 对话中提议 |

**关键约束**（§53.6.2）：
- LLM 永远不能直接启用规则
- 删除规则不可逆（v2.19：软删除，可恢复）
- 任何规则变更进 `rule_audit_log`

---

## 2. DSL 速查（4 段 YAML）

### 2.1 最小规则

```yaml
id: 客厅没人自动关灯
description: 客厅无人 10 分钟自动关灯
when:
  all:
    - sensor.motion.living_room.duration_minutes > 10
    - sensor.motion.living_room.person_count == 0
then:
  - execute_scene: {scene_id: "close_living_room_lights"}
```

### 2.2 完整 7 段结构

```yaml
id: <kebab-case>                    # 唯一标识（必填）
description: <一句话>              # 描述（必填）
when: <predicate>                  # 触发条件（必填）
then: <actions>                    # 动作（必填）
confidence_base: 0.7                # 基础置信度（默认 0.7）
cooldown: 3600                      # 抑制再触发秒数（默认 3600）
window: 1min                        # 窗口粒度（默认 1min）
feedback: <feedback_spec>          # 反馈机制（默认开启）
meta: <metadata>                    # 元数据（可选）
```

### 2.3 谓词逻辑（all / any / none）

```yaml
when:
  all:                    # 全部满足
    - pred1
    - pred2
  any:                    # 任一满足
    - pred3
    - pred4
  none:                   # 全不满足
    - pred5
```

**规则**：嵌套 ≤ 4 层；不允许 5 层以上。

### 2.4 谓词字典（v2.19 起步 23 个）

#### 数值类（6）

| 谓词 | 语法 | 例子 |
|------|------|------|
| `eq` | `field == value` | `sensor.temp == 26` |
| `ne` | `field != value` | `sensor.online != false` |
| `gt` | `field > value` | `sensor.away_minutes > 30` |
| `gte` | `field >= value` | `sensor.rssi >= -70` |
| `lt` | `field < value` | `sensor.flow < 5.0` |
| `lte` | `field <= value` | `sensor.duration <= 60` |
| `between` | `value between [a, b]` | `sensor.temp between [20, 26]` |

#### 时序类（3）

| 谓词 | 语法 | 例子 |
|------|------|------|
| `away_minutes` | `sensor.duration > N` | `bed_pressure.away_minutes > 30` |
| `since_minutes` | `sensor.changed_since > N` | `door.last_open_since > 60` |
| `duration_minutes` | `sensor.in_state_minutes > N` | `motion.in_state_minutes > 45` |

#### 时窗类（3）

| 谓词 | 语法 | 例子 |
|------|------|------|
| `time.in_window` | `time.in_window: ["22:00", "06:00"]` | 夜间 |
| `weekday.in` | `weekday.in: ["mon", "tue", ...]` | 工作日 |
| `date.in` | `date.in: ["2026-08-01", "2026-08-07"]` | 日期范围 |

#### 成员类（3）

| 谓词 | 语法 | 例子 |
|------|------|------|
| `member.is_alone` | `member.is_alone_at_home: true` | 独居 |
| `member.role` | `member.role == "elder"` | 老人 |
| `member.count` | `member.count_at_home > N` | 在家人数 |

#### 传感器类（3）

| 谓词 | 语法 | 例子 |
|------|------|------|
| `sensor.fresh` | `sensor.fresh(<=60s): true` | 数据新鲜 |
| `sensor.value` | `sensor.value == "on"` | 当前值 |
| `sensor.changed` | `sensor.changed(now-5min): true` | 最近变化 |

#### 家庭上下文（3）

| 谓词 | 语法 | 例子 |
|------|------|------|
| `household.in_mode` | `household.in_mode: "night"` | 家庭模式 |
| `weather.condition` | `weather.condition: "rain"` | 天气 |
| `calendar.has_event` | `calendar.has_event("school_day"): true` | 日历事件 |

#### 组合子（3 项，与 §2.3 顶层结构同源）

> 注：all/any/none 在 §2.3 是 DSL 顶层 when 字段的子结构，在本表也作为谓词可嵌套使用。两者是同一机制的不同入口，不冲突。

| 谓词 | 语法 | 例子 |
|------|------|------|
| `all` | `all: [pred1, pred2]` | 全部满足 |
| `any` | `any: [pred1, pred2]` | 任一满足 |
| `none` | `none: [pred1]` | 全不满足 |

### 2.5 动作字典

| 动作 | 用途 | 关键参数 |
|------|------|---------|
| `escalate` | 走 §52 通知升级链 | ladder, timeout_per_step, level, ack_required |
| `notify` | 单次通知（不升级） | to, level, template |
| `record_evidence` | 记录证据快照 | true |
| `capture_snapshot` | 拉摄像头快照 | cameras, ttl |
| `execute_scene` | 调 §42 场景 | scene_id |
| `suggestions` | 推送建议文案 | array |
| `log` | 仅记录不通知 | level, message |

**禁止动作**：任何 `delete_*` / `reset_*` / `modify_*` —— 必须经 §5.3 高危确认。

---

## 3. 系统预设规则（v2.19 全集 16 条：v0.1 5 条 P0 + v0.2+ 11 条 P1）

> v2.19 修订（审计 A 问题 8 修复）：标题"v2.19 起步 16 条"已删，避免与 §53.10.1 v0.1 5 条 P0 口径混淆。**v0.1 实际落地 5 条 P0**；v0.2 补 11 条 P1。每条规则标注 v0.1 / v0.2 状态。

### 3.1 elderly_fall_suspect_v1（老人起夜异常）【v0.1 P0】

```yaml
id: elderly_fall_suspect_v1
description: 独居老人夜间起夜后长时间未归床，疑似摔倒或突发不适
severity: safety
category: elderly_care
confidence_base: 0.7
window: 1min
cooldown: 3600
when:
  all:
    - sensor.bed_pressure.away_minutes > 30
    - sensor.motion.living_room.present == true
    - sensor.motion.living_room.duration_minutes > 30
    - time.in_window: ["22:00", "06:00"]
    - member.is_alone_at_home: true
    - sensor.fresh(<=60s, "bed_pressure"): true
    - sensor.fresh(<=60s, "motion.living_room"): true
then:
  - escalate:
      ladder: [primary_caregiver, secondary_caregiver, neighbor, 120]
      timeout_per_step: 15min
      ack_required: true
  - record_evidence: true
  - capture_snapshot:
      cameras: ["living_room", "hallway"]
      ttl: 30min
  - suggestions:
      - "回看客厅监控"
      - "打电话给老人"
      - "15 分钟无应答 → 通知邻居上门"
```

### 3.2 water_microleak_night_v1（深夜微量漏水）

```yaml
id: water_microleak_night_v1
description: 凌晨无人时段水表持续小流量，疑似水管/水龙头微量泄漏
severity: care
category: water_safety
confidence_base: 0.85
window: 5min
cooldown: 7200
when:
  all:
    - sensor.water_meter.flow_l_per_hour > 0.5
    - sensor.water_meter.flow_l_per_hour < 5.0
    - sensor.water_meter.duration_minutes > 60
    - member.is_alone_at_home: false
    - time.in_window: ["02:00", "05:00"]
    - sensor.fresh(<=300s, "water_meter"): true
then:
  - escalate:
      ladder: [primary_caregiver]
      timeout_per_step: 30min
      level: care
  - record_evidence: true
  - suggestions:
      - "检查水槽 / 卫生间 / 洗衣机进水管"
      - "查看用水曲线截图"
```

### 3.3 child_school_pickup_v1（孩子放学未归）

```yaml
id: child_school_pickup_v1
description: 孩子放学时段到时未归，校门口 GPS 静止
severity: care
category: child_care
confidence_base: 0.6
window: 5min
cooldown: 1800
when:
  all:
    - sensor.front_door.lock.opened_30min == false
    - sensor.gps.child.school_zone_distance < 100
    - sensor.gps.child.duration_minutes > 30
    - time.in_window: ["16:30", "17:30"]
    - weekday.in: ["mon", "tue", "wed", "thu", "fri"]
    - calendar.has_event("school_day"): true
then:
  - notify:
      to: [primary_caregiver]
      level: care
      template: "孩子可能没接到人，已在校门口 {duration} 分钟"
  - suggestions:
      - "打电话给班主任"
      - "看看同学群有没有当天留堂通知"
```

### 3.4 stranger_porch_loiter_v1（陌生人门口徘徊）

```yaml
id: stranger_porch_loiter_v1
description: 门口摄像头检测到陌生人停留 >3 分钟，全家都在外
severity: safety
category: security
confidence_base: 0.75
window: 1min
cooldown: 1800
when:
  all:
    - sensor.camera.porch.person_count > 0
    - sensor.camera.porch.duration_minutes > 3
    - member.is_alone_at_home: false
    - any_family_at_home: false
    - sensor.front_door.lock.opened_10min == false
then:
  - escalate:
      ladder: [primary_caregiver]
      timeout_per_step: 5min
      level: safety
  - capture_snapshot:
      cameras: ["porch", "driveway"]
      ttl: 60min
  - record_evidence: true
```

### 3.5 elderly_no_activity_v1（老人无活动）

```yaml
id: elderly_no_activity_v1
description: 老人 12 小时无任何活动迹象
severity: safety
category: elderly_care
confidence_base: 0.65
window: 60min
cooldown: 7200
when:
  all:
    - sensor.motion.total_count_12h == 0
    - sensor.bed_pressure.last_change_ago > 720
    - sensor.water_meter.last_use_ago > 720
    - sensor.lock.last_open_ago > 720
    - member.role == "elder"
    - sensor.fresh(<=3600s, "motion"): true
then:
  - escalate:
      ladder: [primary_caregiver, secondary_caregiver]
      timeout_per_step: 30min
      level: safety
  - capture_snapshot:
      cameras: ["living_room", "kitchen"]
      ttl: 60min
  - suggestions:
      - "打电话给老人"
      - "查看所有摄像头"
```

### 3.6 ac_unusual_power_v1（空调异常耗电）

```yaml
id: ac_unusual_power_v1
description: 空调本周比上周同条件下耗电高 50% 以上，可能缺氟/老化
severity: care
category: appliance_health
confidence_base: 0.7
window: 60min
cooldown: 86400
when:
  all:
    - sensor.ac.power_watt > 1200
    - sensor.ac.power_watt_vs_last_week > 1.5
    - sensor.outdoor.temp < sensor.ac.target_temp
    - sensor.outdoor.temp > 15
then:
  - notify:
      to: [primary_caregiver]
      level: care
      template: "客厅空调本周比上周费电 {percent}%"
  - suggestions:
      - "检查空调滤网"
      - "考虑约维修（疑似缺氟）"
```

### 3.7 elderly_medication_miss_v1（老人漏吃药）

```yaml
id: elderly_medication_miss_v1
description: 老人该吃药时段未检测到智能药盒打开
severity: care
category: elderly_care
confidence_base: 0.6
window: 5min
cooldown: 3600
when:
  all:
    - sensor.pill_box.opened_30min == false
    - time.in_window: ["08:00", "09:00"]
    - weekday.in: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    - calendar.has_event("medication_morning"): true
then:
  - notify:
      to: [primary_caregiver, secondary_caregiver]
      level: care
      template: "老人今早 8 点没吃药"
  - execute_scene: {scene_id: "elderly_medication_reminder"}
```

### 3.8 dementia_wander_v1（痴呆走失预警）

```yaml
id: dementia_wander_v1
description: 痴呆老人独自离家（开门但没有家人陪同）
severity: safety
category: elderly_care
confidence_base: 0.9
window: 1min
cooldown: 1800
when:
  all:
    - sensor.front_door.lock.opened_5min == true
    - member.role == "elderly_dementia"
    - member.has_caregiver_at_home: false
    - time.in_window: ["00:00", "23:59"]
then:
  - escalate:
      ladder: [primary_caregiver, secondary_caregiver, 110]
      timeout_per_step: 5min
      level: safety
      sos_bypass: true
  - capture_snapshot:
      cameras: ["front_door", "porch"]
      ttl: 120min
  - suggestions:
      - "立即联系家属"
      - "查看实时定位"
```

### 3.9 water_leak_critical_v1（严重水浸）

```yaml
id: water_leak_critical_v1
description: 水浸传感器触发 + 持续流量
severity: safety
category: water_safety
confidence_base: 0.95
window: 1min
cooldown: 0
when:
  all:
    - sensor.water_leak_sensor.triggered == true
    - sensor.water_meter.flow_l_per_hour > 10
    - sensor.fresh(<=30s, "water_leak_sensor"): true
then:
  - escalate:
      ladder: [primary_caregiver, neighbor]
      timeout_per_step: 5min
      level: safety
  - execute_scene: {scene_id: "emergency_water_shutoff"}
  - suggestions:
      - "立即回家检查"
      - "联系物业"
```

### 3.10 smoke_detector_v1（烟雾报警）

```yaml
id: smoke_detector_v1
description: 烟雾传感器触发 + 温度异常
severity: safety
category: fire_safety
confidence_base: 0.95
window: 1min
cooldown: 0
when:
  all:
    - sensor.smoke_detector.triggered == true
    - sensor.fresh(<=30s, "smoke_detector"): true
then:
  - escalate:
      ladder: [primary_caregiver, secondary_caregiver, 119]
      timeout_per_step: 5min
      level: safety
      sos_bypass: true
  - execute_scene: {scene_id: "emergency_fire_response"}
  - capture_snapshot:
      cameras: ["kitchen", "hallway"]
      ttl: 120min
```

### 3.11 gas_leak_v1（燃气泄漏）

```yaml
id: gas_leak_v1
description: 燃气传感器触发
severity: safety
category: fire_safety
confidence_base: 0.95
window: 1min
cooldown: 0
when:
  all:
    - sensor.gas_detector.triggered == true
    - sensor.fresh(<=30s, "gas_detector"): true
then:
  - escalate:
      ladder: [primary_caregiver, 119]
      timeout_per_step: 5min
      level: safety
      sos_bypass: true
  - execute_scene: {scene_id: "emergency_gas_shutoff"}
```

### 3.12 package_at_door_v1（快递到门口）

```yaml
id: package_at_door_v1
description: 摄像头检测到门口有包裹 + 无人
severity: info
category: security
confidence_base: 0.7
window: 1min
cooldown: 1800
when:
  all:
    - sensor.camera.porch.detected("package"): true
    - any_family_at_home: false
    - sensor.front_door.lock.opened_5min == false
then:
  - notify:
      to: [primary_caregiver]
      level: info
      template: "门口有快递，全家不在家"
  - suggestions:
      - "30 分钟后还在 → 通知邻居代收"
```

### 3.13 baby_cry_v1（婴儿哭声）

```yaml
id: baby_cry_v1
description: 婴儿哭声持续 5 分钟无人抱起
severity: care
category: child_care
confidence_base: 0.7
window: 5min
cooldown: 1800
when:
  all:
    - sensor.baby_monitor.cry_detected == true
    - sensor.baby_monitor.cry_duration_minutes > 5
    - sensor.baby_monitor.parent_response == false
then:
  - notify:
      to: [primary_caregiver]
      level: care
      template: "宝宝哭 5 分钟没抱起"
  - suggestions:
      - "去儿童房看看"
```

### 3.14 power_outage_v1（断电）

```yaml
id: power_outage_v1
description: 全屋功率骤降至 0
severity: safety
category: infrastructure
confidence_base: 0.9
window: 1min
cooldown: 0
when:
  all:
    - sensor.power_total.watt < 5
    - sensor.power_total.watt_was_normal_5min_ago: true
    - sensor.fresh(<=30s, "power_total"): true
then:
  - escalate:
      ladder: [primary_caregiver]
      timeout_per_step: 5min
      level: safety
  - suggestions:
      - "检查电闸"
      - "冰箱食物可能受影响"
```

### 3.15 network_offline_v1（NAS 离线）

```yaml
id: network_offline_v1
description: NAS 上行链路断开
severity: info
category: infrastructure
confidence_base: 0.85
window: 1min
cooldown: 3600
when:
  all:
    - sensor.nas.ping_failed == true
    - sensor.nas.ping_failed_count >= 3
then:
  - notify:
      to: [admin]
      level: info
      template: "NAS 已离线 {duration} 分钟"
```

### 3.16 routine_anomaly_v1（习惯异常）

```yaml
id: routine_anomaly_v1
description: 某成员习惯时段（如起床）偏离基线 >2 小时
severity: care
category: lifestyle
confidence_base: 0.5
window: 60min
cooldown: 86400
when:
  all:
    - member.has_routine("morning_wake")
    - member.routine_deviation_minutes("morning_wake") > 120
    - member.is_alone_at_home: false
then:
  - notify:
      to: [primary_caregiver]
      level: care
      template: "{member.name} 今天比平时晚起 {deviation} 分钟"
```

### 3.17 stranger_porch_v2_vision（门口视觉陌生人）【v0.2 P1】

```yaml
id: stranger_porch_v2_vision
description: 门口摄像头视觉检测到陌生人 + 持续 >3 分钟（v0.2 视觉增强版）
severity: safety
category: security
confidence_base: 0.85
cooldown: 1800
window: 1min
when:
  all:
    - sensor.vision.kind: person
    - sensor.vision.camera.location: porch
    - sensor.vision.duration_minutes > 3
    - any_family_at_home: false
    - sensor.front_door.lock.opened_5min: false
then:
  - escalate:
      ladder: [primary_caregiver]
      level: safety
  - capture_snapshot:
      cameras: ["cam_porch"]
      ttl: 60min
  - record_evidence: true
```

**v0.2 视觉增强**：相比 v0.1 `stranger_porch_loiter_v1` 多了视觉证据（人形 + 持续时长）。可与运动传感器互证（双源验证）。

### 3.18 elderly_fall_v2_pose（老人跌倒视觉）【v0.2 P1】

```yaml
id: elderly_fall_v2_pose
description: 客厅摄像头 YOLO-pose 检测到老人跌倒姿态（v0.2 视觉增强版）
severity: safety
category: elderly_care
confidence_base: 0.9
cooldown: 1800
window: 1min
when:
  all:
    - sensor.vision.kind: fall_detected
    - sensor.vision.camera.location: 客厅
    - sensor.vision.confidence > 0.7
    - member.role: elder
then:
  - escalate:
      ladder: [primary_caregiver, secondary_caregiver, 120]
      level: safety
      sos_bypass: true
  - capture_snapshot:
      cameras: ["cam_living_room"]
      ttl: 120min
  - suggestions:
      - "立即回家或联系附近家人"
      - "15 分钟无响应 → 拨 120"
```

**v0.2 视觉增强**：YOLO-pose 检测老人跌倒姿态 + 老年人角色验证（避免误识别小孩摔倒）。**v0.1 `elderly_fall_suspect_v1` 靠床压+人体传感；v0.2 加视觉**——双源互证降误报。

### 3.19 smoke_visual_verify（烟雾视觉复核）【v0.2 P1】

```yaml
id: smoke_visual_verify
description: 烟雾传感器触发 + 厨房摄像头视觉复核（v0.2 视觉增强版）
severity: safety
category: fire_safety
confidence_base: 0.95
cooldown: 0
window: 1min
when:
  all:
    - sensor.smoke_detector.triggered: true
    - sensor.vision.kind: fire_detected
    - sensor.vision.camera.location: 厨房
    - sensor.vision.confidence > 0.5
then:
  - escalate:
      ladder: [primary_caregiver, 119]
      level: safety
      sos_bypass: true
  - capture_snapshot:
      cameras: ["cam_kitchen"]
      ttl: 120min
  - execute_scene: emergency_fire_response
```

**v0.2 视觉增强**：双源验证（烟雾传感器 + 视觉火焰）→ 误报率 < 1%。**v0.1 `smoke_detector_v1` 仅靠传感器**——炒菜的烟常误报。

---

## 3b. 视觉规则 16 条（v0.7 种子）

> v0.7 落地的视觉规则。**基于 §54 视觉管线 + §38.14 被守护者场景**。每条按 §53.2 DSL 规范。
> 引用视觉事件：vision.kind 来自 `vision/detectors.py`（person / fall_detected / fire_detected / smoke_detected / motion / animal / vehicle / package / cry_detected）。

### 3b.1 跌倒（v1-v3）

#### vision_fall_living_room_v1
```yaml
id: vision_fall_living_room_v1
description: 客厅摄像头检测到老人跌倒 + 持续 30 秒未起身
severity: safety
category: elderly_care
confidence_base: 0.85
cooldown: 3600
when:
  all:
    - vision.kind: fall_detected
    - vision.camera.location: 客厅
    - vision.confidence: ">= 0.7"
    - vision.duration_seconds: ">= 30"
    - member.role: elder
    - any_family_at_home: false
then:
  - escalate:
      ladder: [primary_caregiver, 120]
      level: safety
      sos_bypass: true
  - capture_snapshot:
      cameras: ["客厅"]
      ttl: 1800
```

#### vision_fall_bedroom_v2
```yaml
id: vision_fall_bedroom_v2
description: 卧室摄像头检测到老人跌倒（夜起场景）
severity: safety
category: elderly_care
confidence_base: 0.9
cooldown: 3600
when:
  all:
    - vision.kind: fall_detected
    - vision.camera.location: 卧室
    - vision.confidence: ">= 0.8"
    - time.in_window: ["22:00", "07:00"]
then:
  - escalate:
      ladder: [primary_caregiver, secondary_caregiver, 120]
      level: safety
      sos_bypass: true
```

#### vision_fall_bathroom_v3
```yaml
id: vision_fall_bathroom_v3
description: 卫生间跌倒（高风险区域，宁可误报不漏报）
severity: safety
category: elderly_care
confidence_base: 0.95
cooldown: 0
when:
  all:
    - vision.kind: fall_detected
    - vision.camera.location: 卫生间
    - vision.confidence: ">= 0.6"
then:
  - escalate:
      ladder: [primary_caregiver, 120]
      level: safety
      sos_bypass: true
```

### 3b.2 痴呆走失（v1-v3）

#### vision_dementia_outdoor_v1
```yaml
id: vision_dementia_outdoor_v1
description: 痴呆老人独自在户外（门口摄像头）
severity: safety
category: elderly_care
confidence_base: 0.9
cooldown: 1800
when:
  all:
    - vision.kind: person
    - vision.camera.location: 门口
    - member.role: elderly_dementia
    - member.has_caregiver_at_home: false
    - vision.person.identity_match: "< 0.5"
then:
  - escalate:
      ladder: [primary_caregiver, secondary_caregiver, 110]
      level: safety
      sos_bypass: true
  - capture_snapshot:
      cameras: ["门口", "客厅"]
      ttl: 3600
```

#### vision_dementia_door_open_v2
```yaml
id: vision_dementia_door_open_v2
description: 痴呆老人打开门 + 没有家人陪同
severity: safety
category: elderly_care
confidence_base: 0.9
cooldown: 1800
when:
  all:
    - sensor.front_door.lock.opened_5min: true
    - member.role: elderly_dementia
    - any_family_at_home: false
then:
  - escalate:
      ladder: [primary_caregiver, secondary_caregiver, 110]
      level: safety
      sos_bypass: true
```

#### vision_dementia_lost_outside_v3
```yaml
id: vision_dementia_lost_outside_v3
description: 痴呆老人走出家门 + GPS 显示在 500m 外
severity: safety
category: elderly_care
confidence_base: 0.95
cooldown: 0
when:
  all:
    - sensor.front_door.lock.opened_5min: true
    - sensor.gps.elderly.distance_home_m: ">= 500"
    - member.role: elderly_dementia
then:
  - escalate:
      ladder: [primary_caregiver, 110, 120]
      level: safety
      sos_bypass: true
```

### 3b.3 陌生人徘徊（v1-v2）

#### vision_stranger_porch_night_v1
```yaml
id: vision_stranger_porch_night_v1
description: 门口陌生人夜间徘徊
severity: care
category: security
confidence_base: 0.7
cooldown: 1800
when:
  all:
    - vision.kind: person
    - vision.camera.location: 门口
    - vision.person.identity_match: "< 0.3"
    - vision.duration_seconds: ">= 180"
    - time.in_window: ["22:00", "06:00"]
    - any_family_at_home: false
then:
  - escalate:
      ladder: [primary_caregiver]
      level: safety
  - capture_snapshot:
      cameras: ["门口"]
      ttl: 3600
```

#### vision_stranger_window_v2
```yaml
id: vision_stranger_window_v2
description: 阳台 / 后院 / 车库陌生人
severity: care
category: security
confidence_base: 0.75
cooldown: 1800
when:
  all:
    - vision.kind: person
    - vision.camera.location: ["阳台", "后院", "车库"]
    - vision.person.identity_match: "< 0.3"
    - vision.duration_seconds: ">= 120"
then:
  - escalate:
      ladder: [primary_caregiver]
      level: care
```

### 3b.4 火焰 / 烟雾复核（v1-v2）

#### vision_fire_verify_v1
```yaml
id: vision_fire_verify_v1
description: 烟雾传感器 + 视觉同时确认
severity: safety
category: fire_safety
confidence_base: 0.9
cooldown: 0
when:
  all:
    - sensor.smoke_detector.triggered: true
    - any:
        - vision.kind: fire_detected
        - vision.kind: smoke_detected
    - vision.camera.location: 厨房
then:
  - escalate:
      ladder: [primary_caregiver, 119]
      level: safety
      sos_bypass: true
```

#### vision_fire_false_alarm_v2
```yaml
id: vision_fire_false_alarm_v2
description: 烟雾传感器触发但视觉无火无烟（标记为误报候选）
severity: info
category: fire_safety
confidence_base: 0.85
cooldown: 3600
when:
  all:
    - sensor.smoke_detector.triggered: true
    - vision.kind: NOT IN [fire_detected, smoke_detected]
    - vision.camera.location: 厨房
    - vision.confidence: "< 0.3"
then:
  - notify:
      to: [admin]
      level: info
      template: "厨房烟雾报警，但视觉未检测到火/烟（疑似炒菜/蒸汽），请核查"
```

### 3b.5 慢病异常

#### vision_chronic_inactive_v1
```yaml
id: vision_chronic_inactive_v1
description: 慢病老人长时间无活动
severity: care
category: elderly_care
confidence_base: 0.7
cooldown: 7200
when:
  all:
    - member.role: elder
    - member.has_chronic_disease: true
    - vision.motion.rooms_active_count: "< 1"
    - vision.motion.duration_minutes: ">= 120"
then:
  - escalate:
      ladder: [primary_caregiver]
      level: care
  - capture_snapshot:
      cameras: ["客厅", "卧室"]
      ttl: 600
```

### 3b.6 失禁 / 久坐

#### vision_elderly_inactive_sofa_v1
```yaml
id: vision_elderly_inactive_sofa_v1
description: 老人坐沙发后无活动 3 小时
severity: care
category: elderly_care
confidence_base: 0.6
cooldown: 7200
when:
  all:
    - member.role: elder
    - vision.kind: person
    - vision.pose: seated
    - vision.pose.duration_minutes: ">= 180"
    - time.in_window: ["08:00", "22:00"]
then:
  - notify:
      to: [primary_caregiver]
      level: care
      template: "{member.name} 在客厅沙发已坐 3 小时，可能需要关注"
```

### 3b.7 婴儿哭

#### vision_baby_cry_v1
```yaml
id: vision_baby_cry_v1
description: 婴儿哭声持续 5 分钟没人抱起
severity: care
category: child_care
confidence_base: 0.7
cooldown: 1800
when:
  all:
    - vision.kind: cry_detected
    - vision.camera.location: 婴儿房
    - vision.cry.duration_seconds: ">= 300"
    - vision.parent_response: false
then:
  - notify:
      to: [primary_caregiver]
      level: care
      template: "宝宝哭 5 分钟没人抱起"
```

### 3b.8 包裹

#### vision_package_at_door_v1
```yaml
id: vision_package_at_door_v1
description: 门口检测到包裹 + 全家外出
severity: info
category: security
confidence_base: 0.7
cooldown: 1800
when:
  all:
    - vision.kind: package
    - vision.camera.location: 门口
    - any_family_at_home: false
then:
  - notify:
      to: [admin]
      level: info
      template: "门口有快递，全家不在家"
  - suggestions:
      - "30 分钟后还在 → 通知邻居代收"
```

### 3b.9 宠物识别

#### vision_pet_outdoor_v1
```yaml
id: vision_pet_outdoor_v1
description: 宠物独自在户外 5 分钟
severity: info
category: pet_safety
confidence_base: 0.8
cooldown: 1800
when:
  all:
    - vision.kind: animal
    - vision.animal.class: ["cat", "dog"]
    - vision.camera.location: ["门口", "后院"]
    - vision.animal.outdoor_minutes: ">= 5"
    - any_family_at_home: true
then:
  - notify:
      to: [admin]
      level: info
      template: "{animal.class} 已在户外 {outdoor_minutes} 分钟，要叫回来吗？"
```

### 3b.10 SOS 按钮 + 视觉联动

#### vision_sos_with_fall_v1
```yaml
id: vision_sos_with_fall_v1
description: SOS 按钮 + 视觉同时确认（双源验证）
severity: safety
category: elderly_care
confidence_base: 0.99
cooldown: 0
when:
  all:
    - sensor.sos_button.triggered: true
    - any:
        - vision.kind: fall_detected
        - vision.kind: person
    - vision.camera.location: ["卫生间", "卧室", "客厅"]
then:
  - escalate:
      ladder: [primary_caregiver, secondary_caregiver, 120]
      level: safety
      sos_bypass: true
  - capture_snapshot:
      cameras: ["所有"]
      ttl: 3600
```

### 3b.11 视觉规则使用注意

- **依赖 capabilities**：所有 vision.* 谓词依赖 `cameras.capabilities` 字段
- **设备能力变化**：capability 失效时规则自动 archived（§50 不变量）
- **误报控制**：所有 vision 规则必须经用户 7 天实测后启用
- **性能**：每条规则每 5s 扫一次，10 条 vision 规则 = 50ms/家（远低于 §1b SLO 200ms）
- **隐私**：snapshot 30 天清理（§54.6）

---

## 4. 复制改写示例（家属自配）

### 4.1 简化：只保留核心条件

```yaml
# 原版 elderly_fall_suspect_v1
when:
  all:
    - sensor.bed_pressure.away_minutes > 30
    - sensor.motion.living_room.duration_minutes > 30
    - time.in_window: ["22:00", "06:00"]
    - member.is_alone_at_home: true

# 简化版（只关心夜间 + 客厅有人）
id: simple_elderly_check_v1
description: 简化版老人异常检查
when:
  all:
    - sensor.motion.living_room.duration_minutes > 60
    - time.in_window: ["22:00", "06:00"]
```

### 4.2 收紧：误报太多时减少 cooldown

```yaml
# 原版 cooldown 3600 (1 小时不重复)
# 改后 cooldown 7200（2 小时不重复）
cooldown: 7200
```

### 4.3 加严：提高 confidence_base

```yaml
# 误报率高的规则 → 提高基础置信度
confidence_base: 0.85  # 原 0.7
```

### 4.4 并行：加多一个候补动作

```yaml
then:
  - escalate:
      ladder: [primary_caregiver]
  - log:
      level: info
      message: "规则 X 触发但未升级"
```

---

## 5. 谓词实现（开发者视角）

### 5.1 谓词抽象接口

```python
# myhome_agent/rules/evaluator.py
from abc import ABC, abstractmethod
from typing import Any

class Predicate(ABC):
    @abstractmethod
    def eval(self, context: EvalContext) -> bool:
        """Evaluate predicate against current state."""
        pass

    @abstractmethod
    def validate(self, yaml_node: Any) -> None:
        """Validate YAML structure at load time."""
        pass

class NumericPredicate(Predicate):
    """eq, ne, gt, gte, lt, lte, between"""
    pass

class TemporalPredicate(Predicate):
    """away_minutes, since_minutes, duration_minutes"""
    pass

class WindowPredicate(Predicate):
    """time.in_window, weekday.in, date.in"""
    pass
```

### 5.2 谓词注册表

```python
# myhome_agent/rules/registry.py
PREDICATE_REGISTRY = {
    'eq': NumericPredicate,
    'ne': NumericPredicate,
    'gt': NumericPredicate,
    'gte': NumericPredicate,
    'lt': NumericPredicate,
    'lte': NumericPredicate,
    'between': NumericPredicate,
    'away_minutes': TemporalPredicate,
    'since_minutes': TemporalPredicate,
    'duration_minutes': TemporalPredicate,
    'time.in_window': WindowPredicate,
    'weekday.in': WindowPredicate,
    'date.in': WindowPredicate,
    'member.is_alone': MemberPredicate,
    'member.role': MemberPredicate,
    'member.count': MemberPredicate,
    'sensor.fresh': SensorPredicate,
    'sensor.value': SensorPredicate,
    'sensor.changed': SensorPredicate,
    'household.in_mode': HouseContextPredicate,
    'weather.condition': WeatherPredicate,
    'calendar.has_event': CalendarPredicate,
    'all': LogicalPredicate,
    'any': LogicalPredicate,
    'none': LogicalPredicate,
}
```

### 5.3 评估上下文

```python
@dataclass
class EvalContext:
    household_id: int
    rule_id: str
    window: WindowData  # 1min/5min/60min 聚合
    now: datetime
    members_at_home: List[int]
    member_profiles: Dict[int, MemberProfile]
    weather: WeatherData
    calendar: CalendarData
```

### 5.4 谓词测评（CI 必须）

```python
# tests/rules/test_predicates.py
def test_gt_predicate():
    ctx = make_context({'sensor.temp': 30})
    pred = NumericPredicate('gt', field='sensor.temp', value=25)
    assert pred.eval(ctx) == True

def test_away_minutes_predicate():
    ctx = make_context({'bed_pressure': {'value': 0, 'changed_at': now() - 600}})
    pred = TemporalPredicate('away_minutes', field='bed_pressure', threshold=300)
    assert pred.eval(ctx) == True
```

---

## 6. Evaluator 架构

### 6.1 整体流程

```
YAML 规则
   ↓
[Load] → Pydantic schema 校验
   ↓
[Validate] → 谓词引用存在 + 嵌套 ≤ 4 层
   ↓
[Store] → rules 表
   ↓
[每 10s 扫描]
   ↓
[窗口聚合] → 1min/5min/60min/1day
   ↓
[谓词评估] → 命中 / 未命中
   ↓
[置信度校准] → final_confidence
   ↓
[状态机判断] → armed / cooldown
   ↓
[动作执行] → §52 通知 / §42 场景 / 摄像头快照
   ↓
[审计] → rule_audit_log
```

### 6.2 嵌套深度检查

```python
def validate_nesting(node, depth=0):
    if depth > 4:
        raise ValidationError("规则嵌套超过 4 层")
    if isinstance(node, dict):
        for v in node.values():
            validate_nesting(v, depth + 1)
    elif isinstance(node, list):
        for v in node:
            validate_nesting(v, depth + 1)
```

### 6.3 谓词引用检查

```python
def validate_predicates(node, available_sensors):
    if isinstance(node, dict):
        field = node.get('field')
        if field and not any(field.startswith(s) for s in available_sensors):
            raise ValidationError(f"未注册传感器: {field}")
        for v in node.values():
            validate_predicates(v, available_sensors)
    elif isinstance(node, list):
        for v in node:
            validate_predicates(v, available_sensors)
```

---

## 7. 自定义谓词（高级）

### 7.1 何时需要自定义

内置 23 个谓词不覆盖时：
- 复杂数学（斜率、积分）
- 跨设备统计（楼层用水总量）
- 第三方数据（天气 API、股票）

**警告**：自定义谓词必须**纯函数**（无副作用），并提供 **mock 数据**用于测试。

### 7.2 自定义步骤

```python
# 1. 实现 Predicate 类
class EnergySlopePredicate(Predicate):
    def eval(self, ctx):
        readings = ctx.window.get('energy_history', [])
        if len(readings) < 5:
            return False
        slope = calculate_slope(readings)
        return slope > self.threshold

# 2. 注册到 PREDICATE_REGISTRY
PREDICATE_REGISTRY['energy.slope'] = EnergySlopePredicate

# 3. 写测试
def test_energy_slope():
    ctx = make_context({'energy_history': [100, 110, 120, 130, 140]})
    pred = EnergySlopePredicate('energy.slope', threshold=5.0)
    assert pred.eval(ctx) == True

# 4. 在 YAML 中使用
- energy.slope > 5.0
```

---

## 8. LLM 自动生成规则

### 8.1 提示词模板

```markdown
你是家庭智能体的规则助手。基于以下家庭画像和近期事件，提议 3 条新规则。

## 家庭画像
- 5 口之家：祖父母（80 岁）/ 父母（45 岁）/ 孩子（10 岁）
- 设备：智能门锁、客厅 / 主卧 / 老人房 烟雾、卧室 / 厨房 水浸、客厅空调、窗帘 6 个
- 老人活动范围：客厅、卧室、卫生间
- 孩子 18:00 放学回家

## 近期事件（最近 30 天）
- 老人 3 次夜间起夜后长时间未归床（疑似摔倒）
- 1 次厨房水龙头忘关（虚拟事件）
- 0 次陌生人徘徊

## 输出格式
每条规则输出为 YAML，遵循 §53.2 DSL 规范。

## 关键约束
- ≤ 4 层嵌套
- ≤ 20 个条件
- 必须使用 sensor.fresh 防止陈旧数据
- severity 准确标注
- confidence_base 在 0.5-0.9 之间
```

### 8.2 校验流程（v2.19 §53.6.1）

LLM 输出后**必须**经过：

1. **YAML 语法校验**：PyYAML 解析无错
2. **Pydantic schema 校验**：所有必填字段、字段类型
3. **谓词白名单检查**：所有谓词在 23 个内置集 + 注册的自定义集
4. **嵌套深度检查**：≤ 4 层
5. **传感器存在性**：所有引用 sensor 在 devices 表已注册
6. **冲突检查**：与现有规则 id 不同
7. **置信度合理性**：confidence_base ∈ [0.5, 0.9]

**7 步全过** → 写入 `rules` 表，`author_type='llm_suggested'`，`validated_by=NULL`（必须人工确认才能启用）。

**任何一步失败** → LLM 输出回滚 + 提示用户"该规则建议未通过校验"。

### 8.3 用户确认 UI

```
┌─────────────────────────────────────────────┐
│ LLM 提议规则（未启用）                       │
├─────────────────────────────────────────────┤
│ 规则名：客厅有人 30 分钟空调自动调高          │
│ 描述：老人在客厅活动 30 分钟，调高 1 度      │
│ 触发条件：...                                │
│ 动作：调空调 + 推通知                        │
│ 置信度：0.65                                 │
│           [启用]  [修改]  [忽略]  [禁用]    │
└─────────────────────────────────────────────┘
```

### 8.4 LLM 提案审计

每次 LLM 提案写 `rule_audit_log.kind='llm_suggested'`：
```json
{
  "rule_id": "elderly_ac_auto_v1",
  "prompt_hash": "sha256:...",
  "llm_model": "deepseek-chat",
  "tokens_used": 1234,
  "validation_steps": ["yaml", "pydantic", "predicate", "nesting", "sensor", "conflict", "confidence"],
  "all_passed": true
}
```

---

## 9. 调试与复盘

### 9.1 查看规则触发历史

```sql
-- 最近 7 天，规则 X 的触发
SELECT fired_at, confidence, kind, ack_at, ack_by
FROM rule_audit_log
WHERE rule_id = 'elderly_fall_suspect_v1'
  AND fired_at > strftime('%s', 'now', '-7 days')
ORDER BY fired_at DESC;
```

### 9.2 误报分析

```sql
-- 30 天内误报 top 5 规则
SELECT rule_id, COUNT(*) as false_positive_count
FROM rule_feedback
WHERE feedback = 'false_positive'
  AND created_at > strftime('%s', 'now', '-30 days')
GROUP BY rule_id
ORDER BY false_positive_count DESC
LIMIT 5;
```

### 9.3 规则置信度曲线

```sql
-- 规则 X 的 30 天置信度走势
SELECT
  DATE(fired_at, 'unixepoch') as day,
  AVG(confidence) as avg_confidence,
  COUNT(*) as fire_count
FROM rule_audit_log
WHERE rule_id = 'elderly_fall_suspect_v1'
  AND fired_at > strftime('%s', 'now', '-30 days')
GROUP BY day
ORDER BY day;
```

### 9.4 PWA 调试面板入口

- 路径：`/settings/rules/{rule_id}/debug`
- 内容：当前状态 + 最后 10 次 fire + 置信度曲线 + 误报分析

---

## 10. 常见误报模式与调参

### 10.1 误报模式 1：传感器掉线时误报

**症状**：规则连续触发，但实际环境无变化。

**原因**：传感器返回陈旧数据，导致 `duration_minutes` 不断累加。

**调参**：
- 加 `sensor.fresh(<=60s, ...)` 谓词
- 提高频率
- 加 `cooldown: 7200` 减少重试

### 10.2 误报模式 2：深夜过度敏感

**症状**：夜间频繁触发，但白天正常。

**原因**：时间窗设置过宽。

**调参**：
- 收紧 `time.in_window`
- 加 `household.in_mode: "night"` 谓词
- 降低 confidence_base 至 0.5

### 10.3 误报模式 3：成员不在家时误报

**症状**：全员出门时规则触发。

**原因**：逻辑未排除"全家不在"场景。

**调参**：
- 加 `member.is_alone_at_home: true` 谓词
- 加 `any_family_at_home: false` 反向检查

### 10.4 误报模式 4：传感器噪声

**症状**：人体传感器一会在一会在，触发频率高。

**原因**：传感器灵敏度太高。

**调参**：
- 提高 `duration_minutes` 阈值（如 30 → 60）
- 用 `between` 谓词圈定稳定范围
- 加 `cooldown: 3600`

### 10.5 误报模式 5：规则相互重叠

**症状**：A 规则触发后 B 规则也触发。

**原因**：规则覆盖度过高。

**调参**：
- 在 PWA 启用"规则覆盖分析"（v2.20）
- 合并相似规则
- 加 mutually_exclude 谓词

---

## 11. 调参技巧

### 11.1 调参循环

```
1. 观察规则触发频率
2. 用户反馈误报率
3. 调整 confidence_base 或 cooldown
4. 等待 7 天再看数据
5. 调 predicate 条件
6. 循环到满意
```

### 11.2 调参的最佳实践

- **永远从提高到 cooldown 开始**（最不破坏逻辑）
- **不要一次性大改**（会让调参无法追溯）
- **每次调参写 `note`**（备注原因）
- **保留原规则**（用新 id）
- **每 30 天一次评审**（建议 v2.20 加自动评审）

### 11.3 调参的禁忌

- ❌ 不要禁用规则后立即删（保留 30 天）
- ❌ 不要多次小幅调参（合并为一次）
- ❌ 不要给 safety 规则设 confidence_base < 0.5
- ❌ 不要让 LLM 直接编辑规则（必须人工）

---

## 12. 规则备份与恢复

### 12.1 备份（v2.19 复用 §44 备份流程）

```bash
myhome-agent backup export --include rules
```

打包内容：
- `data/myhome.db`（含 rules 4 张表）
- `config/rules/*.yaml`（v2.19 可选：纯 YAML 模式）

### 12.2 恢复

```bash
myhome-agent backup restore myhome-backup-20260803.tar.gz
```

自动：
- 恢复 db 4 张表
- 校验规则数量
- 触发 `cold_start` 状态（不立即触发）

### 12.3 跨家庭复制规则

修改 `household_id` 后重新导入：

```sql
INSERT INTO rules (id, household_id, ...) 
SELECT id || '_v2', 2, ...  -- household_id 改为 2
FROM rules WHERE household_id = 1;
```

---

## 13. 规则版本与变更

### 13.1 规则版本号

每次 `updated_at` 变化 + `version` +1。

### 13.2 规则变更审计

```sql
CREATE TABLE rule_history (
  id INTEGER PRIMARY KEY,
  rule_id TEXT NOT NULL,
  version INTEGER NOT NULL,
  changed_at INTEGER NOT NULL,
  changed_by INTEGER,
  old_yaml TEXT,
  new_yaml TEXT,
  reason TEXT
);
```

### 13.3 规则回滚（v2.20 计划）

v2.19 不做 UI 回滚，命令行支持：

```bash
myhome-agent rules rollback elderly_fall_suspect_v1 --to-version 3
```

---

## 14. 规则与隐私

### 14.1 谁的规则谁能看

| 规则类型 | 谁能看 |
|---------|--------|
| 系统预设 | 全部成员 |
| 医生创建 | 医生 + admin + 监护人 |
| 家属创建 | 创建者 + admin |
| LLM 建议 | 全部成员（启用前） |

### 14.2 规则内容是否上云

**不上云**。规则 YAML 主体存储本地 SQLite，LLM 提示词**不包含**规则内容（避免泄漏家庭字段名）。

### 14.3 触发证据的隐私

```yaml
# evidence_snapshot 30 天后自动清理
# 长期保留只保留结构化字段（rule_id, fired_at, confidence）
```

### 14.4 GDPR（§43）

- 规则创建者撤销 → 规则**保留**（不能删除，因为其他人用了）
- 规则删除 = 软删除 + 30 天后硬删除
- 触发证据含成员画像 → 触发 GDPR 撤销一并清

---

## 15. 性能与监控

### 15.1 性能指标

| 指标 | 目标 | 告警阈值 |
|------|------|---------|
| 单次扫描耗时 | ≤ 200ms | > 500ms |
| 单条规则评估 | ≤ 5ms | > 20ms |
| 规则命中率 | 1-5% | > 20%（可能条件过宽） |
| 误报率 | < 10% | > 30% |
| 漏报率 | < 5% | > 15% |

### 15.2 监控面板

```
健康度指标
├── 扫描耗时 P50/P95/P99
├── 规则命中率
├── 误报率
├── 漏报率（人工标注）
├── 状态分布（armed/cooldown/disabled）
└── 凭证生命周期
```

### 15.3 性能降级

```python
if scan_duration_ms > 200:
    logger.warn("扫描超时，降级")
    SCAN_INTERVAL = 30  # 从 10s 降到 30s
    notify_admin("规则引擎已降级")
```

---

## 16. 迁移与升级

### 16.1 YAML 版本

v2.19 规则 YAML 头部：

```yaml
# yaml-version: 1
id: ...
```

未来 v2.20+ 升级时支持 `yaml-version: 2`。

### 16.2 字段淘汰

被淘汰的字段：

```yaml
# v2.19 之前的旧字段
threshold: 30      # 改为 duration_minutes
enabled: true      # 改为 enabled: 1
```

迁移脚本：

```python
def migrate_v1_to_v2(rule_yaml):
    if 'threshold' in rule_yaml['when']:
        rule_yaml['when']['duration_minutes'] = rule_yaml['when'].pop('threshold')
    return rule_yaml
```

### 16.3 升级检测

启动时：
1. 检查所有规则的 `yaml-version`
2. 不支持的版本 → 标记 `state='disabled'` + 提示

---

## 17. 附录：DSL 完整例子库

### 17.1 老人场景（5 条）

见 §3.1, §3.5, §3.7, §3.8, §3.16。

### 17.2 安全场景（5 条）

见 §3.4, §3.9, §3.10, §3.11, §3.12。

### 17.3 设备健康（3 条）

- §3.6 空调异常耗电
- §3.14 断电
- §3.15 NAS 离线

### 17.4 儿童场景（2 条）

- §3.3 孩子放学未归
- §3.13 婴儿哭声

### 17.5 习惯学习（1 条）

- §3.16 习惯异常

---

## 18. 文档变更日志

- v2.19 初版：完整 DSL 规范 + 16 条系统预设 + 谓词实现 + LLM 评审 + 调试指南
- v2.19 §18 修订：性能监控、迁移备份、隐私
- v2.20 计划：可视化编辑、自动评审、规则市场

---

## 19. 联系与反馈

- 规则引擎 v2.19 配套文档，2026-08-03 完成
- 反馈渠道：GitHub Issues / 项目讨论区
- 下一版（v2.20）计划：可视化规则编辑器 + 规则市场原型
