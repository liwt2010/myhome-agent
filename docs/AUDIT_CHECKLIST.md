# 第三方审计清单（v1.0.1 商业化前置）

> v1.0.1 商业化发布前必做。审计公司可选：CNIL / KPMG / EY / Deloitte / OneTrust。
> 商业化前 6 个月启动；商业化后每年一次。

## 1. 审计前（4 周准备）

### 1.1 文档清单（12 项必交）

- [ ] DPIA（docs/DPIA.md v1.0.1）
- [ ] DPA（docs/DPA.md + DPO 任命公告）
- [ ] 架构设计（ARCHITECTURE.md v1.0.1）
- [ ] 部署验证（DEPLOY_VERIFICATION.md 实测）
- [ ] 治理框架（GOVERNANCE.md + 决策表）
- [ ] 规则市场说明（§55 + §63）
- [ ] 安全架构（HSM / KMS / 2FA / WebAuthn）
- [ ] 数据流图（自动生成 + 标注）
- [ ] 应急响应流程（DPO IncidentResponse + KMS 轮换）
- [ ] 用户同意管理（members.consent_flags）
- [ ] 跨境传输评估（SCC 协议）
- [ ] 第三方 DPA 协议模板

### 1.2 技术证据（4 周收集）

| 类别 | 证据 |
|------|------|
| 代码 | Git 仓库完整历史（v0.1-v1.0.1）|
| 测试 | pytest 全通过 + 覆盖率报告 |
| 部署 | DEPLOY_VERIFICATION.md 12 项全打勾 |
| 监控 | Prometheus 指标 / 错误日志 |

### 1.3 人员访谈

- DPO（DPO 角色）
- 治理 lead（§50 治理负责人）
- 架构 lead（v1.0.1 架构作者）
- 至少 2 个真实家庭用户（可用性测试）

## 2. 审计中（2 周）

### 2.1 必查 12 项

| # | 检查项 | 标准 |
|---|--------|------|
| 1 | household_id 强制隔离 | CNIL / GDPR Article 25 |
| 2 | 数据加密（at-rest + in-transit）| NIST SP 800-111 |
| 3 | 密钥管理（HSM / KMS）| NIST SP 800-57 |
| 4 | 2FA 强制场景 | NIST SP 800-63B |
| 5 | 审计日志完整 | ISO 27001 A.12.4 |
| 6 | DPIA 自动化 | GDPR Article 35 |
| 7 | DPO 独立性 | GDPR Article 38 |
| 8 | 数据主体权利流程 | GDPR Article 12-22 |
| 9 | 跨境传输合规 | GDPR Chapter V |
| 10 | 第三方 DPA | GDPR Article 28 |
| 11 | 应急响应演练 | GDPR Article 33-34 |
| 12 | DPIA 公开 | GDPR Recital 39 |

### 2.2 抽样检查

- 随机 20 个 rule_fire 事件：审计日志 + 决策记录 + 通知路由全链路
- 随机 10 个 member 删除：GDPR 级联是否完整
- 随机 5 次跨家庭模板导入：DPIA 自检是否生效
- 随机 5 次主密钥轮换：旧数据是否仍可解密

### 2.3 渗透测试

- Web Push 通知伪造
- 2FA 绕过尝试
- TG bot 滥用（垃圾 / 越权）
- SQLite 注入（chat_history / rule_audit_log）
- 摄像头 RTSP URL 越权访问

## 3. 审计后（4 周整改）

### 3.1 整改 SLA

| 严重度 | SLA |
|--------|-----|
| 🔴 高（合规违反） | 7 天 |
| 🟠 中（最佳实践） | 30 天 |
| 🟡 低（建议） | 90 天 |

### 3.2 必交文档

- 整改计划（每项 1 行）
- 复测报告（30 天内）
- 升级版本号（v1.0.2 / v1.1.0）
- DPO 复审签字

### 3.3 公开承诺

- 审计公司 logo + 报告摘要（公开页）
- 第三方审计 badge（PWA + 官网）

## 4. 选审计公司

| 公司 | 强项 | 价位（参考）| 推荐场景 |
|------|------|----------|---------|
| **CNIL**（法国监管）| GDPR 严格 | €0（监管义务）| EU 必备 |
| **KPMG** | 全栈合规 + 安全 | €50K-100K | 上市公司 |
| **EY** | GDPR + ISO 27001 | €40K-80K | 中型企业 |
| **Deloitte** | GDPR + SOC2 | €50K-120K | 跨国 |
| **OneTrust** | SaaS 自动化 DPIA | $10K-30K/年 | 中小企业 |

## 5. 推荐路径

### 5.1 中小企业 / 开源版

- 跳过第三方审计
- 走自检清单 + GDPR Article 27 代表任命
- 公开 DPIA 文档

### 5.2 SaaS 商业版（v1.0）

- 必做：CNIL DPIA + DPO + 自检清单
- 推荐：OneTrust 自动化 DPIA 工具（$10K-30K/年）
- 预算：€5K-15K / 年

### 5.3 上市公司 / 跨国（v1.0+）

- 必做：KPMG / EY / Deloitte 第三方审计
- 必做：SOC2 Type II 认证
- 必做：ISO 27001 认证
- 预算：€100K-300K / 年

## 6. 必交付 6 类文档

| 文档 | 内容 | 公开 |
|------|------|------|
| **DPIA** | 数据保护影响评估（已就绪 docs/DPIA.md）| ✅ |
| **DPA** | 数据保护协议 + DPO 角色（已就绪 docs/DPA.md）| ✅ |
| **审计报告摘要** | 第三方审计 + 主要发现 | ✅ |
| **合规证书** | ISO 27001 / SOC2 / GDPR DPA | ✅ |
| **应急流程** | 违规响应 + 通知 SOP | 内部 |
| **DPIA 报告历史** | 每次 DPIA 自动化存档 | 内部 |

## 7. 时间表（商业化前）

```
M-6月   开始文档准备（12 项）
M-5月   文档 + DPO 任命
M-4月   部署验证 + 性能基准
M-3月   选审计公司 + 签合同
M-2月   内部预审 + 整改
M-1月   正式审计（2 周）
M-0.5月 整改 + 复测（4 周）
M       商业化发布
```

## 8. 成本估算

| 规模 | 一次性审计 | 年度维护 |
|------|----------|---------|
| 开源家庭（≤100 家庭）| €0（自检）| €1K-3K |
| SMB SaaS（100-1000 家庭）| €10K-30K | €5K-15K |
| 企业（1000-10K 家庭）| €50K-150K | €50K-150K |
| 跨国（10K+ 家庭）| €150K-500K | €150K-300K |

## 9. 检查表（v1.0.1 发布前）

- [ ] DPO 任命（公开 + 联系方式）
- [ ] DPIA v1.0 自动化跑通
- [ ] HSM / KMS 真实接入（AWS/GCP）
- [ ] 应急响应流程演练（v1.0.1 必演）
- [ ] 第三方 DPA 协议模板
- [ ] 用户同意管理（consent_flags 升级）
- [ ] 数据主体权利 SLA
- [ ] 跨境传输 SCC 协议
- [ ] DPIA 公开页（合规透明）
- [ ] 年度审计签约

## 10. 附录：v1.0.1 已就位 vs 仍需补

| 项 | 状态 |
|----|------|
| DPIA 文档 | ✅ docs/DPIA.md |
| DPA + DPO 任命 | ✅ docs/DPA.md + governance/dpo.py |
| DPIA 自动化 | ✅ governance/dpia_automation.py |
| HSM/KMS 接入 | ✅ security/kms_aws.py + kms_gcp.py |
| 应急响应 | ✅ DPOIncidentResponse |
| 用户同意管理 | ✅ members.consent_flags |
| 数据主体权利 | ✅ §43.3 + /api/households/{id}/export |
| 跨境 SCC 协议 | ❌ 需法务起草 |
| 第三方审计签约 | ❌ v1.0.2 启动 |
| ISO 27001 认证 | ❌ v2.0 启动 |

**v1.0.1 自检部分 100% 完成；外部签约部分需商业化时启动。**