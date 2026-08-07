# 文档同步记录（2026-08-07）

> 本文档记录 2026-08-07 对全部项目文档的同步动作。原则：凡与当前代码冲突处，以代码与 `tests/` 为准；状态以 [ARCHITECTURE.md](../ARCHITECTURE.md) 的“00 实现现状对照”为索引。

## 同步动作

| 文档 | 类型 | 动作 | 说明 |
|------|------|------|------|
| `ARCHITECTURE.md` | 架构 | ✅ 全量重写 | 按当前代码逐章重写，含实现现状对照、API 清单、数据模型、认证权限、已知边界 |
| `README.md` | 入门 | ✅ 重写 | 简体中文，含与传统全屋智能对比 |
| `README.en.md` | 入门 | ✅ 新增 | 英文版 |
| `README.zh-TW.md` | 入门 | ✅ 新增 | 繁体中文版 |
| `SECURITY.md` | 安全 | ✅ 重写 | 安全模型、部署建议、漏洞报告 |
| `docs/CHANGELOG.md` | 记录 | ✅ 更新 | 新增 v2.5 条目 |
| `docs/TODO.md` | 记录 | ✅ 重写 | 已完成项归档 + 剩余优先级 |
| `docs/MATTER_BUILD.md` | 操作 | ✅ 更新 | 上游脚本路径、Docker 镜像风险提示 |
| `docs/DOCS_SYNC.md` | 记录 | ✅ 新增 | 本文件 |
| `docs/AUDIT_CHECKLIST.md` | 合规 | 🔖 状态横幅 | 内容留待合规专项 |
| `docs/CHANNELS.md` | 设计 | 🔖 状态横幅 | Telegram 白名单已实现，A2A/通知已实现 |
| `docs/DEPLOYMENT.md` | 操作 | 🔖 状态横幅 | 认证/RBAC 已就绪 |
| `docs/DEPLOY_VERIFICATION.md` | 操作 | 🔖 状态横幅 | 校验项以当前 API 为准 |
| `docs/DPA.md` | 合规 | 🔖 状态横幅 | 留待合规专项 |
| `docs/DPIA.md` | 合规 | 🔖 状态横幅 | 留待合规专项 |
| `docs/GOVERNANCE.md` | 治理 | 🔖 状态横幅 | 自治/配额/共识已部分实现 |
| `docs/HARDWARE_INTEGRATION.md` | 操作 | 🔖 状态横幅 | 待真机联调 |
| `docs/HOUSEHOLD.md` | 设计 | 🔖 状态横幅 | 领域模型部分未落地 |
| `docs/ISO27001.md` | 合规 | 🔖 状态横幅 | 留待合规专项 |
| `docs/MIGRATION.md` | 操作 | 🔖 状态横幅 | 2026-08 新增表已记录于 SCHEMA 变更 |
| `docs/OBSERVABILITY.md` | 设计 | 🔖 状态横幅 | 审计 API 已实现 |
| `docs/PLUGINS.md` | 设计 | 🔖 状态横幅 | 市场/插件部分未落地 |
| `docs/REAL_PROTOCOL_TESTING.md` | 操作 | 🔖 状态横幅 | 待真机联调 |
| `docs/REAL_WORLD_TESTING.md` | 操作 | 🔖 状态横幅 | 待真机联调 |
| `docs/RELIABILITY.md` | 设计 | 🔖 状态横幅 | 部分机制已实现 |
| `docs/RULES.md` | 设计 | 🔖 状态横幅 | 规则引擎已实现，置信度部分因子仍简化 |
| `docs/SCHEMA.md` | 设计 | 🔖 状态横幅 | 新增表：app_settings / member_credentials / pending_actions |
| `docs/SERVICES.md` | 设计 | 🔖 状态横幅 | 服务代办未落地 |
| `docs/SOC2.md` | 合规 | 🔖 状态横幅 | 留待合规专项 |
| `docs/UX_FLOWS.md` | 设计 | 🔖 状态横幅 | 登录/待确认/审计流程已接后端 |

## 说明

- “✅ 重写 / 新增 / 更新”：已按当前实现逐字同步。
- “🔖 状态横幅”：在文档头部加入了“同步状态”横幅，指向 ARCHITECTURE.md 状态表；正文为历史设计稿，待专项深更。
- 后续每次代码变更后，请在本文档登记并更新对应横幅日期。
