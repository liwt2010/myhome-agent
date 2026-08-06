"""跨生态 adapter 抽象（v2.0 §64）

v2.0 实现：
- 统一 EcosystemAdapter 抽象类（米家/涂鸦/Hue/HomeKit 全部实现）
- capability 标准化（不同生态 → 统一 capability 模型）
- 自动发现 + 健康监控 + 错误处理

v2.0 不做：
- Matter / Thread（v2.1 计划）
- Z-Wave（v2.1 计划）
- Zigbee 直连（v2.1 计划）
"""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================
# 统一 capability 模型
# ============================================================


@dataclass
class Capability:
    """跨生态统一 capability"""

    name: str  # 'light.toggle' | 'ac.adjust_temp' | 'lock.unlock' | ...
    access: str = "rw"  # 'r' | 'w' | 'rw'
    params: list = field(default_factory=list)  # [{name, type, required}]
    source_ecosystem: str = ""  # 'mihome' | 'tuya' | 'hue' | 'homekit'
    source_device_id: str = ""  # 原始生态 ID
    confidence: float = 1.0  # capability 映射置信度（0-1）


@dataclass
class EcosystemDevice:
    """跨生态统一设备"""

    ecosystem: str  # 'mihome' | 'tuya' | 'hue' | 'homekit'
    ecosystem_id: str  # 生态内 ID
    name: str
    type: str  # 'light' | 'ac' | 'lock' | 'sensor' | ...
    online: bool = True
    capabilities: list = field(default_factory=list)  # Capability[]
    room: str = ""
    model: str = ""
    raw_state: dict = field(default_factory=dict)


# ============================================================
# Adapter 抽象
# ============================================================


class EcosystemAdapter(ABC):
    """v2.0 跨生态 adapter 抽象基类

    所有具体 adapter（米家 / 涂鸦 / Hue / HomeKit）必须继承：
    - discover()：发现设备
    - get_capability()：取 capability 列表
    - execute_action()：执行控制
    - get_state()：读状态
    - subscribe_events()：订阅推送（可选）
    - health_check()：健康检查
    """

    def __init__(self, name: str, config: dict):
        self.name = name  # 'mihome' / 'tuya' / 'hue' / 'homekit'
        self.config = config
        self._devices: dict[str, EcosystemDevice] = {}
        self._last_health: float = 0.0
        self._healthy: bool = False

    @abstractmethod
    def connect(self) -> bool:
        """建立连接（OAuth / Bridge / Token）"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def discover(self) -> list[EcosystemDevice]:
        """发现所有设备"""
        pass

    @abstractmethod
    def get_capability(self, device_id: str) -> list[Capability]:
        """取设备的 capability 列表"""
        pass

    @abstractmethod
    def execute_action(self, device_id: str, action: str, params: dict | None = None) -> dict:
        """执行控制动作

        Returns:
            {"success": bool, "state": dict, "message": str}
        """
        pass

    @abstractmethod
    def get_state(self, device_id: str) -> dict:
        """读设备当前状态"""
        pass

    def subscribe_events(self, callback) -> bool:
        """订阅推送事件（可选，v2.0 stub 默认 False）"""
        return False

    def health_check(self) -> dict:
        """健康检查"""
        now = time.time()
        try:
            # 子类可 override
            ok = self._do_health_check()
        except Exception as e:
            ok = False
            logger.error(f"{self.name} health_check 失败: {e}")

        self._healthy = ok
        self._last_health = now

        return {
            "ecosystem": self.name,
            "healthy": ok,
            "checked_at": now,
            "device_count": len(self._devices),
        }

    def _do_health_check(self) -> bool:
        """v2.0 默认：返回 connect 状态"""
        return self._healthy

    # ============================================================
    # 工具
    # ============================================================

    def normalize_capability(self, ecosystem_cap: str) -> str | None:
        """生态特定 capability 名 → 统一 capability 名

        v2.0 映射表（不同生态的 capability 名 → 统一名）：
        - 'switch_1' (Tuya) → 'light.toggle'
        - 'bright_value' (Hue) → 'light.brightness'
        - 'OnOff' (HomeKit) → 'light.toggle'
        """
        MAP = {
            # Tuya
            "switch_1": "light.toggle",
            "switch_led": "light.toggle",
            "bright_value": "light.brightness",
            "temp_value": "light.color_temp",
            "colour_data": "light.color",
            # Hue
            "on": "light.toggle",
            "bri": "light.brightness",
            "ct": "light.color_temp",
            "hue": "light.color_hue",
            "sat": "light.color_saturation",
            # HomeKit
            "OnOff": "light.toggle",
            "Brightness": "light.brightness",
            "Hue": "light.color_hue",
            "Saturation": "light.color_saturation",
            "CurrentTemperature": "sensor.temperature",
            "TargetTemperature": "ac.target_temp",
            # 米家（已有）
            "set_power": "light.toggle",
            "set_bright": "light.brightness",
        }
        return MAP.get(ecosystem_cap)

    def register_device(self, device: EcosystemDevice):
        """缓存设备"""
        self._devices[device.ecosystem_id] = device

    def get_devices_by_type(self, device_type: str) -> list[EcosystemDevice]:
        return [d for d in self._devices.values() if d.type == device_type]


# ============================================================
# Adapter 工厂
# ============================================================


def create_adapter(ecosystem: str, config: dict) -> EcosystemAdapter:
    """v2.0 工厂"""
    if ecosystem == "mihome":
        from .local_miio import LocalMiioCollector
        # v0.1 已存在，转为 adapter 接口
        return _MiHomeAdapterShim(LocalMiioCollector(), config)
    elif ecosystem == "tuya":
        from .tuya_adapter import TuyaAdapter
        return TuyaAdapter(config)
    elif ecosystem == "hue":
        from .hue_adapter import HueAdapter
        return HueAdapter(config)
    elif ecosystem == "homekit":
        from .homekit_adapter import HomeKitAdapter
        return HomeKitAdapter(config)
    else:
        raise ValueError(f"未知 ecosystem: {ecosystem}")


class _MiHomeAdapterShim(EcosystemAdapter):
    """v0.1 LocalMiioCollector → v2.0 EcosystemAdapter 适配"""

    def __init__(self, miio_collector, config):
        super().__init__("mihome", config)
        self._miio = miio_collector

    def connect(self) -> bool:
        return True

    def disconnect(self) -> None:
        pass

    def discover(self) -> list[EcosystemDevice]:
        # v0.1 已实现 sync_from_cloud + local_poll
        return []

    def get_capability(self, device_id: str) -> list[Capability]:
        return []

    def execute_action(self, device_id: str, action: str, params=None) -> dict:
        return self._miio.control(device_id, action, params)

    def get_state(self, device_id: str) -> dict:
        return {}