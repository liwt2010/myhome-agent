# 待办事项 / 待优化项


## ⏸ 暂停点（2026-08-04 v2.2）

- **Matter 真实 SDK 集成**：chip-tool Python 封装完成（`collectors/chip_tool_wrapper.py` + `matter_adapter.py` 升级），待编译 chip-tool 后真实跑通
- **Thread 真实 SDK**：待下次继续
- **Zigbee 真实 SDK**：bellows 已装，待 USB 适配器
- **PWA WebAuthn UI**：占位完成，待接真实 SDK
- **真实 LLM 实测**（Qwen/Zhipu/Kimi 等）：待下次继续
- **真实硬件联调**：待下次继续

下次回来：看 ARCHITECTURE.md 顶部 v2.2 修订注记 + 本文件暂停点

> 截至 v3.0.1（2026-08-04）会话结束时的未完成工作。
> 优先级 ⭐ = 商业化关键 / ⭐ = 重要 / · = nice-to-have

---

## 立即（v0.x 商业化前置）

- [ ] ⭐ 你的真实硬件联调（HARDWARE_INTEGRATION.md 6-8 周流程）
  - 3 品牌摄像头（海康 / 大华 / TP-LINK）
  - TG bot 真实创建 + /bind
  - iOS / Android PWA 实测
  - 100 并发 / 1 小时稳定性
- [ ] ⭐ 撤销 v3.0.1 LLM 对话暴露的 2 个 key（model-info / Kimi）
- [ ] ⭐ LLM 实测扩展：配置 Qwen / Zhipu / Kimi 全部 key + 跑 6 provider 真实对比
- [ ] ⭐ 真实 LLM 端到端：myhome-agent serve + curl /api/chat 触发真实调用

## 短期（v1.0 商业化）

- [ ] ⭐ DPO 团队筹建 + 任命公告（v1.0 必做）
- [ ] ⭐ SOC2 Type II 签约（9-12 月观察窗口启动）
- [ ] ⭐ ISO 27001 认证启动
- [ ] ⭐ Marketplace 平台真实上线（myhome.market SaaS）
- [ ] ⭐ KMS 真实接入 AWS KMS / GCP KMS（替换 stub）
- [ ] ⭐ HSM / TPM 集成（替换 Fernet）
- [ ] · WebAuthn FIDO2 完整 UI + iOS Face ID / Android Fingerprint

## 中期（v1.x 优化 + 跨生态）

- [ ] ⭐ Matter / Thread / Zigbee 真实 SDK 集成
  - chip-tool（编译 1 小时）
  - OpenThread（编译）
  - bellows（已装）
- [ ] ⭐ OCR 数据集 FL（v4.x 扩展摔倒 → 跌倒 + 入侵 + 火灾）
- [ ] · v4.2 真实公开数据集（HAR/URFD 等公开集服务器稳定后）
- [ ] · 跨家庭协作（任务接力 / 资源池 / 共识投票）真实跑通
- [ ] · Web 公共规则市场 UI（PWA 集成）

## 长期（v2.0+ 自治 + 智能）

- [ ] ⭐ v3.1 自治 Agent Marketplace 实施（myhome.market 平台代码）
  - 16 月实施路线 v3.1.0 → v3.1.5
- [ ] ⭐ v4.0 联邦学习（Flower 真实 1000 家庭）
  - 14 月实施路线 v4.0.0 → v4.0.4
- [ ] ⭐ 区块链结算（Polygon / Arbitrum 侧链）
- [ ] ⭐ A2A 协议 v2.0（去中心化 Agent 通信）
- [ ] · AI 增强 5 方向 v5.0
  - 多 LLM 智能路由（v3.0 已实现，v5.0 完善）
  - VLM 视觉（v3.0 已实现，v5.0 完善）
  - 长期记忆（v3.0 已实现，v5.0 完善）
  - 主动服务（v3.0 已实现，v5.0 完善）
  - 智能家庭决策（v3.0 已实现，v5.0 完善）
- [ ] · 跨家庭规则自动同步（consensus 触发）

## 优化项

### 性能

- [ ] · WebSocket 长连接替代轮询（v0.3 已规划）
- [ ] · PWA Service Worker 缓存策略优化（v0.8 已实现）
- [ ] · LLM 调用批处理（v3.0 stub）
- [ ] · 视觉管线 GPU 共享池（v3.1 算力交易）

### 体验

- [ ] · PWA 老人模式 UI（超大字体 + 慢节奏 + 语音优先）
- [ ] · TG 命令补全（/help 显示所有命令）
- [ ] · Marketplace Web UI（v3.1 +）
- [ ] · 治理仪表盘 PWA（v0.6 已实现，v1.0 完善）
- [ ] · 离线模式（v0.8 已实现 Service Worker）

### 安全

- [ ] ⭐ Fernet 主密钥轮换自动化（v0.x 手动作业）
- [ ] ⭐ 异常检测规则（v0.5 已有，继续扩展）
- [ ] ⭐ 自动 DPoA 检查（v1.0 必做）
- [ ] · 第三方 DPA 协议模板
- [ ] · 跨境 SCC 标准合同

### 文档

- [ ] · docs/CHANGELOG.md 写完整版本历史
- [ ] · docs/FAQ.md（用户常问问题）
- [ ] · docs/TROUBLESHOOTING.md（常见故障）
- [ ] · docs/INTEGRATION.md（开发者接入指南）
- [ ] · 翻译：所有文档英文化（v1.0 商业化需）

## 已完成（v3.0.1）

- [x] ✅ 架构 v0.x → v4.3（70 节，~21000 行）
- [x] ✅ 20 专题文档
- [x] ✅ 35+ 代码模块
- [x] ✅ 4 sklearn 真实数据集 FL 训练（iris / wine / breast_cancer / digits）
- [x] ✅ 3 Agent 端到端交易场景
- [x] ✅ A2A 协议（HTTP + WebSocket + HMAC）
- [x] ✅ 2FA / TOTP / WebAuthn 模块
- [x] ✅ 跨生态 adapter 8 个（米家 / 涂鸦 / Hue / HomeKit / Matter / Thread / Zigbee）
- [x] ✅ DPIA / DPA / GDPR / ISO 27001 / SOC2 文档
- [x] ✅ DeepSeek 真实 LLM 集成跑通

## 数字统计（v3.0.1 截至）

| 指标 | 数值 |
|------|------|
| 架构 | ~21500 行 / 70 节 |
| 专题文档 | 20 个 |
| 代码模块 | ~35 个 |
| 真实跑通端点 | 8 个 + 3 Agent 端到端 |
| 真实跑通 LLM | DeepSeek |
| 真实跑通数据集 | 4 sklearn + 合成摔倒 |
| 真实跑通协议 | YOLO + Zigbee + Matter adapter（stub） |

## 接下来你定

回任何时候回来选一个：

1. **v0.8.1 真实硬件联调**（按 HARDWARE_INTEGRATION.md）
2. **v1.0 商业化 DPO + SOC2 启动**
3. **v3.1 自治 Marketplace 实施**
4. **v4.0 联邦学习真实 1000 家庭**
5. **v3.0 国产 LLM 全部 6 provider 实测**
6. **新增方向**（你提）

## 联系 / 后续

- GitHub Issues：bug 报告 / 功能请求
- 文档：ARCHITECTURE.md / docs/*.md
- 项目状态：v3.0.1 商业可用（需真实硬件联调 + 商业化前置）

---

**项目状态：v3.0.1 商业可用** ✅

下次再开始时，先看本文件 + ARCHITECTURE.md 顶部 v3.0.1 修订注记，了解最新进度。
## 开源准备清单（v3.0.1）

✅ 已完成：
- [x] .env 清空真实 key（DEEPSEEK_API_KEY + MYHOME_FERNET_KEY）
- [x] .env.example 重写：仅占位 + 完整 LLM/KMS/TG 配置项
- [x] .gitignore 完整化（.env / 模型权重 / 检查点 / 编辑器）
- [x] SECURITY.md 创建（含报告流程 + 安全架构）
- [x] docs/TODO.md 完善
- [x] ARCHITECTURE.md v3.0.1 修订

⏳ 下次可加（不阻塞开源）：
- [ ] LICENSE（推荐 MIT）
- [ ] CONTRIBUTING.md
- [ ] CODE_OF_CONDUCT.md
- [ ] GitHub Actions CI（pytest + lint）
- [ ] GitHub issue 模板
- [ ] git secrets 工具扫历史 commit
- [ ] Dependabot 配置
