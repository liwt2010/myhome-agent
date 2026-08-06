# 🏠 myhome-agent · 家庭私人管家

> 把家里的一切设备 + 一切家人数据，变成一个**长期陪着的私人管家**——
> 家里的事它都清楚，并能智能化处理日常琐事。

**v2.7 产品定位**：不是智能音箱助理，是懂这家人的管家。

支持多生态：第一阶段米家（最广泛用户群），架构层面对涂鸦/Hue/HomeKit 等其他品牌开放。

基于 **DeepSeek API**（v2.7 默认，国内访问稳定、成本约 Claude 1/20）+ Ollama（阶段 2 本地 LLM）的家庭智能中枢。

**v2.19 新增**：跨信号推理规则引擎（[§53](ARCHITECTURE.md) + [docs/RULES.md](docs/RULES.md)）——管家 99% 的"该发生没发生"判定不依赖 LLM，规则引擎用确定性逻辑 + 置信度校准完成；LLM 只在规则覆盖不到的模糊地带兜底。

## ✨ 核心能力

| 能力 | 说明 |
|------|------|
| 💬 自然交互 | 与管家对话，查询设备状态、控制设备、记住事项 |
| 🏠 家庭概况 | 实时查看设备在线状态、成员在场、告警汇总 |
| 📊 作息学习 | 自动学习家庭起床/就寝时间，建立活动密度基线 |
| ⚠️ 异常检测 | 硬规则（水浸/燃气泄漏）+ **v2.19 跨信号推理**（老人异常/陌生人徘徊/孩子放学未归） |
| 🧠 跨信号推理（v2.19） | 多传感器联合判定"该发生没发生"，LLM 仅在置信度低时兜底 |
| 👨‍👩‍👧‍👦 成员识别 | 门锁事件 + 关联设备信号综合判断（不开摄像头） |
| 📅 家事日历 | 自动记住家庭事务、缴费、接送、纪念日 |
| 🛒 物品追踪 | 冰箱/药箱物品 + 过期告警 |
| 🗣️ 多渠道 | PWA / 小米音箱 / Telegram（v2.19 决策：微信渠道不做） |
| 🔒 本地优先 | 数据存本地 SQLite，敏感数据加密；上云仅传脱敏摘要 |
| 🤖 自主等级 | L0-L4 per 成员 × 场景 矩阵——既敢替你决定又不失控 |
| 🎭 管家意识 | 长期人格 + 主动洞察 + 自主可审计（autonomous_id 回放） |

## 📁 项目结构

```
myhome-agent/
├── ARCHITECTURE.md          # 架构设计文档（v2.7，约 1700 行 30 个二级章节）
├── pyproject.toml           # 项目依赖
├── requirements.txt
├── .env.example             # 环境变量模板
├── config/
│   └── default.yaml         # 系统配置（轮询间隔、告警规则、autonomy 矩阵 等）
├── myhome_agent/
│   ├── __init__.py
│   ├── __main__.py          # 主入口（serve/chat/sync/import/analyze/doctor）
│   ├── config.py            # 配置加载
│   ├── collectors/          # 设备数据采集（米家为先）
│   │   ├── cloud_api.py     # 米家云端 API
│   │   ├── local_miio.py    # 局域网 miio 协议
│   │   ├── spec_norm.py     # spec 自动归一化（v2.3）
│   │   └── registry.py      # 统一设备注册表
│   ├── memory/              # SQLite 存储层
│   │   ├── schema.sql
│   │   └── store.py
│   ├── analytics/           # 家庭状态分析
│   │   ├── presence.py
│   │   ├── routines.py
│   │   └── anomaly.py
│   ├── ingestion/importer.py
│   ├── agent/               # 智能体核心（v2.7 默认 DeepSeek）
│   │   ├── core.py          # LLM 工具调用循环
│   │   ├── prompt.py
│   │   ├── persona.py       # v2.7 管家意识与人格（待补）
│   │   └── tools.py
│   ├── household/           # v2.7 家务领域（待补）
│   ├── services/            # v2.7 服务代办（待补）
│   ├── authz.py             # v2.6 RBAC（待补）
│   ├── scenes/              # v2.6 场景原子性（待补）
│   └── gateway/server.py    # FastAPI REST + WebSocket
├── web/
│   └── index.html           # PWA 前端
└── data/                    # SQLite 数据库（运行时生成）
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Windows / Linux / macOS

### 1. 安装依赖

```bash
cd myhome-agent
pip install -e .
```

或使用 requirements.txt：

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的配置
```

最少需要：

```env
# DeepSeek API Key（用于智能体对话）
DEEPSEEK_API_KEY=sk-xxxxx

# 米家账号（用于同步设备清单，可选；项目也支持涂鸦 / Hue 等后续扩展）
MI_USERNAME=your_xiaomi_account
MI_PASSWORD=your_xiaomi_password
MI_REGION=cn

# 数据库路径（默认 data/myhome.db）
# MYHOME_DB_PATH=data/myhome.db

# 服务地址（默认 0.0.0.0:8300）
# MYHOME_HOST=0.0.0.0
# MYHOME_PORT=8300
```

### 3. 启动服务

```bash
python -m myhome_agent
```

浏览器打开 `http://localhost:8300`，即可访问前端界面。

### 4. 开始使用

启动后，在聊天框中输入：

- "家里现在怎么样？"
- "帮我开客厅的灯"
- "今天家里有人吗？"
- "记住爸爸喜欢 26 度的空调"
- "明天下午 3 点接娃"

## 📖 命令行用法

```bash
# 启动 Web 服务（默认）
python -m myhome_agent serve

# 命令行对话
python -m myhome_agent chat "家里现在怎么样？"

# 同步云端设备清单
python -m myhome_agent sync

# 导入历史 CSV 数据
python -m myhome_agent import readings.csv

# 手动执行一次作息学习 + 异常检测
python -m myhome_agent analyze

# 启动前诊断（待补）
python -m myhome_agent doctor
```

## 🔧 API 参考

### REST API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查（含系统状态灯） |
| GET | `/api/summary` | 家庭概况 |
| GET | `/api/devices` | 设备列表 |
| GET | `/api/devices/{id}` | 单个设备状态 |
| POST | `/api/devices/control` | 控制设备（高危走二次确认） |
| GET | `/api/events` | 事件列表 |
| GET | `/api/members` | 成员列表 |
| GET | `/api/presence` | 在场状态 |
| GET | `/api/routines` | 作息规律 |
| GET | `/api/alerts` | 告警列表 |
| POST | `/api/alerts/{id}/ack` | 确认告警 |
| GET | `/api/memories` | 记忆检索 |
| POST | `/api/memories` | 添加记忆 |
| POST | `/api/chat` | 与管家对话 |

### WebSocket

| 路径 | 说明 |
|------|------|
| `ws/chat` | 实时对话 |
| `ws/events` | 事件/告警实时推送 |

### 对话请求示例

```json
{
  "message": "把客厅的灯关掉",
  "session_id": "abc123"
}
```

## 🧠 管家工具清单（v2.7 升级）

管家可调用的工具（按管家能力轨道分组）：

| 工具 | 描述 | 轨道 |
|------|------|------|
| `list_devices` | 列出所有设备（可按房间/类型筛选） | 设备管家 |
| `get_device_state` | 获取设备当前状态 | 设备管家 |
| `query_readings` | 查询设备历史数据 | 设备管家 |
| `query_events` | 查询家庭事件 | 设备管家 |
| `control_device` | 控制设备（按 RBAC + 渠道分级） | 设备管家 |
| `list_members` | 列出家庭成员 | 通用 |
| `get_member_status` | 查询成员在场状态 | 通用 |
| `get_home_summary` | 家庭整体概况 | 通用 |
| `get_alerts` | 查看告警 | 通用 |
| `remember` / `recall` | 长期记忆 | 通用 |
| `get_routines` | 查看作息规律 | 设备管家 |
| `add_calendar_event` | 加家事（v2.7 P1'） | 家务管家 |
| `add_item` | 加物品（v2.7 P1'） | 家务管家 |
| `book_service` | 服务代办（v2.7 P2） | 服务管家 |
| `check_autonomous_history` | 查自主行为历史 | 通用（v2.6 §18） |

## ⚙️ 配置说明

### config/default.yaml

```yaml
home:
  timezone: Asia/Shanghai      # IANA 时区，开源用户必填
  locale: zh-CN

collect:
  local_poll_interval: 60
  cloud_sync_interval: 3600

analytics:
  interval: 300
  routine_window_days: 30
  inactivity_grace_minutes: 180

agent:
  model: deepseek-chat         # DeepSeek V3.x（默认）
  max_tokens: 16000
  history_turns: 30

autonomy:                       # v2.7 自主等级矩阵
  default_level: 2              # L2 默认
  budget_per_order: 200         # 大额二次确认
  ...

control_confirm:
  - lock
  - gas
  - camera
  - curtain_main
```

### .env 配置项

| 变量 | 必填 | 说明 |
|------|------|------|
| `DEEPSEEK_API_KEY` | ✅ | DeepSeek API 密钥 |
| `MI_USERNAME` | 可选 | 米家账号（用于云端同步） |
| `MI_PASSWORD` | 可选 | 米家密码 |
| `MI_REGION` | 可选 | 区域：cn / sg / us 等（默认 cn） |
| `MYHOME_DB_PATH` | 可选 | SQLite 路径（默认 data/myhome.db） |
| `MYHOME_HOST` | 可选 | 服务监听地址（默认 0.0.0.0） |
| `MYHOME_PORT` | 可选 | 服务端口（默认 8300） |

## 🔒 隐私设计（v2.7）

1. **本地存储**：所有数据存本地 SQLite；健康/账本（v2.7 P2）加密存
2. **强制脱敏**：所有上云 payload 100% 经过 `redactor.py`（架构 §5.11）
3. **最小云端传输**：调用 LLM 时只传脱敏后的家庭摘要 + 用户提问，不传原始设备日志
4. **硬规则告警**：水浸/燃气泄漏等紧急告警不经过 LLM，直接触发本地告警
5. **可审计**：每轮对话 + 每个自主行为（autonomous_id）记录到 SQLite，可完整回放
6. **regulator 友好**：开源项目不持有支付凭证；服务代办仅发起 API 调用，资金走用户账号

## 🛠️ 开发

### 运行测试（架构持续补全）

```bash
# 智能体离线测试（可选依赖）
python -c "
from myhome_agent.memory.store import Store
from myhome_agent.analytics.routines import routine_summary
s = Store(':memory:')
print(routine_summary(s))
"
```

### 模块间耦合

- `collectors/`：与设备通讯，写入 `store`
- `memory/`：SQLite 封装，所有模块只通过 `Store` 存取
- `analytics/`：从 `store` 读，产出作息/异常，写回 `store`
- `agent/`：通过 `Store` + `Registry` 拼上下文，调用 LLM
- `household/` (v2.7)：家务领域逻辑（物品/日历/健康/账本）
- `services/` (v2.7)：服务代办 adapter 集合
- `gateway/`：FastAPI 服务，暴露 REST / WebSocket

模块间只通过 `Store` 传递数据，松耦合。

## 📖 进一步阅读

- [ARCHITECTURE.md](ARCHITECTURE.md) — 完整架构设计（v2.2，~22200 行 / 21 文档 / Matter 真实 SDK 集成）
- [docs/TODO.md](docs/TODO.md) — 待办事项 / 待优化项（v3.0.1 收尾）
- [docs/REAL_PROTOCOL_TESTING.md](docs/REAL_PROTOCOL_TESTING.md) — 真实协议联调
- [docs/REAL_WORLD_TESTING.md](docs/REAL_WORLD_TESTING.md) — 真实家庭试用
- [docs/ISO27001.md](docs/ISO27001.md) — ISO 27001
- [docs/SOC2.md](docs/SOC2.md) — SOC2 Type II
- [docs/AUDIT_CHECKLIST.md](docs/AUDIT_CHECKLIST.md) — 第三方审计
- [docs/HARDWARE_INTEGRATION.md](docs/HARDWARE_INTEGRATION.md) — 真实硬件联调
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — 部署指南
- [docs/DEPLOY_VERIFICATION.md](docs/DEPLOY_VERIFICATION.md) — 联调清单
- [docs/DPIA.md](docs/DPIA.md) — GDPR DPIA
- [docs/DPA.md](docs/DPA.md) — 数据保护协议 + DPO
- [docs/CHANNELS.md](docs/CHANNELS.md) — 渠道集成
- [docs/GOVERNANCE.md](docs/GOVERNANCE.md) — 治理框架
- [docs/RULES.md](docs/RULES.md) — 规则 DSL + 16 视觉规则
- [docs/UX_FLOWS.md](docs/UX_FLOWS.md) — PWA 流程
- [docs/SCHEMA.md](docs/SCHEMA.md) — 字段定义
- [docs/SERVICES.md](docs/SERVICES.md) — 服务代办
- [docs/HOUSEHOLD.md](docs/HOUSEHOLD.md) — 家务数据模型
- [docs/PLUGINS.md](docs/PLUGINS.md) — 跨生态插件

## 📄 License

MIT License — 详见 LICENSE 文件
