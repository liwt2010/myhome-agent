# SOC2 Type II 认证准备（v2.0）

> 美国注册会计师协会（AICPA）Trust Services Criteria。
> B2B SaaS 商业化必备（美国客户必查）。
> 区别于 SOC2 Type I（单点评估），Type II 需 9-12 月连续观察窗口。

## 1. SOC2 五大 Trust Services Criteria

| TSC | 简称 | 重点 | myhome-agent v2.0 |
|-----|------|------|-------------------|
| **Security** | CC1-CC9 | 防未授权访问 | ✅ 核心 |
| **Availability** | A1 | 系统可用性 | ✅ 重点 |
| **Processing Integrity** | PI1 | 处理准确性 | ✅ 重点 |
| **Confidentiality** | C1 | 保密信息保护 | ✅ 重点 |
| **Privacy** | P1-P8 | 个人隐私 | ✅ 重点（GDPR）|

**SOC2 Type II 报告**：覆盖选定 TSC + 9-12 月运行证据

## 2. Security（CC 通用控制）— 必选

### 2.1 CC1 控制环境

| 控制 | 实施 |
|------|------|
| CC1.1 治理 | §50 治理 + DPO |
| CC1.2 董事会监督 | v2.1 计划（商业化需）|
| CC1.3 管理层职责 | §50 governance_decisions |
| CC1.4 能力 / 培训 | DPO / 治理 lead 培训 |
| CC1.5 责任追究 | 决策审计表 |

### 2.2 CC2 通信与信息

| 控制 | 实施 |
|------|------|
| CC2.1 内部沟通 | docs/ 14 文档 |
| CC2.2 外部沟通 | docs/DPA.md + 公共隐私页 |
| CC2.3 信息捕获 | audit_log 表 |

### 2.3 CC3 风险评估

| 控制 | 实施 |
|------|------|
| CC3.1 业务目标 | ARCHITECTURE.md §1 决策表 |
| CC3.2 风险识别 | §7 风险表 + DPIA |
| CC3.3 欺诈风险 | DPO + 治理仪表盘 |
| CC3.4 变更管理 | §27 路线图 |

### 2.4 CC4 监控活动

| 控制 | 实施 |
|------|------|
| CC4.1 持续监控 | governance_decisions |
| CC4.2 缺陷评估 | DPIA 自动化 |

### 2.5 CC5 控制活动

| 控制 | 实施 |
|------|------|
| CC5.1 控制选择 | §50 治理 + §47 policy |
| CC5.2 技术控制 | KMS + Fernet + WebAuthn |
| CC5.3 部署政策 | ARCHITECTURE + DEPLOYMENT |

### 2.6 CC6 逻辑与物理访问

| 控制 | 实施 |
|------|------|
| CC6.1 访问控制策略 | §14 RBAC + §47 policy 9 角色 |
| CC6.2 注册/注销 | §43 删 member 10 步 |
| CC6.3 授权 | §14 决策表 + §61 2FA |
| CC6.4 物理访问 | 数据中心 ISO 27001 |
| CC6.5 数据销毁 | GDPR §17 + Fernet |
| CC6.6 外部边界 | Web Push + WebAuthn |
| CC6.7 传输加密 | TLS + WebSocket |
| CC6.8 恶意软件 | vision 16 规则 |

### 2.7 CC7 系统操作

| 控制 | 实施 |
|------|------|
| CC7.1 检测异常 | §16 状态灯 |
| CC7.2 异常响应 | DPOIncidentResponse |
| CC7.3 事件评估 | 自动 DPIA |
| CC7.4 事件响应 | 24h 启动 + 72h 通知 |
| CC7.5 恢复 | §44 backup + restore |

### 2.8 CC8 变更管理

| 控制 | 实施 |
|------|------|
| CC8.1 变更授权 | §50 治理 review |
| CC8.2 测试 | DEPLOY_VERIFICATION.md |
| CC8.3 部署 | v0.x-y 修订流程 |

### 2.9 CC9 风险缓解

| 控制 | 实施 |
|------|------|
| CC9.1 风险识别 | §7 风险表 |
| CC9.2 缓解措施 | §50 治理 + KMS + DPIA |

## 3. Availability（A）

| 控制 | 实施 | 目标 |
|------|------|------|
| A1.1 容量规划 | §1b SLO | ≥99.9% |
| A1.2 环境保护 | NAS 备份 + 异地 | 99.99% |
| A1.3 恢复测试 | §44 backup + restore | RTO < 30 min |

## 4. Processing Integrity（PI）

| 控制 | 实施 |
|------|------|
| PI1.1 数据准确性 | §53 置信度校准 |
| PI1.2 数据完整性 | SQLite WAL + §44 backup |
| PI1.3 处理监控 | §16 状态灯 |

## 5. Confidentiality（C）

| 控制 | 实施 |
|------|------|
| C1.1 数据识别 | §5.11 redactor |
| C1.2 数据处置 | Fernet + 30 天清理 |

## 6. Privacy（P）

| 控制 | 实施 | 章节 |
|------|------|------|
| P1.1 隐私声明 | docs/DPA.md | ✅ |
| P2.1 数据收集 | consent_flags | ✅ |
| P3.1 数据使用 | §50 治理 | ✅ |
| P4.1 数据访问 | §47 policy 9 角色 | ✅ |
| P5.1 数据保留 | 30 天 + §43 | ✅ |
| P5.2 数据销毁 | §43.3 GDPR 级联 | ✅ |
| P6.1 访问权 | 治理仪表盘 | ✅ |
| P6.2 更正权 | PWA 设置 | ✅ |
| P6.3 删除权 | §43 删 member | ✅ |
| P6.4 数据可携 | /api/households/export | ✅ |
| P6.5 反对权 | consent_flags 单字段 | ✅ |
| P6.6 限制处理 | consent_flags | ✅ |
| P7.1 通知 | DPA 公开 | ✅ |
| P8.1 质量 | 数据验证 | ⚠️ |

## 7. Type II 证据收集

### 7.1 9-12 月窗口

每月抽样：
- 5 次 governance_decisions（覆盖各种 severity）
- 5 次 rule_fire（覆盖各种规则类型）
- 5 次 access_control（admin / adult / elder）
- 3 次 backup + restore 演练
- 1 次 DPIA 自动化跑通

### 7.2 测试方法

- **Inquiry（询问）**：问管理员 / 用户
- **Observation（观察）**：看实际运行
- **Inspection（检查）**：审计日志 + 代码
- **Re-performance（复演）**：重新跑控制

## 8. SOC2 审计师

| 公司 | 强项 |
|------|------|
| **Deloitte** | 大客户优先 |
| **EY** | 全球覆盖 |
| **KPMG** | 中型客户 |
| **Coalfire** | 中小 SaaS |
| **Schellman** | 中小 SaaS |

## 9. 时间表

```
M-12月 启动：定义 TSC 范围
M-9月  实施控制 + 文档
M-6月  内部审计 + 整改
M-3月  选审计师 + 签合同
M       9-12 月观察窗口开始
M+9月  Type II 报告发布
M+12月 客户可索取报告
```

## 10. 成本估算

| 项 | 费用 |
|----|------|
| Type II 审计 | ¥200K-500K |
| Type I 预审 | ¥50K-100K |
| 内审员 + 文档 | ¥100K |
| 修复 + 整改 | ¥50K-200K |

**总预算：¥400K-900K**

## 11. 与 ISO 27001 协同

| 项 | ISO 27001 | SOC2 |
|----|-----------|------|
| 治理 | 完整 ISMS | CC1 通用控制 |
| 风险 | 风险评估方法 | CC3 风险评估 |
| 物理 | A.7 14 控制 | CC6.4 |
| 技术 | A.8 34 控制 | CC6.6/6.7 |

**建议**：先 ISO 27001（基础），再 SOC2 Type II（美国客户）

## 12. v2.0 已就位 vs 仍需补

| v2.0 已做 | 仍需做 |
|---------|--------|
| ✅ CC1-CC9 大部分控制 | ⚠️ CC1.2 董事会监督 |
| ✅ A1.1-A1.3 容量规划 | ⚠️ 真实恢复测试 |
| ✅ PI1.1-PI1.3 | ⚠️ 处理异常追踪 |
| ✅ C1.1-C1.2 | ⚠️ 第三方数据处理 |
| ✅ P1-P8 大部分 | ⚠️ 数据质量 P8 |

**v2.0 控制层 ~85% 完整，证据层需 9-12 月。**

## 13. 检查表

- [ ] TSC 范围确定（Security + Privacy + Confidentiality + Availability）
- [ ] 控制文档化
- [ ] 9-12 月证据收集开始
- [ ] 选审计师 + 签合同
- [ ] Type I 预审
- [ ] Type II 正式审
- [ ] 报告发布

**v2.0 启动准备 = 12 月后可发布报告。**

## 14. 附录：客户侧使用

- 大客户合同要求：附 SOC2 Type II 报告
- 政府客户：ISO 27001 + SOC2
- 医疗客户：HIPAA + SOC2 + ISO 27001
- 欧洲客户：GDPR + ISO 27701

**商业化建议路径**：SOC2 Type I (6 月) → SOC2 Type II (12 月) → ISO 27001 (24 月)。