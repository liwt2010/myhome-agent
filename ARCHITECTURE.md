# 家庭智能体（MyHome Agent）架构设计 v0.2

> 本文档于 2026-08-07 按当前代码全量重写，取代旧 v2.x 设计稿。章节与代码模块一一对应，凡与代码冲突处以代码与 `tests/` 为准。

## 00. 实现现状对照

| 模块 | 现状 | 说明 |
|------|------|------|
| 网关鉴权 | ✅ 已实现 | 所有 REST/WS 要求 `MYHOME_API_TOKEN`（Bearer）或成员 JWT；WebSocket 走 `?token=`；仅健康检查、登录、2FA/WebAuthn 登录公开 |
| 成员登录 / RBAC | ✅ 已实现 | 密码登录（bcrypt）签发 24h 成员 JWT；角色权限矩阵已挂到控制/记忆/设置/导出/审计端点 |
| 2FA / TOTP | ✅ 已实现 | 服务端暂存 challenge，不信任客户端回传 secret；备用码 bcrypt 存储 |
| WebAuthn / FIDO2 | ✅ 已实现 | 后端 py_webauthn 真实验签，6 个端点；前端注册与登录 UI 已接通 |
| 统一审计 API | ✅ 已实现 | `/api/audit/rules\|decisions\|notifications\|summary\|export`，受 `audit.read`/`data.export` 保护 |
| 待确认控制动作 | ✅ 已实现 | 规则 `then.control` 生成 `pending_actions`，确认/取消受 RBAC + 高危设备 2FA 保护；前端确认 UI 已接 |
| A2A 跨家庭 | ✅ 已实现 | HMAC-SHA256 + 时间戳窗口 + 重放去重 + `MYHOME_A2A_SECRET` |
| Telegram 通道 | ✅ 已实现 | `MYHOME_TELEGRAM_ALLOWED_CHAT_IDS` 白名单，未授权拒绝命令 |
| 规则引擎 | ✅ 已实现 | `cooldown/window` 列迁移、`field > value` 叶子语法、`sensor.fresh`、matched 谓词收集、cooldown 到期自动 re-arm；种子规则可真实触发 |
| 视觉管线 | ⚠️ 部分 | RTSP/YOLO 调度已接线，`MYHOME_VISION_ENABLED=1` 开启；RTSP URL 加密存储；需真机验证 |
| 视觉快照访问 | ✅ 已实现 | 检测帧自动落盘 `MYHOME_SNAPSHOT_DIR`，`/api/vision/snapshots/{file}` 提供 RBAC + 防穿越访问 |
| 视觉事件联动 | ✅ 已实现 | 安全类视觉事件（fall/fire/person）自动生成告警并走通知链路 |
| 米家云同步 | ⚠️ 部分 | micloud 真实实现已接入，依赖 `pip install micloud`；需真实账号联调 |
| KMS | ⚠️ 部分 | 本地 PBKDF2 + salt 轮换 + Fernet 重加密已实现；AWS/GCP/Azure 仍为 stub |
| 联邦学习 | ⚠️ 部分 | `phe` 真实 Paillier 同态 + DP 噪声已实现；跨家庭密钥分发协议仍为简化实现 |
| Marketplace / 钱包 | ⚠️ 部分 | 基础转账、escrow 扣款与结算已实现；公开市场未对外 |
| LLM 预算路由 | ⚠️ 部分 | `LLMRouter` 已接入网关并按估算 token 记账；非精确计费 |
| SQLite | ✅ 已实现 | 连接自动 close/commit/rollback；不再跨连接误提交 |
| 前端 | ⚠️ 部分 | 登录、场景/隐私/设备控制/WebAuthn/TOTP/待确认操作已接后端；登录态持久化已实现 |
| 测试 | ✅ 已实现 | `pytest` 35 项通过（`tests/`），`scripts/` 下为硬件联调脚本不参与单测 |

**与旧设计稿的已知差异**：旧稿 §5.11“强制脱敏”未实现，LLM 请求会发送家庭摘要与工具结果；WebSocket 已加鉴权；加密聚合已从占位改为 `phe` 真实实现。

## 1. 项目概览

myhome-agent 是一个本地优先的家庭私人管家：采集家庭智能设备数据、学习作息、运行确定性规则引擎、通过 LLM 提供自然语言交互，并对自主行为做审计与二次确认。数据默认存储在本地 SQLite，云端仅用于 LLM/设备同步等可选能力。

目标定位：
- 本地优先：设备控制、规则、记忆、告警都在本机闭环。
- 可审计：规则触发、治理决策、通知投递、待确认动作全部落库并可导出。
- 安全默认：网关鉴权、2FA、RBAC、密钥托管均已落地。

## 2. 技术栈与依赖

- Python >= 3.10
- FastAPI + Uvicorn（REST + WebSocket）
- SQLite（WAL，自动建表与兼容迁移）
- OpenAI SDK（DeepSeek 等 OpenAI 兼容模型）、requests（其他 provider）
- PyJWT / pyotp / bcrypt / py_webauthn（认证与 2FA）
- cryptography / phe（密钥加密与 Paillier 同态加密）
- ultralytics / opencv-python / numpy（视觉）
- python-telegram-bot / micloud / python-miio（通道与设备）
- pytest（测试）

完整依赖见 `pyproject.toml` 与 `requirements.txt`。

## 3. 目录结构

```text
myhome-agent/
├── ARCHITECTURE.md / README.md / README.en.md / README.zh-TW.md
├── pyproject.toml / requirements.txt / .env.example / config/default.yaml
├── myhome_agent/
│   ├── __main__.py            # CLI：serve/chat/sync/import/analyze/init/rules/channels
│   ├── config.py              # 配置加载（env + YAML）
│   ├── agent/                 # LLM 客户端、Agent 循环、工具、路由
│   ├── analytics/             # 作息学习、在场推断、异常检测
│   ├── auth/                  # API token、成员登录/RBAC、2FA、WebAuthn
│   ├── channels/              # Telegram、A2A、通知队列
│   ├── collectors/            # 米家/涂鸦/Hue/Matter/Zigbee/Thread 采集适配
│   ├── federation/            # 联邦学习与隐私（Paillier + DP）
│   ├── gateway/server.py      # FastAPI 网关
│   ├── governance/            # 自治、配额、共识、市场、DPO/DPIA
│   ├── ingestion/             # CSV 导入
│   ├── memory/                # SQLite Store + schema
│   ├── rules/                 # 规则引擎、置信度、兜底、反馈
│   ├── security/              # KMS、env secret
│   └── vision/                # RTSP/文件/mock 源、YOLO 检测、调度、快照
├── web/                       # PWA（index.html / sw.js / manifest.json）
├── docs/                      # 操作、合规、设计文档
├── tests/                     # pytest 单测
└── scripts/                   # 硬件联调脚本
```

## 4. 分层架构

### 4.1 网关层（gateway/server.py）

- FastAPI 应用，挂载 WebAuthn 路由、认证中间件、REST 与 WebSocket。
- 后台任务：设备轮询、分析、通知队列消费、视觉调度（可选）。
- 生命周期使用 `lifespan` 统一管理启动/关闭。
- 全部 API（除公开路径）要求 Bearer：`MYHOME_API_TOKEN` 或成员 JWT。

### 4.2 采集层（collectors/）

- `registry.py`：统一设备注册表，负责云同步、本地轮询、控制。
- `cloud_api.py`：米家云（micloud 真实实现，缺依赖降级）。
- `local_miio.py`：本地 miio 协议轮询与控制。
- `ecosystem.py`：跨生态抽象（Capability / EcosystemAdapter）。
- `tuya_adapter.py`、`hue_adapter.py`、`matter_adapter.py`、`zigbee_adapter.py`、`thread_adapter.py`：各生态适配。
- `chip_tool_wrapper.py`、`matter_real.py`、`thread_real.py`：Matter/Thread 子进程封装。

### 4.3 存储层（memory/）

- `store.py`：SQLite 封装，`_conn()` 为自动 commit/rollback/close 的上下文管理器。
- `schema.sql`：核心业务表 + 迁移兼容（`cooldown/window` 等列）。
- 表清单见 §5。

### 4.4 分析层（analytics/）

- `routines.py`：从事件学习 first/last activity 与运动密度。
- `presence.py`：基于成员关联设备在线状态推断在场。
- `anomaly.py`：硬规则（AST 白名单求值，杜绝 `eval` 注入）+ 无活动软异常。

### 4.5 规则层（rules/）

- `engine.py`：YAML DSL 解析、谓词求值（含 `field > value` 字符串语法）、状态机（cold_start/armed/firing/cooldown，到期自动 re-arm）、扫描器、种子规则。
- `confidence.py`：4 因子置信度校准（部分因子当前为简化默认）。
- `fallback.py`：低置信 + 信号矛盾时调用 LLM 兜底（只给建议，不执行）。
- `feedback.py`：误报闭环（true_positive/false_positive/ignored/disable、自动暂停、author 撤销级联）。

### 4.6 智能体层（agent/）

- `core.py`：Agent 循环，标准 OpenAI 风格 `assistant.tool_calls + role=tool` 消息。
- `tools.py`：13 个工具（设备、成员、记忆、规则、异常等），高危控制需二次确认。
- `llm.py`：`_LLMClient` 抽象、Mock、DeepSeek（OpenAI 兼容）。
- `llm_router.py`：多 provider 能力矩阵、国产优先、预算路由（估算记账）。
- `openai_compatible.py`、`dashscope_client.py`、`zhipu_client.py`、`kimi_client.py`、`wenxin_client.py`、`local_llama_client.py`：各 provider 客户端。

### 4.7 视觉层（vision/）

- `sources.py`：RTSP（cv2 + FFMPEG、断流重连）、文件、mock 源。
- `detectors.py`：YOLOv8n person、YOLOv8n-pose 跌倒、Fire、Motion（MOG2）。
- `scheduler.py`：多摄像头并发调度、性能监控、降帧。
- `pipeline.py`：拉流 → 检测 → 事件；安全类事件自动告警 + 快照落盘。
- `vlm.py`：多模态 LLM 分析接口（DashScope/Zhipu/OpenAI/Anthropic）。
- `crypto.py`：RTSP 凭证 Fernet 加密（KMS 优先）。

### 4.8 治理层（governance/）

- `autonomy.py`：L0-L4 自主等级、4 维风险评分、决策落库。
- `quotas.py`：按时间段/度假模式动态配额（内存态）。
- `consensus.py`：简化 PBFT（多数派 quorum、防重复投票、规则 YAML 应用前校验）。
- `marketplace.py`：Agent 卡片、信誉、钱包、escrow、任务市场。
- `dpo.py` / `dpia_automation.py`：DPO 登记、季度审计、DPIA 生成。

### 4.9 联邦学习（federation/）

- `privacy.py`：真实 `phe` Paillier 同态加密 + 差分隐私（按查询次数分摊 epsilon）；明文聚合必须显式开启。
- `fedavg.py`、`auto_label.py`、`flower_adapter.py`：训练与标注管线。
- `real_fall_train.py`、`real_public_fl.py`：真实数据训练脚本。

### 4.10 渠道层（channels/）

- `telegram.py`：Telegram bot（命令 + 对话 + chat_id 白名单绑定）。
- `a2a_server.py`：A2A 消息（HMAC 验签、时间窗、重放去重、路由校验）。
- `notify.py`：通知队列（notification_queue）与 Telegram/站内投递。

### 4.11 安全层（security/ 与 auth/）

- `security/env_secret.py`：自动生成并持久化到 `.env` 的密钥。
- `security/kms.py`：本地 PBKDF2、salt 轮换、Fernet 重加密、Shamir 占位。
- `auth/api_auth.py`：网关 Bearer 校验（API token / 成员 JWT）。
- `auth/session.py`：2FA JWT 签发与校验（密钥来自 env，不再硬编码）。
- `auth/twofa.py`：TOTP + 备用码，服务端挑战流程。
- `auth/webauthn.py` + `webauthn_endpoints.py`：FIDO2 注册/登录真实验签。
- `auth/authz.py`：bcrypt 密码、成员 JWT、RBAC 权限矩阵。

## 5. 数据模型

核心表（`memory/schema.sql` 与启动迁移）：

| 表 | 用途 |
|----|------|
| `devices` | 设备目录（id/name/model/type/room/ip/token/source/online） |
| `readings` | 时序采样 |
| `events` | 离散事件（开门/运动/到达/离开等） |
| `members` | 家庭成员（role/preferences/devices JSON） |
| `presence` | 在场状态 |
| `routines` | 作息基线 |
| `alerts` | 告警（open/acked） |
| `memories` | 长期记忆 |
| `chat_history` | 对话历史 |
| `rules` / `rule_state` / `rule_audit_log` / `rule_feedback` | 规则引擎 4 表 |
| `member_2fa` / `member_webauthn` | 2FA 与 FIDO2 凭据 |
| `member_credentials` | 成员登录密码（bcrypt） |
| `notification_queue` | 通知队列 |
| `governance_decisions` | 治理决策审计 |
| `pending_actions` | 规则触发的待确认控制动作 |
| `app_settings` | 场景配置与隐私开关（key-value） |
| `cameras` / `vision_events` | 摄像头与视觉事件 |
| `wallets` / `task_escrow` / `wallet_transactions` / `agent_cards` / `market_tasks` 等 | 市场与钱包（使用方自行建表） |

## 6. API 清单

### REST

- 设备：`GET /api/devices`、`GET /api/devices/{id}`、`POST /api/devices/control`、`POST /api/devices/control/secure`
- 家庭：`GET /api/summary`、`GET /api/members`、`GET /api/presence`、`GET /api/routines`、`GET /api/events`、`GET /api/alerts`、`POST /api/alerts/{id}/ack`
- 记忆：`GET/POST /api/memories`
- 对话：`POST /api/chat`、`/ws/chat`
- 事件推送：`/ws/events`
- 规则：`GET /api/rules*`、`POST /api/rules/feedback`、`/api/rules/auto_pause_check`、`/api/rules/fallback`、`/api/rules/fallback/stats`
- 视觉：`GET /api/cameras`、`POST /api/cameras/seed`、`GET /api/vision/events`、`GET /api/vision/snapshots/{file}`
- 治理：`GET /api/governance/quotas`、`POST /api/governance/vacation`、`GET /api/governance/decisions`、`POST /api/governance/autonomy/test`、`GET /api/governance/policies`
- 场景与隐私：`GET/POST /api/scenes`、`POST /api/scenes/run`、`GET /api/privacy`、`POST /api/privacy/{vision|llm|remote}`
- 审计：`GET /api/audit/rules|decisions|notifications|summary|export`
- 待确认动作：`GET /api/actions/pending`、`POST /api/actions/{token}/confirm|cancel`
- 认证：`POST /api/auth/login`、`POST /api/auth/credentials`、`GET /api/auth/members`、`/api/auth/2fa/*`、`/api/auth/webauthn/*`
- 家庭数据：`GET /api/households/{id}/export`、`POST /api/households/import`
- 健康：`GET /api/health`

### WebSocket

- `/ws/chat`：实时对话。
- `/ws/events`：开放告警轮询推送。
- 均要求 `?token=`（API token 或成员 JWT）。

## 7. 认证与权限

### 7.1 凭据

- 管理员：`MYHOME_API_TOKEN`（自动生成或手动配置），视为 admin。
- 成员：`POST /api/auth/login`（member_id 或 name + 密码）签发 24h JWT（bcrypt 校验）。
- 2FA：TOTP 或 WebAuthn 验证后签发 30 分钟 `X-2FA-Token`。

### 7.2 RBAC 矩阵

| 权限 | admin | adult | elder | child | guest |
|------|:--:|:--:|:--:|:--:|:--:|
| chat | ✅ | ✅ | ✅ | ✅ | ✅ |
| device.control | ✅ | ✅ | ❌ | ❌ | ❌ |
| memories.write / settings.write | ✅ | ✅ | ❌ | ❌ | ❌ |
| data.export | ✅ | ✅ | ✅ | ❌ | ❌ |
| audit.read | ✅ | ✅ | ❌ | ❌ | ❌ |
| vision.read | ✅ | ✅ | ❌ | ❌ | ❌ |

### 7.3 高危控制

`lock/gas/camera/curtain_main` 类型设备的控制（含待确认动作确认）必须携带有效 `X-2FA-Token`。

## 8. 通知与审计

- 规则触发（safety/care）→ `alerts` + `notification_queue`。
- 通知消费者把 Telegram 消息发送给已绑定 chat_id 的成员，失败重试 3 次。
- 站内通知由 `/ws/events` 轮询开放告警实现。
- 审计统一由 `/api/audit/*` 提供，导出含 sha256。

## 9. 规则引擎

- DSL：YAML `when/then`，支持 `all/any/none`、数值比较、时间窗、成员与传感器谓词、`field > value` 字符串语法。
- 状态机：cold_start → armed → firing → cooldown；cooldown 到期自动 re-arm。
- 动作：`escalate` → 告警 + 通知；`control` → 生成 `pending_actions` 等待二次确认。
- 兜底：低置信 + 矛盾时调用 LLM 输出建议（不执行）。
- 反馈：误报自动暂停/禁用、置信度增减、author 撤销级联。

## 10. 视觉管线

- 源：RTSP（cv2.CAP_FFMPEG，断流指数退避重连）、文件、mock。
- 检测：YOLOv8n person、pose 跌倒、fire、MOG2 运动。
- 调度：每摄像头独立线程、性能统计、CPU 过载降帧。
- 事件：安全类事件（fall/fire/person）自动告警 + Telegram 通知 + 快照落盘。
- 访问：`/api/vision/snapshots/{file}`（RBAC + 防穿越）。
- 开关：`MYHOME_VISION_ENABLED=1`。

## 11. 隐私与安全设计

- 密钥：`MYHOME_API_TOKEN` / `MYHOME_JWT_SECRET` / `MYHOME_FERNET_KEY` 自动生成并持久化 `.env`。
- RTSP 凭证：Fernet 加密存储，不落明文。
- 联邦学习：真实 Paillier 同态 + DP；明文路径必须显式开启。
- 已知限制：LLM 请求会携带家庭摘要与工具结果，尚无自动脱敏层；敏感环境建议本地模型。

## 12. 配置与环境变量

| 变量 | 说明 |
|------|------|
| `DEEPSEEK_API_KEY` | 默认 LLM 密钥 |
| `MI_USERNAME` / `MI_PASSWORD` / `MI_REGION` | 米家云账号 |
| `MYHOME_DB_PATH` / `MYHOME_HOST` / `MYHOME_PORT` | 数据库与监听 |
| `MYHOME_API_TOKEN` / `MYHOME_JWT_SECRET` | 网关与 JWT 密钥（自动生成） |
| `MYHOME_A2A_SECRET` | A2A 共享密钥 |
| `MYHOME_TELEGRAM_ALLOWED_CHAT_IDS` | Telegram 白名单 |
| `MYHOME_VISION_ENABLED` / `MYHOME_SNAPSHOT_DIR` | 视觉开关与快照目录 |
| `MYHOME_LLM_BUDGET` / `MYHOME_LLM_CN_PCT` / `MYHOME_LLM_PREFERRED` / `MYHOME_LLM_PRIVACY` | LLM 路由预算 |
| `MYHOME_KMS_PASSPHRASE` / `MYHOME_KMS_SALT` | KMS 派生 |
| `MYHOME_FERNET_KEY` | Fernet fallback 密钥 |

## 13. 部署

- 本地：`pip install -e .` → `cp .env.example .env` → `python -m myhome_agent`。
- 生产建议：反向代理 TLS、非 root 运行、`.env` 权限 600、`git init` 基线。
- 详见 `docs/DEPLOYMENT.md`。

## 14. 测试

- `pip install -e ".[dev]"` 后 `python -m pytest`。
- 当前 35 项单测覆盖：鉴权、2FA、WebAuthn 端点、规则引擎、通知链路、审计、待确认动作、钱包、共识、联邦加密、快照。
- `scripts/` 下为硬件联调脚本，不参与单测。

## 15. 已知边界与路线图

- 真机联调：米家/Hue/Tuya/Matter/Zigbee/Thread 需真实设备与账号验证。
- LLM 预算为估算记账，非精确 token 计费。
- 联邦学习跨家庭密钥分发协议为简化实现。
- 前端 WebAuthn 登录已接；成员密码设置 UI 未做（可用管理 API）。
- 快照访问已闭环；快照自动清理/保留策略未实现。

## 16. 变更记录

- 2026-08-07：按当前代码全量重写本架构文档；README 三语化；其余 docs 加同步状态横幅，详见 `docs/DOCS_SYNC.md` 与 `docs/CHANGELOG.md`。
