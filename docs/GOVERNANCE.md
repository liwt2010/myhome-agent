# 治理框架（v0.5 §50 完整化）

> v2.19 §50 是占位，v0.5 落地完整治理体系。核心：**管家能力强了，谁来管管家？** 治理 = 风险评分 + 自治等级 + 资源配额 + 审计 + 用户覆盖。

## 1. 4 维风险评分

每个动作（控制 / 通知 / 决策）按 4 维评 0-1 风险分：

```
风险分 = severity + irreversibility + time + member_role + 在家
        最高 0.4 + 最高 0.3 + 最高 0.15 + 最高 0.15 + 0.05
        总上限 1.0
```

### 1.1 severity 维度

| 等级 | 分数 | 例子 |
|------|------|------|
| safety | 0.4 | 水浸 / 燃气 / 老人救命 |
| care | 0.2 | 异常告警 / 用药提醒 |
| info | 0.05 | 场景触发 / 日报 |

### 1.2 irreversibility 维度

| 等级 | 分数 | 例子 |
|------|------|------|
| irreversible | 0.3 | 删除设备 / 清空记忆 / 关阀 |
| costly | 0.15 | 重启路由器 / 恢复出厂 |
| reversible | 0.0 | 开灯 / 调温 |

### 1.3 time 维度

| 时段 | 分数 |
|------|------|
| night (22:00-8:00) | 0.15 |
| vacation | 0.10 |
| day | 0.0 |

### 1.4 member_role 维度

| 角色 | 分数 | 备注 |
|------|------|------|
| child | 0.15 | **强制 L1**（任何动作） |
| elder | 0.10 | 老人误操作风险 |
| guest | 0.05 | 访客受限 |
| adult | 0.0 | 自主 |

### 1.5 在家加成

- member_home=false: +0.05（远程操作风险高）

## 2. 自治等级决策树

| 风险分 | 等级 | 行为 |
|--------|------|------|
| **强制 L1** | L1 | safety+irreversible / child |
| ≥ 0.7 | L1 | 强制 confirm |
| ≥ 0.15 | L2 | 自动执行 + 通知 |
| < 0.15 | L3 | 自动 + 不通知 |
| 理论 L4 | L4 | 完全自主（v0.5 不启用） |

### 2.1 强制 L1 规则

**v0.5 不变式**：
- safety + irreversible 组合 → 永远 L1
- child 在场 → 永远 L1
- guest 在场 → 永远 L1（v0.5 简化版）

## 3. 资源配额

详见 `quotas.py`。

| 资源 | 基础 | 夜间 | 度假 |
|------|------|------|------|
| LLM 兜底 | 10/天 | 5/天 | 15/天 |
| LLM-Vision | 20/天 | 5/天 | 30/天 |
| Rule fire | 500/天 | 500/天 | 500/天 |

**降级链**：
- 超限 → 静默跳过
- 超限 ×2 → 降级到本地
- 超限 ×3 → 警告用户

## 4. 审计与覆盖

### 4.1 governance_decisions 表

```sql
CREATE TABLE governance_decisions (
  id INTEGER PRIMARY KEY,
  household_id INTEGER,
  member_id INTEGER,
  action TEXT NOT NULL,
  level TEXT NOT NULL,
  risk_score REAL,
  requires_confirm INTEGER DEFAULT 0,
  outcome TEXT,                  -- 'pending' | 'executed' | 'overridden' | 'rejected'
  user_override INTEGER DEFAULT 0,
  created_at INTEGER
);
```

### 4.2 用户覆盖

- **L1**：必须 PWA / TG 二次确认
- **L2/L3**：可事后审计（用户看 history 改 outcome）
- **L4**：不允许覆盖（v0.5 不启用）

### 4.3 审计查询

```sql
-- 最近 7 天所有 L1 决策
SELECT * FROM governance_decisions
WHERE level = 'L1' AND created_at > strftime('%s', 'now', '-7 days')
ORDER BY created_at DESC;

-- 用户覆盖率
SELECT level,
       SUM(CASE WHEN outcome='overridden' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as override_rate
FROM governance_decisions
WHERE created_at > strftime('%s', 'now', '-30 days')
GROUP BY level;
```

## 5. 与其他模块的对接

### 5.1 与 §53 规则引擎

每条规则 fire → 调 AutonomyEngine 决定执行/确认
- L1 → 等用户确认
- L2 → 自动执行 + 通知
- L3 → 自动不通知

### 5.2 与 §5.3 高危控制

- L1 → 强制 confirm
- L2/L3 → 不再额外 confirm（已分级）

### 5.3 与 §52 通知路由

- L2 自动 + notify=True → 走 §52 路由
- L3 自动 + notify=False → 不通知

### 5.4 与 §50 治理框架

- 风险评分 = §50 4 维评分
- 自治等级 = §50 L0-L4
- 资源配额 = §50 3 维（资源 × 时段 × 度假）

## 6. 治理 UI（PWA）

### 6.1 治理仪表盘（v0.5 计划）

- 当前风险分趋势
- 自治等级分布
- 资源配额使用
- 用户覆盖历史

### 6.2 决策详情

- 4 维评分雷达图
- 类似历史决策
- 一键覆盖 / 标记误报

## 7. 治理 API

```
GET  /api/governance/quotas             - 配额状态
POST /api/governance/vacation           - 度假模式开关
GET  /api/governance/decisions?days=7   - 决策历史
POST /api/governance/decisions/{id}/override  - 覆盖决策
```

## 8. 治理升级路径

| 版本 | 新增 |
|------|------|
| v0.5 | 4 维风险 + 自治等级 + 动态配额 + 治理决策表 |
| v0.6 | 智能风险预测（基于历史）+ 自治学习 |
| v1.0 | 跨家庭策略共享 + 公共治理模板 |

## 9. 治理不变量

- **任何 safety + irreversible 必走 L1**——不可绕过
- **任何 child 在场必走 L1**——不可绕过
- **超限必须降级**——不可"假装没看到"
- **决策必须审计**——不可静默执行
- **用户可覆盖**——不可"系统说了算"

## 10. 治理失败模式

| 失败 | 系统行为 |
|------|---------|
| 风险评分函数 bug | 降级到 L1（最保守） |
| 配额计数器崩 | 走默认配置 + 报警 |
| 决策表写入失败 | 重试 3 次，失败时拒绝执行 |
| AutonomyEngine 不可用 | 全部走 L1（最保守） |

## 11. §50 章节兑现

v2.19 §50 治理框架（占位）→ v0.5 本文档 + 代码 + API 全部落地。

| v2.19 占位 | v0.5 兑现 |
|-----------|----------|
| 规则版本 + 撤销 | rules.version + cascade_author_revoke（v0.4） |
| capabilities 不可变 | spec_normalizer + irreversibility_tier（v0.4） |
| 资源配额 | DynamicQuotas + 度假因子（v0.5） |
| 审计可追溯 | governance_decisions + rule_audit_log（v0.5） |
| 4 维风险评分 | AutonomyEngine（v0.5 新增） |
| 自治等级决策树 | L0-L4 决策（v0.5 新增） |
| 用户覆盖 | outcome + user_override（v0.5 新增） |
| GDPR 兼容 | §43 + 治理不变量（v0.4） |
