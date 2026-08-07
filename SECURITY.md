# 安全说明（Security Policy）

## 安全模型

myhome-agent 面向家庭局域网部署，安全设计如下：

- **网关鉴权**：除健康检查、登录、2FA/WebAuthn 登录外，所有 REST 与 WebSocket 都要求 Bearer 凭据（`MYHOME_API_TOKEN` 或成员 JWT）。
- **成员登录与 RBAC**：密码以 bcrypt 存储；角色权限矩阵控制设备控制、设置、导出与审计。
- **2FA / WebAuthn**：TOTP 备用码 bcrypt 存储；WebAuthn 使用 `py_webauthn` 真实验签；JWT 密钥来自 `.env`，不硬编码。
- **高危操作二次确认**：门锁 / 燃气 / 摄像头 / 主窗帘控制必须携带 `X-2FA-Token`；规则触发的直接控制进入 `pending_actions` 等待确认。
- **凭证加密**：RTSP URL 使用 Fernet 加密存储；优先使用 KMS（PBKDF2）派生。
- **注入防护**：硬规则条件使用 AST 白名单求值，不执行任意表达式。
- **可审计**：规则触发、治理决策、通知投递、待确认动作全部落库，可通过 `/api/audit/*` 查询与导出。

## 已知边界

- LLM 请求会携带家庭摘要与工具结果，当前没有自动脱敏层；敏感环境请使用本地模型。
- WebSocket 支持成员 JWT 与 API token；请使用 HTTPS 反向代理对外暴露。
- 联邦学习同态加密为真实 Paillier 实现，但跨家庭密钥分发协议仍是简化版本。

## 部署建议

- 将 `.env` 权限设为 `600`，不要提交或分发。
- 使用 HTTPS 反向代理（Caddy / Nginx / Tailscale 等）。
- 以非 root 用户运行；定期轮换 `MYHOME_API_TOKEN`、`MYHOME_JWT_SECRET` 与 `.env` 中的其他密钥。
- 使用 `git init` 后及时提交基线，便于追踪变更。

## 报告安全漏洞

请通过 GitHub Security Advisories（私有报告）提交漏洞，不要公开泄露细节。报告中请包含：

- 受影响版本与部署方式
- 复现步骤与最小示例
- 影响评估（例如是否可导致未授权设备控制 / 数据泄露）

我们会尽快确认并修复。
