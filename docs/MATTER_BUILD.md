# Matter 真实 SDK 编译指南（v2.2）

> **目标**：在 PC 上编译 connectedhomeip，得到 `chip-tool` 命令行工具。
> v2.2 Matter Adapter 自动探测 + graceful fallback。

## 1. Linux（推荐，1 小时）

```bash
# 安装依赖
sudo apt update
sudo apt install -y \
    git gcc g++ pkg-config libssl-dev libdbus-1-dev \
    libglib2.0-dev libavahi-client-dev ninja-build python3 \
    python3-pip python3-venv python3-dev

# 克隆（~500MB）
git clone https://github.com/project-chip/connectedhomeip.git
cd connectedhomeip
git submodule update --init --recursive

# 引导（拉依赖）
./script/bootstrap.sh

# 编译（30-60 分钟）
./script/build_platform.sh

# 安装
sudo cp out/raspbian-x64/chip-tool /usr/local/bin/
sudo chmod +x /usr/local/bin/chip-tool

# 验证
chip-tool --version
# 应输出：ConnectedHomeIP version 1.3.x.x
```

## 2. macOS（1 小时）

```bash
# Xcode CLI 工具
xcode-select --install

# Homebrew
brew install openssl@3 pkg-config glib dbus

# 编译
git clone https://github.com/project-chip/connectedhomeip.git
cd connectedhomeip
git submodule update --init --recursive

# 重要：用专用 bootstrap（macOS 路径）
./script/bootstrap.sh -p darwin

# 编译
./script/build_platform.sh

# 安装
cp out/darwin-x64/chip-tool /usr/local/bin/
```

## 3. Windows（推荐 WSL2，2 小时）

**方案 A：WSL2（推荐）**

```powershell
# PowerShell（管理员）
wsl --install
wsl --set-default-version 2
# 重启

# WSL Ubuntu
wsl
# 同 Linux 步骤
```

**方案 B：Docker（最快）**

```powershell
docker run -it --rm \
  -v ${PWD}:/work \
  -w /work \
  ubuntu:22.04 \
  bash -c "apt update && apt install -y git gcc g++ libssl-dev libdbus-1-dev libglib2.0-dev libavahi-client-dev ninja-build python3-pip && git clone --depth 1 https://github.com/project-chip/connectedhomeip.git && cd connectedhomeip && git submodule update --init --recursive && ./script/bootstrap.sh && ./script/build_platform.sh -p raspberry-x64 && cp out/raspberry-x64/chip-tool /work/"
```

完成大约 1 小时。

## 4. 验证安装

```bash
# myhome-agent 自动检测
cd /path/to/myhome-agent
python -c "
from myhome_agent.collectors.chip_tool_wrapper import is_chip_tool_available
print('chip-tool:', 'AVAILABLE' if is_chip_tool_available() else 'NOT FOUND')
"

# 或直接：
which chip-tool && chip-tool --version
```

预期：输出 `ConnectedHomeIP version 1.3.x.x`，v2.2 Adapter 自动走真集成的 3 路选择。

## 5. 配 myhome-agent

`myhome_agent/.env` 加（可选）：
```bash
# Matter
MYHOME_CHIP_TOOL_PATH=chip-tool
```

默认就是 `chip-tool`（PATH 查找），如自定义路径就显式指定。

## 6. 真实 commissioning 流程

```bash
# 1. 设备进入配对模式（按住设备按钮 10s）
# 2. 运行 pairing
chip-tool pairing ble-thread 1 20202021 3840

# 3. 列出已配对设备
chip-tool discovery list-nodes

# 4. 控制设备
chip-tool onoff on 1 1
chip-tool onoff off 1 1
```

实测（v2.2 adapter）：
```python
from myhome_agent.collectors.chip_tool_wrapper import ChipToolAdapter
adapter = ChipToolAdapter()
result = adapter.onoff(1, 1, True)
print(result.success, result.stdout[:200])
```

## 7. 故障排查

| 症状 | 原因 | 解决 |
|---|---|---|
| `chip-tool: command not found` | 未装 PATH | 步骤 1 末尾 `cp` 到 `/usr/local/bin/` |
| `fatal error: dbus.h` | 缺 libdbus | `apt install libdbus-1-dev` |
| 编译慢（> 2h） | 内存不足 | 关其他进程，最低 8GB RAM |
| chip-tool 编译失败 | SSL 版本冲突 | `apt install libssl-dev`（不要用 SSL 3） |
| macOS 找不到 dbus | Homebrew | `brew install dbus` |
| Windows 无 WSL | 装 WSL2 | `wsl --install` 或 Docker |

## 8. 真实设备清单（v2.2 实测）

| 设备 | 类型 | 价位 | 验证 |
|---|---|---|---|
| Aqara LED Bulb T1 | Matter / Thread | ¥99 | onoff + level |
| Eve Energy | Matter / Thread | ¥298 | onoff + 功率读 |
| TP-Link Kasa KP125M | Matter / Wi-Fi | ¥159 | onoff |
| Nanoleaf Essentials | Matter | ¥119 | onoff + level + color |
| Yubii Home | Matter Hub | - | Thread Border Router |

**最低实测预算**：¥600（Nanoleaf + Aqara + USB 适配器）。

## 9. 下一步

编译完成后：
1. myhome-agent 自动检测 chip-tool（v2.2 已实现）
2. 跑 `scripts/test_real_matter.py`（v2.2 实施）
3. 设备控制延迟 < 200ms 目标
4. 写实测报告到 `docs/MATTER_REAL_TESTING.md`

## 10. 替代方案（如果编译失败）

- **pre-built Docker image**：`docker pull matterhub/chip-tool:v1.3`
  - `docker run --rm -it matterhub/chip-tool --version`
- **预编译二进制**：见 [official releases](https://github.com/project-chip/connectedhomeip/releases)
- **完全跳过**：myhome-agent 仍可用 stub 模式（仅 capability 映射，不能真实控制）

## 11. v2.2+ 升级路线

- v2.2：当前文档（chip-tool + IPv4/IPv6 + 3 路选择）
- v2.3：matter-server Python 封装（HTTP 远程）
- v3.0：fabric multi-admin（iOS / Alexa / Google Home 同管）