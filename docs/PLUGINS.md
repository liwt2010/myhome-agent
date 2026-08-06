# 多品牌设备插件架构

> 短期内我们只做米家，但承认现实：很多家庭是混合设备生态（米家 + 涂鸦 + 华为 + HomeKit）。这套插件架构让接入新品牌 = 加一个目录。

## 1. 设计目标

1. 加一个品牌 ≠ 改动核心代码
2. 品牌特有逻辑（认证、协议、状态字段差异）封装在插件内
3. 上层（agent、分析、场景）面向统一抽象工作
4. 插件可以独立开发、独立测试、独立启用/禁用
5. 保留第三方贡献插件的可能

## 2. 插件契约（Plugin Interface）

每个插件实现一个类，遵守统一抽象：

```python
# myhome_agent/plugins/base.py
from abc import ABC, abstractmethod
from typing import Iterator, Any

class DevicePlugin(ABC):
    """所有设备品牌插件的基类"""
    
    # ── 元信息 ─────────────────────────
    @property
    @abstractmethod
    def brand(self) -> str:
        """品牌标识：myhome / tuya / huawei / homekit"""
    
    @property  
    def name(self) -> str:
        """人类可读品牌名"""
        return self.brand
    
    @property
    def version(self) -> str:
        return "0.1.0"
    
    # ── 生命周期 ───────────────────────
    @abstractmethod
    def configure(self, config: dict) -> None:
        """加载品牌特有配置（账号、密钥等）"""
    
    @abstractmethod
    def discover(self) -> Iterator[dict]:
        """
        扫描并产出设备。
        yield {"id": "xxx", "name": "yyy", "type": "light", 
               "brand": self.brand, "raw": {...}}
        """
    
    # ── 数据操作 ───────────────────────
    @abstractmethod
    def poll(self, device: dict) -> dict[str, Any]:
        """轮询单设备当前状态，返回 {metric: value}"""
    
    @abstractmethod
    def control(self, device: dict, action: str, params: list) -> Any:
        """对单设备下发控制指令"""
    
    # ── 可选钩子 ───────────────────────
    def sync_scenes(self) -> list[dict]:
        """同步品牌方的自动化场景（不是所有品牌都有）"""
        return []
    
    def fetch_history(self, device: dict, since: str) -> Iterator[dict]:
        """拉取设备历史日志（不是所有品牌都提供）"""
        return iter([])
    
    def supports(self, capability: str) -> bool:
        """声明能力：local_push / history / scene_sync"""
        return False
```

## 3. 数据归一化

不同品牌的"温度"字段名不同：

| 品牌 | 温度字段 | 单位 |
|------|---------|------|
| 米家 | `temperature` | ℃ |
| 涂鸦 | `temp_current` | ℃ |
| 华为 | `temp` | ℃ |
| HomeKit | `CurrentTemperature` | ℃ |

**每个插件负责把品牌字段映射到统一命名**：

```python
# 在插件内
FIELD_MAP = {
    "temp_current": "temperature",  # 涂鸦
    "hum_current": "humidity",
}

def normalize(brand_data: dict) -> dict:
    return {FIELD_MAP.get(k, k): v for k, v in brand_data.items()}
```

统一字段表放在 `myhome_agent/plugins/fields.py`，全系统唯一权威。

## 4. 插件目录与发现

```
myhome_agent/plugins/
├── base.py           # 抽象基类
├── fields.py         # 统一字段命名
├── registry.py       # 插件注册中心
├── myhome/           # 米家（已有 collectors 迁移过来）
│   ├── __init__.py
│   ├── plugin.py     # 实现 DevicePlugin
│   ├── cloud.py      # 云端 API
│   ├── local.py      # miio 直连
│   └── fields.py     # 米家字段映射
├── tuya/             # 涂鸦（未来）
│   └── ...
├── huawei/           # 华为（未来）
│   └── ...
└── homekit/          # HomeKit（未来）
    └── ...
```

### 注册方式

```python
# myhome_agent/plugins/myhome/__init__.py
from .plugin import MiHomePlugin

def register():
    return MiHomePlugin
```

主程序启动时扫描 `plugins/` 目录的子包，调用每个包的 `register()`。

### 启用配置

```yaml
# config/plugins.yaml
enabled:
  - myhome
  # - tuya          # 默认关闭
  # - homekit

myhome:
  username: ${MI_USERNAME}
  password: ${MI_PASSWORD}
  # 支持 cn / us / sg / de / in / ru 等米家 region
  # 海外华人/出国家庭需要调整；详见下文 "Region 支持"
  region: cn

tuya:
  access_id: ${TUYA_ACCESS_ID}
  access_secret: ${TUYA_SECRET}
  region: cn
```

#### Region 支持矩阵（v2.4 新增）

> 项目以中国大陆开发，但有海外用家。所有 region 不是装饰字段，必须有真实可用依据。

| region | 米家支持 | 涂鸦支持 | 备注 |
|--------|---------|---------|------|
| `cn` (默认) | ✅ 全功能 | ✅ | 国内默认 |
| `us` / `sg` / `de` / `in` / `ru` | ✅（账号体系与 cn 不通；`micloud` 需用对应 server host） | ✅ | 海外华人/出国家庭 |
| `homekit` (区域无关) | ⚠️ 后续 | ✅ | 通过 HomeKit bridge |

**region 不只是 LLM 区域**：还决定米家 API server、`micloud` 登录端点、币种时区、推送通知渠道（如 apns/fcm 区分）。**插件必须读自己的 region，禁止假定全局**。

**如何验证 region 配置正确**：`myhome-agent doctor --region` 测试登录可用性，不打真实控制指令。

## 5. 插件间通信

**插件独立，不相互调用**。共享需求通过核心层中转：

```
插件 → 核心 Store（共享 SQLite）
插件 → 核心 EventBus（发布订阅）
插件 → 核心 Metrics（上报指标）
```

例子：小米门锁的"门开"事件，可能触发华为空调的"开机"。这个联动在**场景引擎**写，不写在米家插件里：

```yaml
# config/scenes.yaml，与品牌无关
- name: 开门开空调
  when: 
    event: door_open
    device_label: 客厅门锁        # 米家设备
  then:
    - device_label: 客厅空调       # 华为设备
      action: on
      params: [{"mode": "cool"}]
```

## 6. 状态字段对齐挑战

不同品牌的"在线状态"含义不同：

| 品牌 | 在线判断 |
|------|---------|
| 米家 | miio ping 通 = 在线 |
| 涂鸦 | 云端 last_online < 60s |
| HomeKit | mDNS 能解析 = 在线 |

**插件负责给出统一抽象**：

```python
class DeviceStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"  
    UNKNOWN = "unknown"

class DevicePlugin(ABC):
    @abstractmethod
    def check_online(self, device: dict) -> DeviceStatus: ...
```

上层只看枚举值。

## 7. 新增一个品牌插件的步骤

1. **复制模板**：`cp -r plugins/_template plugins/<brand>`
2. **实现 device plugin**：写 `plugin.py`，实现抽象方法
3. **映射字段**：写 `fields.py`，把品牌字段映射到统一命名
4. **写配置 schema**：写明这个插件需要哪些配置
5. **注册**：在 `__init__.py` 写 `register()` 函数
6. **加测试**：`tests/plugins/test_<brand>.py`，至少 mock 测试
7. **加文档**：`docs/plugins/<brand>.md`，说明适用设备类型和限制

## 8. 安全与沙箱

- 插件运行在**同进程**，但调用有 wrapper 记录所有控制指令（"这个插件操作了哪些设备"）
- 高危控制（锁、燃气）的二次确认逻辑在核心层，插件绕不过
- 配置文件加密存储品牌密钥：`.env` 不入库不入 git

### 8.1 强制 `http_client` 注入（v2.4 升级）

> 原版只说"通过 http_client 注入"，没说哪些能力必须走它、违规怎样。这一节把所有出站网络调用收口到 `PluginHTTPClient`，插件代码里不允许直接调用 `requests` / `urllib` / `httpx` / 自建 socket。

**PluginHTTPClient 提供的强制能力**：

- 限流（每个 brand/region/account 独立 token bucket，§RELIABILITY 4.1）
- 熔断（连续失败自动暂停）
- 重试（指数退避）
- 超时统一
- 上云数据经 `redactor.apply()`（详见 ARCHITECTURE §5.11）
- 全链路 audit log（每个请求记到 logs/audit/）

**插件代码必须走的能力清单**（`PluginHTTPClient` 是唯一出站点）：

| 必须走 | 理由 |
|--------|------|
| 账号登录/刷新（OAuth / API key） | 有重试 + 限流 + audit |
| 设备列表拉取 | 有重试 + 熔断 |
| 设备状态轮询 | 有限流（避免触发对端风控）|
| 控制指令下发 | 有重试 + audit |
| 事件/历史日志拉取 | 有重试 + 熔断 |
| 推送通知（TG/企微/邮件） | 有重试 + 备份渠道 |
| Spec 拉取 | 有重试 + 缓存 |

**不允许直接调用的清单**（PyPI linter 在 `tests/plugins/test_no_direct_http.py` 检查）：

```python
# 这些 import 在 plugins/ 子包下都将抛 ImportError
import requests, httpx, urllib3, aiohttp      # 同/异步 HTTP
import socket, asyncio  (UDP 例外，仅 miio 协议允许)  # 部分允许
import http.client, urllib.request            # 标准库低阶
```

**检查机制**：

- `tests/plugins/test_no_direct_http.py` — AST 扫描所有 plugin .py 文件，命中即失败
- pre-commit hook：`myhome-agent-doctor --check-plugins`
- 生产模式：`logs/audit/` 里有所有出站 HTTP 请求的来源插件与目的

**UDP 例外**：局域网 miio 协议允许直接构造 UDP 数据报（python-miio 本质就是这样），但需走 `PluginUDPClient` 包装器，同样有超时/重试/限流。

### 8.2 沙箱与权限

- 插件不能写 `config/*.yaml`（由核心统一管）
- 插件不能修改其他品牌的设备
- 插件不能读 `.env`（仅读 `PluginContext.credentials`）
- 插件 crash 不会拖死主进程（独立的 try/except 包住）

## 9. 对现有代码的影响

已有的 `collectors/` 实际就是"米家插件"的雏形。改造步骤：

1. 把 `collectors/cloud_api.py` 移到 `plugins/myhome/cloud.py`
2. 把 `collectors/local_miio.py` 移到 `plugins/myhome/local.py`
3. 新建 `plugins/myhome/plugin.py`，实现 `DevicePlugin` 接口
4. `collectors/registry.py` 改为多品牌的 `PluginRegistry`：
   ```python
   class PluginRegistry:
       def __init__(self):
           self.plugins: dict[str, DevicePlugin] = {}
       
       def register(self, plugin: DevicePlugin): ...
       def discover_all(self) -> Iterator[dict]: ...
       def poll(self, device: dict) -> dict: 
           plugin = self.plugins[device["brand"]]
           return plugin.poll(device)
   ```

5. `devices` 表加 `brand` 字段，标识这条记录来自哪个插件

## 10. 什么时候引入第二个品牌

以下任一条件满足时投入：

- 用户明确要求接入非米家设备
- 米家 API 持续不稳定，需要备选方案
- 出现"米家没有但很想要"的强需求设备

否则保持单一品牌，避免过度工程。

## 11. 第三方插件的远期可能

如果未来开放第三方插件：
- 发布 `myhome-agent-plugin-template` cookiecutter 项目
- 提供 `myhome-agent-plugin-sdk` 包，把基类和工具类抽出
- 加 `plugins/external/` 目录加载第三方包
- 增加签名/权限审查机制

**当前不做**，但目录结构预留了这个可能性。

## 12. 实施路线

| 阶段 | 内容 |
|------|------|
| P0（当前） | 验证米家插件在新架构下能跑通 |
| P1 | 把 collectors 重构为插件结构，单品牌仍可用 |
| P2 | 加第二个品牌做概念验证（建议涂鸦，市场占有率高） |
| P3 | 完善插件 SDK 和测试基础设施 |
| P4 | 视用户反馈决定是否开放第三方 |
