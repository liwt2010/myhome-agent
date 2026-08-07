# 🏠 myhome-agent · 家庭私人管家

本地优先的家庭智能体：采集智能设备数据、学习作息、运行确定性规则引擎、通过 LLM 自然对话，并对自主行为做审计与二次确认。

其他语言：English（[README.en.md](README.en.md)）· 繁體中文（[README.zh-TW.md](README.zh-TW.md)）

## 核心能力

- 设备接入：米家（micloud/miio）、涂鸦、Hue、Matter、Zigbee、Thread（Matter/Zigbee/Thread 代码已接，真机联调待 chip-tool / 硬件）
- 规则引擎：跨信号推理、置信度校准、LLM 兜底、误报反馈闭环
- 视觉管线：RTSP + YOLO 人形/跌倒/火焰检测、快照落盘与访问控制
- 自然交互：DeepSeek（默认）等多 LLM 路由、工具调用、长期记忆
- 自主治理：L0-L4 等级、风险评分、决策审计
- 安全默认：网关鉴权、成员登录/RBAC、2FA/WebAuthn、高危设备二次确认
- 通知与审计：Telegram/站内通知、统一审计 API、待确认动作
- 联邦学习：真实 Paillier 同态加密 + 差分隐私

## 与传统全屋智能的区别

| 维度 | 传统全屋智能（米家 / 华为 / Home Assistant 等） | myhome-agent |
|------|-----------------------------------------------|--------------|
| 定位 | 设备控制与场景自动化平台 | 家庭私人管家：懂成员、懂作息、能记忆、可审计 |
| 判断逻辑 | 固定 if-else 自动化 | 确定性规则引擎 + 置信度校准 + 低置信 LLM 兜底 |
| 数据主权 | 依赖厂商云或平台云 | 本地优先，SQLite 本地闭环，RTSP 凭证加密 |
| 安全 | 弱鉴权或平台账号 | 网关鉴权 + 成员 RBAC + 2FA/WebAuthn + 高危设备二次确认 + 全量审计 |
| 跨生态 | 通常绑定单一品牌 | 米家 / 涂鸦 / Hue / Matter / Zigbee / Thread 统一管理 |
| 自主能力 | 固定场景自动化 | L0-L4 自主等级 + 风险评分 + 可回放审计 |
| 通知与确认 | 简单推送 | 告警 → 通知 → 待确认动作（确认 / 取消 / 过期） |
| 隐私 | 大量数据上云 | 本地模型可配，联邦学习用 Paillier 同态加密 + DP |

核心理念：把家里所有设备和成员变成一个“管家”能理解的整体，而不是一堆开关和自动化。**确定性规则引擎兜底安全（水浸 / 燃气 / 烟雾），LLM 只处理模糊地带；高风险动作永远先问人，所有决策可审计。**

## 快速开始

### 1. 安装

```bash
cd myhome-agent
pip install -e .
```

### 2. 配置

```bash
cp .env.example .env
# 编辑 .env，至少配置 DEEPSEEK_API_KEY
```

首次启动会自动生成并写入以下密钥（请妥善保管，不要分发）：

- `MYHOME_API_TOKEN`：网关 API token（前端登录页可选择 API Token 模式）
- `MYHOME_JWT_SECRET`：成员 JWT 与 2FA 签名密钥
- `MYHOME_FERNET_KEY`：RTSP 凭证加密密钥

### 3. 启动

```bash
python -m myhome_agent
```

浏览器打开 `http://localhost:8300`。首次访问会弹出登录页：可输入成员密码（需先通过管理 API 设置）或粘贴 `MYHOME_API_TOKEN`。

### 4. 常用命令

```bash
python -m myhome_agent serve          # 启动 Web 服务（默认）
python -m myhome_agent chat "家里怎么样？"
python -m myhome_agent sync           # 米家云同步（需安装 micloud）
python -m myhome_agent analyze        # 作息学习 + 异常检测
python -m myhome_agent init           # 初始化规则种子
python -m myhome_agent rules list     # 规则列表
```

## 目录结构

```text
myhome-agent/
├── myhome_agent/
│   ├── gateway/        # FastAPI 网关（REST + WebSocket）
│   ├── auth/           # API token、成员登录/RBAC、2FA、WebAuthn
│   ├── collectors/     # 设备采集适配（米家/涂鸦/Hue/Matter 等）
│   ├── memory/         # SQLite 存储
│   ├── rules/          # 规则引擎
│   ├── agent/          # LLM 客户端与 Agent 循环
│   ├── vision/         # RTSP/YOLO 视觉管线
│   ├── governance/     # 自治、配额、共识、市场
│   ├── federation/     # 联邦学习与隐私
│   └── security/       # KMS 与密钥管理
├── web/                # PWA 前端
├── docs/               # 文档
├── tests/              # pytest 单测
└── scripts/            # 硬件联调脚本
```

## API 摘要

### 认证

- `POST /api/auth/login`：成员密码登录，返回 24h JWT
- `POST /api/auth/credentials`：管理员设置成员密码
- `GET /api/auth/members`：公开成员列表（登录页使用）
- `/api/auth/2fa/*`、`/api/auth/webauthn/*`：2FA 与 FIDO2

### 家庭与设备

- `GET /api/summary`、`GET /api/devices`、`GET /api/members`、`GET /api/presence`
- `POST /api/devices/control`（高危设备需 `X-2FA-Token`）
- `POST /api/devices/control/secure`（强制 2FA）

### 规则与场景

- `GET /api/rules`、`POST /api/rules/feedback`
- `GET/POST /api/scenes`、`POST /api/scenes/run`
- `GET /api/privacy`、`POST /api/privacy/vision|llm|remote`

### 审计与待确认动作

- `GET /api/audit/rules|decisions|notifications|summary|export`
- `GET /api/actions/pending`、`POST /api/actions/{token}/confirm|cancel`

### WebSocket

- `/ws/chat`：实时对话
- `/ws/events`：告警推送（需 `?token=`）

完整端点见 [ARCHITECTURE.md](ARCHITECTURE.md#6-api-清单)。

## 配置项

| 变量 | 说明 |
|------|------|
| `DEEPSEEK_API_KEY` | 默认 LLM 密钥 |
| `MI_USERNAME` / `MI_PASSWORD` / `MI_REGION` | 米家云账号 |
| `MYHOME_DB_PATH` / `MYHOME_HOST` / `MYHOME_PORT` | 数据库与监听地址 |
| `MYHOME_API_TOKEN` / `MYHOME_JWT_SECRET` | 网关与 JWT 密钥（自动生成） |
| `MYHOME_A2A_SECRET` | 跨家庭 A2A 共享密钥 |
| `MYHOME_TELEGRAM_ALLOWED_CHAT_IDS` | Telegram chat_id 白名单 |
| `MYHOME_VISION_ENABLED` / `MYHOME_SNAPSHOT_DIR` | 视觉开关与快照目录 |
| `MYHOME_LLM_BUDGET` / `MYHOME_LLM_PREFERRED` / `MYHOME_LLM_PRIVACY` | LLM 预算与隐私模式 |

## 安全说明

- 除健康检查、登录、2FA/WebAuthn 登录外，所有 API 与 WebSocket 都需要 Bearer 凭据。
- 门锁/燃气/摄像头/主窗帘控制必须通过 2FA。
- 规则触发的直接控制动作进入 `pending_actions`，等待用户确认。
- `.env` 包含真实凭据，请设置 `600` 权限并确保不随项目分发。
- 建议使用 HTTPS 反向代理后暴露服务。

## 开发与测试

```bash
pip install -e ".[dev]"
python -m pytest
```

当前 35 项单测覆盖鉴权、2FA、规则引擎、通知、审计、钱包、共识、联邦加密与快照。

## 文档索引

- [ARCHITECTURE.md](ARCHITECTURE.md)：架构与实现现状
- [docs/CHANGELOG.md](docs/CHANGELOG.md)：变更记录
- [docs/DOCS_SYNC.md](docs/DOCS_SYNC.md)：文档同步记录
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)：部署
- [docs/REAL_PROTOCOL_TESTING.md](docs/REAL_PROTOCOL_TESTING.md)：真实协议联调

## License

MIT
