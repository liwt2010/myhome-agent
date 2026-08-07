# 待办事项 / 待优化项

> 更新：2026-08-07。已完成项会移入“已完成”并留痕；剩余项按优先级排序。

## ✅ 已完成（2026-08-07 前）

- [x] 网关鉴权、成员登录 / RBAC、2FA / WebAuthn、高危设备二次确认
- [x] 规则触发 → 告警 → 通知队列 → Telegram / 站内推送
- [x] 统一审计 API 与待确认控制动作（确认 / 取消 / 过期）
- [x] 前端登录页、WebAuthn 登录、待确认操作、场景与隐私设置
- [x] 视觉快照落盘与访问控制、视觉事件告警联动
- [x] 联邦学习真实 Paillier 同态加密 + 差分隐私
- [x] Matter ID 表校正、chip-tool 命令构造、返回契约、commission 参数
- [x] 开源准备：README 三语、LICENSE、CONTRIBUTING、CI、SECURITY
- [x] 文档同步：ARCHITECTURE 重写、CHANGELOG、DOCS_SYNC、各 docs 状态横幅

## 立即（优先级高）

- [ ] ⭐ 吊销 / 轮换对话中出现的 GitHub PAT（两个 token 均已明文泄露）
- [ ] ⭐ 删除或妥善保管 `C:\tmp\myhome-agent-secrets-quarantine` 中的隔离凭据文件
- [ ] ⭐ 真实硬件联调（HARDWARE_INTEGRATION.md 6-8 周流程）
  - 3 品牌摄像头（海康 / 大华 / TP-LINK）
  - TG bot 真实创建 + `/bind`
  - iOS / Android PWA 实测
- [ ] ⭐ Matter / Thread / Zigbee 真机联调（chip-tool / ot-ctl / bellows）
- [ ] ⭐ LLM 实测扩展：配置 Qwen / Zhipu / Kimi 等 key 并跑真实对比

## 短期（v1.0 商业化）

- [ ] ⭐ DPO 团队筹建 + 任命公告
- [ ] ⭐ SOC2 Type II / ISO 27001 认证启动
- [ ] ⭐ Marketplace 平台真实上线（myhome.market SaaS）
- [ ] ⭐ KMS 真实接入 AWS KMS / GCP KMS（替换 stub）
- [ ] ⭐ HSM / TPM 集成（替换 Fernet fallback）
- [ ] · 前端成员密码设置 UI（后端 API 已就绪）
- [ ] · 待确认动作的站内确认页完善（当前为模态框）

## 中期（v1.x 优化 + 跨生态）

- [ ] ⭐ Matter / Thread / Zigbee 真实设备验证与命令输出解析
- [ ] ⭐ OCR / 视觉数据集联邦学习（摔倒 → 跌倒 + 入侵 + 火灾）
- [ ] · 跨家庭协作（任务接力 / 资源池 / 共识投票）真实跑通
- [ ] · Web 公共规则市场 UI（PWA 集成）
- [ ] · LLM 预算精确记账（当前为估算 token）
- [ ] · 视觉快照自动清理 / 保留策略

## 长期（v2.0+ 自治 + 智能）

- [ ] ⭐ 自治 Agent Marketplace 实施（myhome.market 平台代码）
- [ ] ⭐ 联邦学习 Flower 真实 1000 家庭训练
- [ ] ⭐ 区块链结算（Polygon / Arbitrum 侧链）
- [ ] ⭐ A2A 协议 v2.0（去中心化 Agent 通信）
- [ ] · AI 增强 5 方向 v5.0
