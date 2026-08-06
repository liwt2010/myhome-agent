# 渠道集成（v0.5 §50 升级路径 2）

> Telegram / 微信 / 小爱 等多渠道接入指南。v0.5 实现 TG；微信 v2.19 决策 B 不做。

## 1. Telegram（v0.5 完整支持）

### 1.1 创建 bot

1. 打开 Telegram，搜 **@BotFather**
2. 发送 `/newbot`
3. 按提示填名字（myhome-agent-bot）和 username（myhome_xxx_bot）
4. 拿到 **bot token**（形如 `123456:ABC-DEF...`）
5. 把 token 写入 `.env`：
   ```bash
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
   ```

### 1.2 启动 TG bot

```bash
myhome-agent channels start-telegram
```

或 CLI 内部调：
```python
from myhome_agent.channels.telegram import TelegramBot
bot = TelegramBot(token=os.getenv("TELEGRAM_BOT_TOKEN"), agent=my_agent, store=my_store)
bot.start()
```

后台线程 polling 启动。日志看到 `Telegram bot 启动` 即可。

### 1.3 用户绑定（/bind）

1. 用户在 TG 搜你的 bot username
2. 发送 `/start` → 看到欢迎 + 命令列表
3. 发送 `/bind 张爷爷`（或你的家庭成员名）
4. bot 返回 `✅ 已绑定张爷爷！`

**per-member 绑定**：每个家庭成员用自己的 TG 账号，bind 自己的名字。bot 通过 `members.notification_prefs.telegram_chat_id` 区分消息来源。

### 1.4 完整命令

| 命令 | 功能 |
|------|------|
| `/start` | 欢迎 + 帮助 |
| `/bind <名字>` | 绑定 chat_id 到 member |
| `/chat <消息>` | 与 Agent 对话（DeepSeek） |
| `/status` | 家庭状态（设备/成员/告警）|
| `/rules` | 已启用规则列表 |
| `/devices` | 设备列表 |
| `/alerts` | 当前告警 |

### 1.5 远程控制（v0.5 基础）

直接发消息 → Agent 收到 → 走 §5.3 高危确认。

```bash
# 远程关灯
TG: 关客厅灯
Bot: 我注意到你要关闭客厅灯（safety level）。请在 PWA 二次确认。

# 或直接 /chat
TG: /chat 帮我关掉客厅的灯
Bot: 已通知 PWA，请确认
```

**v0.5 限制**：远程控制需 PWA 二次确认（避免 TG 误触发高危动作）。v1.0 加"快速确认 5 分钟"机制。

### 1.6 群组支持（v0.5.2，§50 升级路径 2）

- 群组中 @bot 触发对话
- reply_to_message 识别提问人
- 群组事件审计

## 2. 微信（v2.19 决策 B：不做）

**v2.19 决策 B**：个人微信协议 2023 起高风险，企业微信需要企业主体，第三方 iPad 协议随时封号。**v0.5 不支持**。

**未来条件**：
- v3 治理框架成熟（v2.21+ 预计）
- 用户提供企业微信 corp_id（合规主体）
- 走企业微信 API 而非个人微信

**临时替代**：Telegram 始终可用（推荐）或外网用 Telegram、内网用 PWA。

## 3. 小爱音箱（§7 风险表，攻关项）

- 官方不开放 API
- 社区方案：miservice / mi-gpt（逆向）
- v0.5 占位，v1.0 不确定能解

## 4. Web Push（v0.5 完整支持）

PWA 启用 Web Push（v0.5 已实现）：
- 用户在 PWA 启用推送
- 服务器用 VAPID key 推送
- v0.5 PWA 自动申请 + 持久化 `push_subscriptions` 表

详见 §30.3 PWA 章节。

## 5. 渠道优先级

按 §52 通知路由 + §5.3 高危确认：

| 等级 | 渠道优先级 |
|------|-----------|
| **safety** | PWA → TG → SMS → voice call |
| **care** | PWA → TG（按成员 preference）|
| **info** | PWA → 每日汇总 |

## 6. 渠道安全

- **bot token 加密**：Fernet 存储（v0.5 默认 `.env` 明文 + 文档提示 Fernet 升级）
- **per-member chat_id**：必须 bind 才能收到个人消息
- **审计**：每次消息 / 控制进 events 表
- **降级**：bot 不可达 → 仍走 PWA push

## 7. 故障排查

| 症状 | 原因 | 解决 |
|------|------|------|
| bot 不响应 | token 错 | `curl https://api.telegram.org/bot<token>/getMe` 测 |
| /bind 失败 | 找不到成员 | 先在 PWA `/settings/members` 添加 |
| 消息不收 | chat_id 未绑 | 重新 /bind |
| 中文乱码 | TG 默认 UTF-8 OK | 检查 bot code page |

## 8. 未来路线

- v0.6：bot 状态推送（规则 fire 实时推）
- v1.0：内联键盘（直接点按钮操作）
- v1.0：视频片段（v0.3 视觉事件附 5s 片段）
