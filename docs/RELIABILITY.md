# 鲁棒性与可靠性（Reliability）设计

> **同步状态（2026-08-07）**：本文档已纳入整体同步；与当前实现的差异以 [ARCHITECTURE.md](../ARCHITECTURE.md) 状态表和 `tests/` 为准。


> 系统 7×24 跑在家里，会断电、会断网、米家服务器会挂、设备会重启。不可靠的智能家居比没有还糟——家人会因此不再信任它。

## 1. 失效场景清单

| 场景 | 频率 | 影响 | 我们要做什么 |
|------|------|------|-------------|
| 单台设备暂时无响应 | 每天 | 该设备短暂掉线 | 指数退避重试 + 设备降级标记 |
| 整局域网波动 | 每周几次 | 采集失败 | 任务队列缓冲 + 批量重试 |
| 米家云端 5xx | 每月几次 | sync_from_cloud 失败 | 缓存旧 token + 延长下次重试间隔 |
| DeepSeek API 挂 | 少见 | AI 不可用 | 本地模型降级 + 提示用户 |
| 本机断电/重启 | 每月 | 全服务停止 | systemd/Docker 自动拉起 + SQLite WAL 无损恢复 |
| 数据库写失败 | 罕见 | 数据丢失 | 事务 + 失败时 enqueue 重试 |
| 配置错误改坏 | 用户操作 | 启动失败 | 启动时 schema 校验 + 清晰错误信息 |

## 2. 重试策略

### 2.1 重试矩阵

| 操作 | 重试次数 | 退避 | 总时长上限 | 失败处理 |
|------|---------|------|-----------|---------|
| 单设备轮询 | 3 | 指数 1s/2s/4s | 10s | 标记 `online=0`，下轮再试 |
| 单设备控制（用户触发） | 5 | 指数 1s/2s/4s/8s/16s | 30s | 失败后明确告知用户，记录 events 表 |
| 云端 sync_from_cloud | 3 | 指数 60s/300s/900s | 20 分钟 | 用旧 token 继续，记录告警 |
| DeepSeek API | 2 | 立即 + 5s | 15s | 降级到本地模型或明确告知 |
| SQLite 写 | 3 | 100ms/500ms/2s | 5s | 进队列稍后重试，超 3 次落盘 .dlq 文件 |
| 发送通知（微信/TG） | 3 | 立即 + 10s + 60s | 90s | 失败时尝试备用渠道 |

### 2.2 指数退避公式

```python
wait = base_delay * (2 ** attempt) + random_jitter(0, base_delay)
```

`random_jitter` 防止多设备同时重试打爆对端。

### 2.3 熔断（Circuit Breaker）

连续失败时停止调用一段时间：

```
失败 5 次 → 熔断 60s
熔断期间所有请求直接返回错误，不实际调用
60s 后进入半开状态，允许 1 次试探
试探成功 → 完全恢复
试探失败 → 再熔断 60s
```

应用对象：
- 米家云端（防止触发风控）
- DeepSeek API（防止烧钱）
- 任何外部 webhook

## 3. 任务队列

不引入 Redis/RabbitMQ，用 SQLite 自带表实现持久队列：

```sql
CREATE TABLE task_queue (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,           -- poll_device / send_notify / llm_call
    payload TEXT NOT NULL,         -- JSON
    priority INTEGER DEFAULT 5,
    retry_count INTEGER DEFAULT 0,
    next_attempt_at TEXT,          -- 下次执行时间
    created_at TEXT,
    started_at TEXT,
    finished_at TEXT,
    status TEXT DEFAULT 'pending'  -- pending/running/done/failed/dlq
);
```

工作方式：
- 工作线程从队列取任务（`UPDATE ... WHERE status='pending' AND next_attempt_at <= now ORDER BY priority, id LIMIT 1`）
- 失败时按重试矩阵更新 `next_attempt_at`，重新入队
- 重试次数超上限 → `status=dlq`，会被监控告警
- 系统重启后未完成任务自动恢复

## 4. 限流

### 4.1 出站限流（保护对端）

```
米家云端：≤ 1 次/秒
DeepSeek API：≤ 5 次/秒（按 token bucket）
单台设备：≤ 1 次/秒
通知（微信/TG）：≤ 1 次/2秒
```

实现：每个出站调用通道挂一个 `RateLimiter` 装饰器。

### 4.2 入站限流（保护自身）

```
PWA 用户请求：≤ 20 次/秒/IP
控制指令：≤ 5 次/秒/设备
LLM 调用：≤ 10 次/分钟/用户
```

## 5. 数据安全

### 5.1 SQLite 配置

```sql
PRAGMA journal_mode = WAL;          -- 允许并发读写
PRAGMA synchronous = NORMAL;        -- 性能与安全平衡
PRAGMA busy_timeout = 15000;        -- 等锁最多 15s
PRAGMA foreign_keys = ON;
```

### 5.1b 加密（v2.4 新增）

> 原生 `sqlite3` 不支持加密。家庭数据存在 NAS/小主机上，物理失窃/磁盘挂载到别的机器就能直接读到完整作息 + 成员 + 控制历史。必须考虑加密。

**选项对比**：

| 方案 | 加密强度 | 性能损耗 | 实现成本 | 优点 | 缺点 |
|------|---------|---------|---------|------|------|
| **不加密** | 0% | 0% | 0 | 简单 | 物理失窃即全露 |
| **SQLCipher** | AES-256（页面级） | 5-15% | 中（替换 sqlite3 模块） | 透明，不需要改 SQL | 多一个原生依赖（pip install pysqlcipher3） |
| **应用层加密** | AES-GCM（行级） | 自定义 | 高 | 不依赖原生 | 要重写 store.py，行级 join 受影响 |
| **磁盘加密（LUKS/EFS）** | AES（块级） | 1-3% | 取决于上层 | 一处加密全保护 | 需 Linux/eCryptfs/EFS 平台支持，macOS/Windows 不一致 |

**推荐方案：SQLCipher（默认） + 磁盘加密（可选）**

- 默认开启 SQLCipher，加密 key 来自 `MYHOME_DB_KEY` 环境变量（不入仓）
- 启动时若 key 缺失 → 自动生成、提示用户用 `pass` 备份到本地
- 用户跑 `myhome-agent doctor --check-encryption` 可验证加密是否真生效（不报 key 字面）
- 已加密库导出备份时仍加密（备份文件本身就是加密的）

**配置项**（`config/default.yaml`）：

```yaml
database:
  path: ./data/myhome.db
  # 是否加密
  encrypted: true
  # 加密 key 来源：env / file / prompted
  key_source: env
  # 备份再加密（true 推荐）
  backup_encrypted: true
```

**降级路径**：用户在 PWA 设置里关闭 `encrypted` → 下次启动前会重写库（一次性的解密迁移）；或做强制：`encrypted: required`，关闭不让启动。

**风险**：
- 丢 key = 丢全部数据 → README 必须大字强调
- SQLCipher 原生模块在 ARM 上偶尔有 pip wheels 缺失 → 必要时回退到不加密 + 加 LUKS

### 5.2 自动备份

每天凌晨 3 点：

```python
# 用 sqlite3 的 backup API 在线备份（无需停服务）
src.backup(dst, pages=1000)
```

保留策略：
- 最近 7 天的日备份：`backups/myhome-YYYY-MM-DD.db`
- 每月 1 号保留本月备份：`backups/monthly/myhome-YYYY-MM.db`
- 总大小超过 5GB 时清理最老日备份
- 备份文件若启用加密（§5.1b），需要保持加密状态不被后台明文落盘

### 5.3 启动时一致性检查

启动时跑：
- `PRAGMA integrity_check`（校验数据库没坏）
- schema 版本检查（不匹配的提示迁移）
- 设备表至少有 1 条设备（否则提示先跑 sync_from_cloud）
- 加密状态自检：`myhome-agent doctor --check-encryption`

## 6. 单点与恢复

### 6.1 进程级（v2.5：Docker Compose 为主，systemd 为可选项）

> **为什么 Docker 优先**：开源用户机器差异大（NAS、Linux 服务器、macOS、Windows）；systemd 只在 Linux 跑，macOS/Windows 没法用。Docker Compose 跨平台一致，开发/生产用同一份 compose。

#### 6.1a 主推：Docker Compose（开发与生产通用）

```yaml
# docker-compose.yml
services:
  myhome-agent:
    build: .
    container_name: myhome-agent
    restart: unless-stopped
    env_file: .env
    volumes:
      - ./data:/app/data          # SQLite 持久化
      - ./logs:/app/logs          # 日志
      - ./config:/app/config:ro   # 配置
      # 局域网访问：host 网络模式（macvlan 也可）
    network_mode: host
    healthcheck:
      test: ["CMD", "python", "-m", "myhome_agent", "doctor", "--health"]
      interval: 60s
      timeout: 10s
      retries: 3
```

**`network_mode: host` 必须**：因为 agent 需要直接访问局域网设备的 UDP 端口（miio 54321、SSDP 1900），bridge 网络会丢失广播/组播。

**image size 目标**：≤ 200MB（用 `python:3.10-slim`，免装完整 git）。

**健康检查**：`myhome-agent doctor --health` 返回 0 = 健康。`docker ps` 状态显示 `Up (healthy)`。

**常用命令**：

```bash
docker compose up -d             # 后台启动
docker compose logs -f           # 查看日志
docker compose restart           # 重启
docker compose down              # 停止（数据保留）
docker compose pull && up -d     # 升级到新版镜像
```

#### 6.1b 可选：systemd（Linux 服务器环境）

如家里只有 Linux 服务器且用 Docker 不习惯，可走 systemd：

```ini
[Unit]
Description=MiHome Agent
Documentation=https://github.com/<user>/myhome-agent
After=network-online.target              # 等网络真的在线再起
Wants=network-online.target              # 不阻塞但有提示
StartLimitIntervalSec=300
StartLimitBurst=5

[Service]
Type=simple
Restart=always
RestartSec=5
User=myhome
Group=myhome
WorkingDirectory=/opt/myhome-agent
EnvironmentFile=/opt/myhome-agent/.env    # 不入 git
ExecStartPre=/usr/bin/python3 -m myhome_agent doctor --preflight
ExecStart=/usr/bin/python3 -m myhome_agent
TimeoutStartSec=60

# 安全收口：禁止访问 ssh-agent、限制文件系统
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/myhome-agent /var/log/myhome-agent

[Install]
WantedBy=multi-user.target
```

**`ExecStartPre` 检查清单**（`doctor --preflight`）：

- `.env` 存在且关键 key 齐全
- SQLite 路径可写、加密 key 存在（如启用）
- 端口未被占用
- 设备清单不为空（或允许清单为空，初次启动）
- 磁盘有 ≥ 1GB 可用

**失败时**：systemd 记录失败原因（journald）并按 `Restart=on-failure` 重试，受 `StartLimit*` 约束避免无限重启。`TimeoutStartSec=60` 防止网络挂起阻塞启动。

**macOS / Windows（不在 systemd 平台）**：统一走 Docker Compose。开发态常驻前台可用 `docker compose up`（无 -d）。

### 6.2 数据级

- SQLite WAL 模式保证断电不丢已 commit 数据
- 缓存的设备状态重启后从 SQLite 恢复
- `pending_confirm` 表带 TTL，超时未确认自动作废

### 6.3 网络级

- 所有外部 HTTP 调用必须有超时（默认 10s，云端/LLM 30s）
- DNS 解析失败时缓存最后一次成功结果 5 分钟（抗 DNS 抖动）
- 局域网断开时进入"本地模式"：只采本地 miio，云端、通知、LLM 全暂停

## 7. 优雅降级矩阵

| 故障 | 系统表现 |
|------|---------|
| DeepSeek 挂 | 用本地模型，质量下降但可用 |
| 本地模型也挂 | 只能查预设命令，告诉用户"AI 暂不可用" |
| 米家云端挂 | 用本地缓存清单继续工作，只剩 sync_from_cloud 失败 |
| 局域网挂 | 全部功能停摆，但 PWA 还能看历史数据 |
| SQLite 挂 | 进 RB (read-only + backup) 模式，紧急备份，提醒用户 |
| 通知渠道挂 | 关键告警尝试备用渠道，其余延后重发 |

## 8. 故障演练

至少每季度做一次：

- `systemctl stop myhome-agent` 后能否自动拉起？多久？
- 拔网线 5 分钟，恢复后是否所有数据自动补传？
- 改破坏性的 yaml 配置，重启时错误信息是否足够告诉用户错在哪？
- 模拟米家云端返回 500，是否正确切换本地缓存？

## 9. 实现位置

```
myhome_agent/
├── reliability/         # 新增
│   ├── retry.py         # 重试装饰器（重试矩阵可配置）
│   ├── circuit.py       # 熔断器
│   ├── queue.py         # SQLite 任务队列
│   ├── ratelimit.py     # 限流器
│   ├── backup.py        # 自动备份 + 一致性检查
│   └── watchdog.py      # 进程自检（基础健康指标）
└── ...
```

依赖：零新增，纯 stdlib。
