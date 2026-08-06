# 部署验证清单（v0.6）

> v0.4 已通过本地部署验证（见 D.1-D.7），v0.6 加联调清单。
> **目的**：让你（或外部贡献者）一次跑通所有功能。

## 1. 准备阶段

### 1.1 硬件

- **最低**：L1 树莓派 5 / N100 8GB
- **推荐**：L2 N100 16GB（完整跑 YOLO）
- **测试环境**：任何 Python 3.10+ 机器（你本地 PC）

### 1.2 软件

```bash
# Python 3.10+
python3 --version

# git
git --version

# curl（测 API）
curl --version
```

## 2. 安装（5 分钟）

```bash
# 1. 克隆
git clone https://github.com/your-org/myhome-agent.git
cd myhome-agent

# 2. 虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 装依赖（如果 SSL 限制，加 --trusted-host pypi.org）
pip install --trusted-host pypi.org -e ".[dev]"

# 4. 配 .env
cp .env.example .env
# 编辑：填 DEEPSEEK_API_KEY=sk-...
```

## 3. 初始化（30 秒）

```bash
myhome-agent init
# 预期：
# === myhome-agent v0.1 初始化 ===
#   ✓ 数据库表已建: ./data/myhome.db
#   ✓ 种子 5 条 P0 规则
```

## 4. CLI 验证（5 分钟）

```bash
# 4.1 规则列表
myhome-agent rules list
# 预期：5 条 P0 全部 armed

# 4.2 规则扫描
myhome-agent rules scan
# 预期：本次扫描无触发（无真实传感器）

# 4.3 命令行对话（Mock）
myhome-agent chat "你好"
# 预期：mock 模式回复

# 4.4 命令行对话（DeepSeek 真实）
myhome-agent chat "今天天气"
# 预期：DeepSeek 真实回复（如果有 API key）

# 4.5 度假模式
myhome-agent channels vacation-on
# 预期：✅ 度假模式：配额提升 1.5x
myhome-agent channels vacation-off
```

## 5. 服务验证（10 分钟）

### 5.1 启动

```bash
myhome-agent serve &
# 等待 5 秒启动
sleep 5
```

### 5.2 健康检查

```bash
curl http://localhost:8300/api/health
# 预期：{"status":"ok","version":"0.1.0","name":"myhome-agent"}
```

### 5.3 规则 API

```bash
curl http://localhost:8300/api/rules
# 预期：JSON 含 5 条规则

curl http://localhost:8300/api/rules/fallback/stats
# 预期：{"llm_available":true,"llm_model":"deepseek-chat","daily_count":0}
```

### 5.4 自治决策测试

```bash
curl -X POST http://localhost:8300/api/governance/autonomy/test \
    -H 'Content-Type: application/json' \
    -d '{"severity":"safety","irreversibility":"irreversible","member_role":"adult"}'
# 预期：{"level":"L1","risk_score":0.7,"requires_confirm":true,...}
```

### 5.5 对话 API

```bash
# 用 httpx 或 Python 测试中文（避免 curl 编码问题）
python3 -c "
import httpx
r = httpx.post('http://localhost:8300/api/chat', json={'message': '你好'})
print(r.json()['reply'][:100])
"
# 预期：DeepSeek 回复
```

### 5.6 治理配额

```bash
curl http://localhost:8300/api/governance/quotas
# 预期：{"households":[{"resources":{"llm_fallback":{"limit":10,"used":0,...}}}]}

# 度假模式 + 配额变化
curl -X POST http://localhost:8300/api/governance/vacation -H 'Content-Type: application/json' -d '{"enable":true}'
curl http://localhost:8300/api/governance/quotas
# 预期：llm_fallback.limit 变为 15
```

## 6. PWA 验证（5 分钟）

```bash
# 浏览器打开
open http://localhost:8300
```

### 6.1 聊天

- 输入"你好" → 应答
- 切换到中文 → DeepSeek 真实回复

### 6.2 规则标签

- 点击底部"规则"
- 预期：5 条 P0 规则列表（带 severity 颜色）
- 点击某条 → 详情弹窗
- 反馈 4 按钮（真异常/误报/忽略/禁用）

### 6.3 治理标签（v0.6 新增）

- 点击底部"治理"
- 预期：5 个卡片区
  - 资源配额（3 个 LLM/视觉/规则进度条）
  - 自治等级分布（L1/L2/L3 柱状图）
  - 4 维风险评分测试（下拉 + 测试按钮）
  - 决策历史（7 天 timeline）
  - 度假模式开关

### 6.4 Fire 横幅

- URL 加 `?demo=fire`
- 预期：5 秒后弹出 fire 横幅

## 7. Telegram 验证（10 分钟）

### 7.1 创建 bot

1. 打开 Telegram 搜 `@BotFather`
2. 发送 `/newbot`
3. 填名字 + username
4. 拿到 token
5. 在 `.env` 加 `TELEGRAM_BOT_TOKEN=xxx:yyy`

### 7.2 启动

```bash
myhome-agent serve  # 完整服务（含规则引擎 + API）
# 另开窗口
myhome-agent channels start-telegram
# 预期：✅ Telegram bot 启动
```

### 7.3 绑定

1. TG 搜你的 bot username
2. 发送 `/start` → 欢迎
3. 发送 `/bind 张爷爷`（家庭成员名）
4. 预期：`✅ 已绑定张爷爷！`

### 7.4 命令

```
/status    → 家庭状态
/rules     → 5 条 P0 规则列表
/devices   → 设备列表
/alerts    → 当前告警
/chat 你好 → 调 DeepSeek 对话
```

## 8. 视觉管线验证（10 分钟，需 N100+）

### 8.1 装视觉依赖

```bash
pip install --trusted-host pypi.org ultralytics opencv-python cryptography
# 首次跑会自动下 6.2MB yolov8n.pt
```

### 8.2 种子摄像头

```bash
curl -X POST http://localhost:8300/api/cameras/seed
# 预期：3 个 mock 摄像头
```

### 8.3 看视觉事件

```bash
curl 'http://localhost:8300/api/vision/events?since=60'
# 预期：空（无真实视频流）
```

### 8.4 测试图（可选）

```python
import cv2
import numpy as np

img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
cv2.imwrite('test.jpg', img)

# 用 YOLO 测
python3 -c "
import sys; sys.path.insert(0, '.')
from myhome_agent.vision.detectors import PersonDetector
det = PersonDetector()
dets = det.detect(cv2.imread('test.jpg'))
print(f'Detections: {len(dets)}')
"
```

## 9. 失败排查速查

| 症状 | 原因 | 解决 |
|------|------|------|
| `pip install` 失败 | SSL | 加 `--trusted-host pypi.org` |
| `init` GBK 报错 | Windows cmd | 已在 v0.4 修，stdio 自动 reconfigure |
| `chat` 中文 500 | curl 编码 | 用 httpx / Python 测 |
| `serve` 启动失败 | 端口占用 | `MYHOME_PORT=8301 myhome-agent serve` |
| TG bot 不响应 | token 错 | `curl https://api.telegram.org/bot<token>/getMe` 测 |
| YOLO 下载失败 | 网络 | 重试或代理 |

## 10. 完整检查表

- [ ] Python 3.10+ 装好
- [ ] `pip install -e .` 成功
- [ ] `.env` 填了 `DEEPSEEK_API_KEY`
- [ ] `myhome-agent init` 成功
- [ ] `myhome-agent rules list` 显示 5 条 P0
- [ ] `myhome-agent serve` 启动
- [ ] `/api/health` 返回 200
- [ ] `/api/chat` 中文回复（DeepSeek 真实）
- [ ] `/api/governance/quotas` 返回 3 资源
- [ ] `/api/governance/autonomy/test` 返回 L 等级
- [ ] PWA 聊天 / 规则 / 治理 3 标签正常
- [ ] TG bot `/start` `/bind` 正常
- [ ] （可选）YOLO 模型自动下 + 推理跑通

**全打勾 = 你的 myhome-agent v0.9 已完整部署。**

## 11. v0.9 实测（2026-08-04 真实跑通）

```
=== health ===         {"status":"ok","version":"0.1.0","name":"myhome-agent"} ✓
=== rules ===          5 条 P0 全部 armed ✓
=== fallback stats === {"llm_available":true,"llm_model":"deepseek-chat"} ✓
=== autonomy test ===  L1, risk=0.7, 强制 confirm ✓
=== 2fa status ===     {"enabled":false} ✓
=== chat (英文) ===    "你好呀！我是小管家..." (DeepSeek 真实) ✓
=== quotas (度假) ===  LLM 兜底 10→15 / LLM-Vision 20→30 ✓
```

**v0.9 全 8 个核心端点 PASS。**

## 12. v0.9 vs v0.7 升级清单

| 端点 | v0.7 | v0.9 |
|------|------|------|
| /api/auth/2fa/{setup,verify,disable,status} | ❌ | ✅ 4 个 |
| /api/devices/control/secure (2FA-protected) | ❌ | ✅ 占位 |
| /api/households/{id}/export | ❌ | ✅ |
| /api/households/import | ❌ | ✅ |
| /api/governance/policies | ❌ | ✅ |
| /api/governance/quotas | ✅ | ✅ + vacation |
| Web Push (manifest.json + sw.js) | ❌ | ✅ |
| WebAuthn 流程（前端 navigator.credentials） | ❌ | ✅ 后端完整 |
