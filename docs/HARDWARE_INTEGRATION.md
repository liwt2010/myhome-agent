# 真实硬件联调清单（v1.0.1）

> v1.0.1 商业化前必做——本机代码 vs 真实硬件 / 真实账号的差异。
> 完成后才能贴"v1.0.1 production ready"标签。

## 1. 摄像头实测（3 品牌 × 4 项）

### 1.1 测试品牌

| 品牌 | 型号（参考）| 价位 | RTSP URL 格式 |
|------|----------|------|---------------|
| **海康威视** | DS-2CD2043G2-I | ¥350 | `rtsp://user:pass@ip:554/Streaming/Channels/101` |
| **大华** | IPC-HDW2431T-AS | ¥400 | `rtsp://user:pass@ip:554/cam/realmonitor?channel=1&subtype=0` |
| **TP-LINK** | TL-IPC44AW | ¥300 | `rtsp://user:pass@ip:554/stream1` |

### 1.2 必测项

每台摄像头跑：

- [ ] **RTSP 拉流**（FFMPEG + OpenCV）
  ```bash
  python3 -c "
  import cv2, sys
  sys.path.insert(0, '.')
  from myhome_agent.vision.sources import RTSPCameraSource
  src = RTSPCameraSource('rtsp://user:pass@192.168.1.100:554/stream1')
  src.open()
  for _ in range(20):
      ok, frame = src.read()
      print('frame:', ok, frame.shape if frame is not None else None)
  "
  ```
  预期：20 帧全成功，shape (1080, 1920, 3) 或 (720, 1280, 3)

- [ ] **YOLOv8n 推理**
  ```bash
  python3 -c "
  from myhome_agent.vision.detectors import PersonDetector
  det = PersonDetector(device='cpu')
  # 用摄像头真实帧
  dets = det.detect(frame)
  print(f'persons: {len(dets)}')
  "
  ```
  预期：检测到 1-3 个人形，置信度 ≥ 0.6

- [ ] **断流重连**
  - 拔网线 30 秒 → 自动重连 ✓
  - 弱网（信号 -85dBm）→ 自动重连 + 3 次指数退避 ✓

- [ ] **凭证加密**（v0.3 真实）
  ```bash
  python3 -c "
  from myhome_agent.vision.crypto import encrypt, decrypt
  print(encrypt('rtsp://secret@ip'))
  print(decrypt(encrypt('rtsp://secret@ip')))
  "
  ```

### 1.3 必排除

- ❌ 小米摄像头（仅云端 RTSP，不符合隐私红线）
- ❌ 萤石 / TP-Link 仅云端（须有本地 RTSP 入口）

## 2. Telegram bot 完整流程

### 2.1 准备

1. 搜 @BotFather → /newbot → 拿 token
2. 写 .env: `TELEGRAM_BOT_TOKEN=<your-token>`
3. 启动：`myhome-agent channels start-telegram`

### 2.2 必测

- [ ] /start 欢迎消息
- [ ] /bind 张爷爷 → 绑定成功
- [ ] /chat 你好 → DeepSeek 真实回复
- [ ] /status 显示家庭状态
- [ ] /rules 列出 5 条 P0
- [ ] /devices 设备列表（v0.x 可能为空）
- [ ] /alerts 当前告警（v0.x 必为空）
- [ ] TG 群组：@bot 触发 + 不相关消息忽略

### 2.3 异常

- [ ] bot token 错 → 启动失败提示
- [ ] TG API 限流 → 自动重试
- [ ] 群组消息无 @ → 忽略

## 3. PWA 移动端实测（iOS + Android）

### 3.1 iOS（≥16.4 才支持 Web Push）

- [ ] Safari 打开 http://nas-ip:8300
- [ ] 加桌面（Safari 分享 → 加到主屏幕）
- [ ] 离线打开（飞行模式）→ 显示缓存数据
- [ ] Web Push 通知（v0.8 实测）
- [ ] 后台 7 天不打开 → 重新打开仍可加载

### 3.2 Android（Chrome）

- [ ] Chrome 打开 http://nas-ip:8300
- [ ] 加桌面（Chrome 菜单 → 加到主屏幕）
- [ ] Web Push 通知
- [ ] 离线打开

### 3.3 已知限制

| 限制 | iOS | Android |
|------|-----|---------|
| Web Push | 16.4+ | 所有 |
| 后台同步 | ❌ | ✅ |
| Service Worker 缓存 | 7 天 | 30 天+ |
| 推送到达率 | 🟡 中 | 🟢 高 |

## 4. 性能基准

### 4.1 单家庭（20 设备 / 4 摄像头 / 5 成员）

| 指标 | 目标 | 实测 |
|------|------|------|
| 服务启动 | < 5s | ? |
| 规则扫描（5 规则 × 20 设备）| < 200ms | ? |
| YOLO 单帧推理 | < 100ms | ? |
| 4 路摄像头并发 | < 400ms 总 | ? |
| LLM mock 对话 | < 200ms | ? |
| LLM DeepSeek 对话 | < 3s | ? |
| 通知路由（care 级）| < 5s | ? |
| 2FA verify | < 500ms | ? |
| Fernet 加密/解密 | < 5ms | ? |
| 备份导出 | < 30s | ? |

### 4.2 多家庭（3 家庭 / 60 设备 / 12 摄像头）

| 指标 | 目标 |
|------|------|
| 服务内存 | < 500MB |
| SQLite 单库 | < 1GB |
| CPU 空闲 | < 5% |
| CPU 峰值（4 路 + 5 规则）| < 30% |

### 4.3 压力测试

```bash
# 100 并发 /api/chat（mock）
hey -n 1000 -c 100 http://localhost:8300/api/chat

# 100 并发规则扫描
hey -n 1000 -c 100 http://localhost:8300/api/rules/scan

# 1 小时稳定性
python3 stress_test.py  # 自写脚本
```

## 5. NAS 迁移实测

### 5.1 备份

```bash
myhome-agent backup export --output myhome-test.tar.gz
ls -lh myhome-test.tar.gz
# 预期: 50-200MB（含 .db + 配置 + logs）
```

### 5.2 恢复（新机器）

```bash
# 拷备份
scp myhome-test.tar.gz new-nas:/tmp/

# 装 + 恢复
myhome-agent backup restore /tmp/myhome-test.tar.gz

# 验证
myhome-agent rules list  # 应有 5 条 P0
```

## 6. 真实家庭试用（建议 2 周）

### 6.1 招募

- 1 个老人家庭（验证老人守护）
- 1 个有娃家庭（验证儿童场景）
- 1 个独居（验证 §38 全场景）

### 6.2 反馈收集

- 误报率（rule_feedback 表统计）
- PWA 易用性（评分 1-10）
- 老人使用障碍（哪些需要 Slow Mode 强化）
- TG bot 体验
- 性能瓶颈

### 6.3 必看数据

- 老人守护场景命中率（§38 19 场景）
- 自动学习是否生效（误报率应随时间下降）
- 资源配额是否够用（动态配额自适应）

## 7. 故障场景实测

| 场景 | 预期 | 实测 |
|------|------|------|
| NAS 突然断电 | 自动恢复 + WAL | ? |
| 网络断 1h | 摄像头重连 + 通知补发 | ? |
| 数据库损坏 | 备份恢复 + WAL replay | ? |
| DeepSeek API 不可用 | LLM 降级 mock | ? |
| TG bot token 失效 | 启动报错 + 通知 admin | ? |
| 主密钥泄露 | 应急轮换 + 数据可恢复 | ? |
| 误删规则 | 7 天内可回滚（rule_history）| ? |

## 8. 联调完成检查表

- [ ] 3 品牌摄像头实测全过
- [ ] TG bot 7 命令全过
- [ ] iOS + Android PWA 实测
- [ ] 性能基准达标
- [ ] 100 并发 / 1h 稳定
- [ ] NAS 迁移测试
- [ ] 2 周真实家庭试用
- [ ] 故障场景演练

## 9. 联调人员 + 时间表

| 阶段 | 人员 | 时间 |
|------|------|------|
| 摄像头实测 | 1 人 | 1 周 |
| TG bot + PWA | 1 人 | 3 天 |
| 性能压测 | 1 人 | 1 周 |
| NAS 迁移 | 1 人 | 2 天 |
| 真实家庭试用 | 3 家庭 × 2 周 | 4 周 |

**总工期 ~6-8 周**。

## 10. 商业化发布门槛

- [ ] 摄像头 3 品牌实测
- [ ] 7 端点 100 并发 / 1h 稳定
- [ ] 真实家庭 2 周试用反馈 ≥ 8 分
- [ ] 故障演练 5 场景全过
- [ ] 第三方审计（KPMG/EY 任一）

**全过 = 可以贴 v1.0.1 production ready 标签。**