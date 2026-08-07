# 真实协议联调（v2.1.1）

> **同步状态（2026-08-07）**：本文档已纳入整体同步；与当前实现的差异以 [ARCHITECTURE.md](../ARCHITECTURE.md) 状态表和 `tests/` 为准。


> v2.1.1 真实硬件联调：3 主流协议（Zigbee / Matter / Thread）实测。
> 总工期 4-6 周（v1.0.1 6-8 周基础上减半，因为协议更标准化）。

## 1. 准备（1 周）

### 1.1 硬件清单

| 协议 | 设备 | 价位 |
|------|------|------|
| **Zigbee** | ConBee II USB 适配器 + 5 个 Zigbee 设备（灯/门磁/PIR） | ¥600 |
| **Matter** | 1-2 个 Matter 设备（如 Aqara 智能灯 / Eve Energy）+ 1 个 Thread BR | ¥800 |
| **Thread** | OpenThread BR（如 Nest Hub / Apple HomePod mini / 自建 OTBR） | ¥500-1500 |
| **共需** | NAS 跑 myhome-agent + 调试笔记本 | 已有 |

### 1.2 软件依赖（v2.1.1 装包）

```bash
# Matter
# - chip-tool（源码编译，1 小时编译时间）
# https://github.com/project-chip/connectedhomeip
git clone https://github.com/project-chip/connectedhomeip
cd connectedhomeip && ./script/bootstrap
./script/build platform/raspbian
sudo make install

# Thread
# - ot-cli-ftd（OpenThread 源码）
git clone https://github.com/openthread/openthread
cd openthread && ./script/bootstrap
./script/build platform/raspbian

# Zigbee
pip install zigpy bellows   # v2.1.1 已装
```

### 1.3 后端配置

```yaml
# config/ecosystems.yaml
matter:
  backend: chip_tool
  chip_tool_path: /usr/local/bin/chip-tool
  node_id: 1
  passcode: 20202021
  discriminator: 3840

thread:
  backend: ot_ctl
  ot_ctl_path: /usr/local/bin/ot-ctl
  network_name: myhome-thread
  channel: 20

zigbee:
  backend: bellows
  radio_path: /dev/ttyUSB0
  baud: 57600
```

## 2. Matter 实测（1 周）

### 2.1 commissioning

```bash
# 1. 重置设备（按住 10s）
# 2. 运行 commissioning
chip-tool pairing ble-thread 1 20202021 3840
# 预期: Pairing Success. Device is commissioned.

# 3. 验证
myhome-agent ecosystem list
# 预期: matter_1 / OnOff Light / online
```

### 2.2 必测

- [ ] **commissioning**（setup passcode 验证）
- [ ] **OnOff toggle**（开/关）
- [ ] **Level control**（亮度 0-254）
- [ ] **ColorTemperature**（2700-6500K）
- [ ] **Multi-admin fabric**（加入 Apple Home 后仍可 myhome-agent 控制）
- [ ] **CASE 认证**（重连后无需重新 commissioning）

### 2.3 真实测试命令

```python
from myhome_agent.collectors.matter_real import RealMatterAdapter

adapter = RealMatterAdapter({
    "backend": "chip_tool",
    "chip_tool_path": "chip-tool",
})
adapter.connect()
adapter.commission(setup_passcode=20202021)

devices = adapter.discover()
print(f"发现 {len(devices)} 设备")

# 控制
for dev in devices:
    if "light" in dev.type:
        result = adapter.execute_action(dev.ecosystem_id, "light.toggle", {"on": True})
        print(f"  {dev.name}: {result}")
```

### 2.4 失败排查

| 症状 | 原因 | 解决 |
|------|------|------|
| Pairing timeout | 设备没在配对模式 | 按住 10s 重置 |
| "fabric mismatch" | 多 fabric 冲突 | Reset factory + 重试 |
| chip-tool 找不到 | PATH 问题 | 完整路径 /usr/local/bin/chip-tool |

## 3. Thread 实测（1 周）

### 3.1 Border Router 配置

```bash
# OTBR（OpenThread Border Router）启动
sudo otbr-agent \
    --radio-url "spinel+hdlc+uart:///dev/ttyACM0?uart-baudrate=115200" \
    --network-name "myhome-thread" \
    --channel 20 \
    --panid 0x1234 \
    --masterkey 00112233445566778899aabbccddeeff
```

### 3.2 必测

- [ ] **OTBR 在线**（HTTP API 200）
- [ ] **数据集导出**（active dataset -x）
- [ ] **设备配对**（commissioning，设备 5s 内入网）
- [ ] **mesh 路由**（router 节点 > 1）
- [ ] **Thread 1.3 多播**（fire 规则）
- [ ] **断电恢复**（BR 断电 5min 后自愈）

### 3.3 真实测试命令

```python
from myhome_agent.collectors.thread_real import RealThreadAdapter

adapter = RealThreadAdapter({
    "backend": "ot_ctl",
    "ot_ctl_path": "ot-ctl",
})
adapter.connect()

state = adapter.backend.get_state()
print(f"Thread state: {state['stdout']}")

devices = adapter.discover()
for dev in devices:
    print(f"  {dev.name} ({dev.type})")
```

### 3.4 失败排查

| 症状 | 原因 | 解决 |
|------|------|------|
| BR 启动失败 | 串口错 / 没权限 | `sudo usermod -aG dialout $USER` |
| 设备不入网 | PAN ID / 频道不匹配 | 检查 active dataset |
| 路由循环 | mesh 过密 | 减少 router 节点 |

## 4. Zigbee 实测（1 周）

### 4.1 USB 适配器

```bash
# 检查 USB 设备
ls -l /dev/ttyUSB*  # Linux
# Windows: 设备管理器 → COM 端口

# 装驱动（ConBee II）
sudo apt install -y deconz-dev
```

### 4.2 必测

- [ ] **bellows 启动**（无 USB 报错）
- [ ] **permit_join**（60s 标准）
- [ ] **设备配对**（按住 5s 入网）
- [ ] **OnOff 控制**（开/关 Zigbee 灯）
- [ ] **Level 控制**（亮度）
- [ ] **Cluster 读取**（温度传感器 / 门磁）
- [ ] **网络拓扑**（router / end device 区分）

### 4.3 真实测试命令

```python
from myhome_agent.collectors.zigbee_real import RealZigbeeAdapter

adapter = RealZigbeeAdapter({
    "backend": "bellows",
    "radio_path": "/dev/ttyUSB0",  # 或 COM3 (Windows)
    "baud": 57600,
})
adapter.connect()

# 允许新设备加入
adapter.permit_join(60)
# 用户在 60s 内按设备配对按钮

# 发现
devices = adapter.discover()
for dev in devices:
    print(f"  {dev.name} ({dev.type}) - {len(dev.capabilities)} caps")
```

### 4.4 失败排查

| 症状 | 原因 | 解决 |
|------|------|------|
| bellows 启动失败 | USB 串口权限 | `sudo chmod 666 /dev/ttyUSB0` |
| 设备配对失败 | 协议不匹配（Zigbee 1.2 vs 3.0）| 用 ZHA 兼容的 3.0 设备 |
| 通信频繁掉线 | 信号弱 / 干扰 | 加 router 节点中继 |

## 5. 协议互通（1 周）

### 5.1 场景：Zigbee 设备 → Apple Home 显示

```
Zigbee 设备（IKEA 灯泡）
   ↓ (Zigbee 802.15.4)
bellows (USB ConBee II)
   ↓ (MQTT / serial)
myhome-agent (RealZigbeeAdapter)
   ↓ (HomeKit bridge)
HAP-python
   ↓ (HomeKit protocol)
iOS Home app
```

### 5.2 验证互通

```python
# 1. Zigbee 设备入 myhome-agent
zigbee_adapter = RealZigbeeAdapter({'backend': 'bellows', ...})
zigbee_adapter.connect()
devices = zigbee_adapter.discover()
print(f"Zigbee 设备: {[d.name for d in devices]}")

# 2. 暴露到 HomeKit
from myhome_agent.collectors.homekit_adapter import HomeKitAdapter
hk = HomeKitAdapter({'persist_file': '~/.myhome/homekit.db'})
hk.connect()
for dev in devices:
    if 'light' in dev.type:
        hk.add_light_accessory(dev)
hk.start()  # 用户在 iOS Home app 添加
```

### 5.3 场景：Matter 设备 → iOS Home 自动发现

Matter 设备已原生支持 iOS Home。myhome-agent 加入后：

- iOS Home 看到设备
- 同时 myhome-agent 也能控制
- Multi-admin fabric 双向同步

## 6. 性能基准（1 周）

### 6.1 单协议

| 指标 | Matter | Thread | Zigbee |
|------|--------|--------|--------|
| 配对时间 | < 30s | < 5s | < 10s |
| 控制延迟 | < 200ms | < 100ms | < 150ms |
| 群组 10 设备切换 | < 1s | < 500ms | < 800ms |
| 网络节点容量 | 100+ | 250+ | 50+ |

### 6.2 多协议并存

- 同 NAS 跑 3 协议总 CPU：< 15%
- 内存：< 300MB
- 数据库 7 天增长：< 50MB

## 7. 失败恢复（1 周）

| 故障 | 恢复时间 | 预期 |
|------|---------|------|
| chip-tool 崩溃 | 5s | 自动重启（systemd） |
| OTBR 断电 | 5min | 自愈（Thread mesh 重组）|
| Zigbee USB 拔 | 1s | bellows 重连 |
| myhome-agent 重启 | 30s | 状态全部恢复 |

## 8. 检查表（v2.1.1 发布）

- [ ] Matter commissioning + 6 个 cluster 命令 PASS
- [ ] Thread mesh 3 设备入网 + 路由正常
- [ ] Zigbee bellows 5 设备入网 + 11 cluster 控制
- [ ] 3 协议并存 < 15% CPU
- [ ] 互通测试：Zigbee 灯在 iOS Home 显示
- [ ] 失败恢复 4 场景演练
- [ ] 文档 + 教程更新

## 9. 升级路径

| v2.1.1 | 真实集成 |
|--------|---------|
| v2.1.2 | Wi-Fi HaLow 远距离设备 |
| v2.1.3 | Z-Wave 北美 900MHz |
| v2.2 | Matter fabric 跨生态 multi-admin 优化 |
| v2.3 | LoRaWAN 户外传感器 |

## 10. 商业化集成

- 跨设备自动发现：用户买 Aqara 灯 → 自动入 myhome-agent
- 多生态统一控制：iOS Home / Google Home / Alexa 同时可控制
- 隐私：所有数据在 NAS（vs 米家云端）
- 切换成本：低（无需更换现有设备）

**v2.1.1 = 智能家居协议全覆盖 = 商业化差异化最强点。**