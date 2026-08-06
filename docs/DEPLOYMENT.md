# 部署指南（v0.4）

> 从 0 到能用的完整路径——含 4 类硬件档位、首次配置、摄像头接入、故障排查。

## 1. 硬件要求

| 档位 | 硬件 | RAM | 存储 | 适用 | 月度云端成本 |
|------|------|-----|------|------|-------------|
| **L1 入门** | 树莓派 5 / N100 8GB | 8GB | 64G SD / 256G SSD | ≤10 设备、纯控制 + 云端 LLM | 5-15 元 |
| **L2 推荐** | N100 / N305 小主机 | 16GB | 500G SSD | 10-30 设备、含老人守护 + 本地 1.5B | 10-30 元 |
| **L3 舒适** | i5 / M2 Mac mini | 32GB | 1TB SSD | 30-50 设备、视觉深度集成 + 本地 7B | 20-50 元 |
| **L4 升级** | RTX 3060 12GB | 32GB | 1TB SSD | ≥50 设备、本地 14B | 5-15 元 |

**单实例上限**：≤ 3 个家庭（v2.18 §1 设定，SQLite 单写者）。

## 2. 系统要求

- **OS**：Linux（Debian 12+ / Ubuntu 22.04+）/ macOS 13+ / Windows 11 WSL2
- **Python**：3.10+（推荐 3.11）
- **端口**：8300（HTTP），可选 8301（HTTPS）
- **磁盘**：≥ 10GB（含 SQLite + 快照 + 模型）
- **网络**：局域网能访问米家设备

## 3. 安装步骤

### 3.1 一键安装

```bash
# 1. 克隆
git clone https://github.com/your-org/myhome-agent.git
cd myhome-agent

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖（含 v0.3 视觉）
pip install -e .

# 4. 复制环境变量模板
cp .env.example .env

# 5. 编辑 .env（必填 DEEPSEEK_API_KEY）
nano .env
```

### 3.2 .env 必填项

```bash
# ===== 必填 =====
DEEPSEEK_API_KEY=sk-你的key              # 没有也能跑（自动降级 mock）
MYHOME_DB_PATH=./data/myhome.db
MYHOME_PORT=8300

# ===== 可选（米家集成）=====
MI_USERNAME=你的小米账号
MI_PASSWORD=你的密码
MI_REGION=cn

# ===== 自动生成（首次启动后追加）=====
MYHOME_FERNET_KEY=                    # v0.3 自动生成 + 写入 .env
```

### 3.3 初始化 + 启动

```bash
# 初始化（建表 + 种子 5 条 P0 规则 + 3 个 mock 摄像头）
myhome-agent init

# 启动服务
myhome-agent serve

# 浏览器打开
open http://localhost:8300
```

### 3.4 验证清单

```bash
# 健康检查
curl http://localhost:8300/api/health
# → {"status":"ok","version":"0.1.0","name":"myhome-agent"}

# 规则列表
myhome-agent rules list
# → 已启用规则（5 条）
#   [safety]  elderly_fall_suspect_v1  armed
#   ...

# 摄像头列表
curl http://localhost:8300/api/cameras
# → cameras: []

# 命令行对话
myhome-agent chat "你好"
# → 小管家: 你好！我是...
```

## 4. 摄像头接入（v0.3 真实视觉）

### 4.1 选型建议

- **必须支持 ONVIF / RTSP**（隐私边界）
- 推荐：海康 / 大华 / TP-LINK / 萤石（部分型号有 RTSP）
- **不要选**：只能米家云的小米摄像头（隐私红线）

### 4.2 添加摄像头

```bash
# PWA → 设置 → 摄像头 → 添加
# 填入：
#   名称: 门口
#   位置: 门口
#   RTSP URL: rtsp://admin:password@192.168.1.100:554/stream1
#   能力: motion, person, face, fire...
```

或 CLI（v0.4 计划）：

```bash
myhome-agent cameras add --name "门口" --location 门口 \
    --rtsp "rtsp://admin:xxx@192.168.1.100:554/stream1" \
    --capabilities motion,person,face
```

### 4.3 验证视觉管线

```bash
# 查看最近视觉事件
curl 'http://localhost:8300/api/vision/events?since=60'
# → events: [{kind: "person", confidence: 0.85, ...}]
```

## 5. 故障排查

### 5.1 服务起不来

| 症状 | 原因 | 解决 |
|------|------|------|
| `Address already in use` | 8300 被占 | `MYHOME_PORT=8301` |
| `permission denied` 数据目录 | 权限不足 | `chmod -R 755 data/` |
| `ModuleNotFoundError: ultralytics` | v0.3 视觉依赖未装 | `pip install ultralytics opencv-python` |
| `DEEPSEEK_API_KEY not configured` | 环境变量未设 | 编辑 `.env` 或 `export DEEPSEEK_API_KEY=...` |

### 5.2 摄像头连不上

| 症状 | 原因 | 解决 |
|------|------|------|
| 视觉事件始终为空 | RTSP URL 错 | `vlc rtsp://...` 测试 |
| 3 秒后报"打开失败" | 凭证错 | 检查用户名/密码（@ → %40） |
| 拉流卡顿 | 带宽不够 | 降低 fps（5 → 3）或换有线 |
| `cv2.error` | opencv 装错版本 | `pip install opencv-python>=4.8.0` |

### 5.3 规则不触发

| 症状 | 原因 | 解决 |
|------|------|------|
| 规则列表为空 | 未 init | `myhome-agent init` |
| 规则 cooldown 中 | 刚触发过 | 等 cooldown 到期 |
| 状态显示 disabled | 自动暂停（30 天 FP>5） | `/api/rules/auto_pause_check` 复查 |
| 永远不命中 | 谓词条件过严 | `myhome-agent rules scan` 看命中详情 |

### 5.4 LLM 兜底不工作

| 症状 | 原因 | 解决 |
|------|------|------|
| `/api/rules/fallback/stats` 显示 LLM 不可用 | DEEPSEEK_API_KEY 未设 | 配置后重启 |
| 兜底次数始终 0 | 规则没进入"低可信"区间 | 检查 confidence_base 是否合理 |

## 6. 备份与恢复

### 6.1 自动备份（每日）

```bash
# cron 任务：每天凌晨 3 点备份
0 3 * * * cd /path/to/myhome-agent && myhome-agent backup export --output /backup/myhome-$(date +\%Y\%m\%d).tar.gz
```

### 6.2 手动备份

```bash
myhome-agent backup export --output myhome-backup.tar.gz
```

打包内容：
- `data/myhome.db`（SQLite 整库）
- `config/*.yaml`
- `logs/` 最近 7 天
- **不含** `.env`（含敏感 key，需用户单独备份）

### 6.3 恢复

```bash
myhome-agent backup restore myhome-backup.tar.gz
# 自动：解压 + 校验 + 迁移
```

### 6.4 跨机器迁移

```bash
# 旧机器
scp .env new-user@new-nas:/path/to/myhome-agent/.env
scp myhome-backup.tar.gz new-user@new-nas:/tmp/

# 新机器
myhome-agent backup restore /tmp/myhome-backup.tar.gz
myhome-agent serve
```

## 7. 升级路径

```bash
# 1. 备份
myhome-agent backup export

# 2. 拉新代码
git pull origin main

# 3. 升级依赖
pip install -e . --upgrade

# 4. 跑迁移（自动）
myhome-agent serve
# 启动时自动检测 schema_meta.version + 应用新迁移
```

## 8. 安全清单

- [x] `.env` 已在 `.gitignore`，**绝不**提交
- [x] `rtsp_url` 凭证 Fernet 加密（v0.3+）
- [x] `household_id` 强制隔离（§36.6 白名单）
- [x] 上云前 redactor 脱敏（§5.11）
- [x] 控制指令二次确认（§5.3）
- [x] DeepSeek key 撤销入口：https://platform.deepseek.com/api_keys
- [ ] 防火墙限制 PWA 仅 LAN 访问（v0.4 计划）
- [ ] 自动安全更新（v0.5 计划）

## 9. 监控指标

PWA `/settings/monitoring` 可见：
- 服务 uptime
- 规则引擎扫描耗时 P50/P95/P99
- 视觉管线每摄像头延迟
- LLM 调用次数 / 兜底次数 / 当日 token
- 摄像头在线状态

## 10. 联系

- GitHub Issues：bug / 功能请求
- 项目讨论区：架构 / 集成问题
- 文档：见 README.md 链接
