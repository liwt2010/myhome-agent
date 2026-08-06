"""ZHA 真实集成（v2.1.1）

依赖：
    pip install zigpy bellows  # 已装（v2.1.1）

zigpy = 通用 Zigbee 协议库
bellows = ZHA 用 zigpy 包装（更友好 API）

用法：
    config = {
        'radio_path': 'COM3',     # Windows USB 串口
        # 'radio_path': '/dev/ttyUSB0',  # Linux
        'baud': 57600,            # CC2652 默认
    }
    adapter = RealZigbeeAdapter(config)
    await adapter.start()
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from .ecosystem import Capability, EcosystemAdapter, EcosystemDevice
from .zigbee_adapter import (
    ZIGBEE_CLUSTERS, ZIGBEE_CLUSTER_TO_CAPABILITY,
)

logger = logging.getLogger(__name__)


# ============================================================
# bellows 真实 ZHA 适配
# ============================================================


class BellowsBackend:
    """v2.1.1 bellows（ZHA 的 Python 实现）真实集成

    bellows = Home Assistant ZHA 用的 Python 库
    直接连 USB Zigbee 适配器（CC2652 / ConBee II / ZBT-1）
    """

    def __init__(self, radio_path: str = "/dev/ttyUSB0", baud: int = 57600):
        self.radio_path = radio_path
        self.baud = baud
        self._app = None

    def connect(self) -> bool:
        try:
            import bellows
            from bellows.zigbee.application import ControllerApplication

            # bellows 0.38+ 新 API
            self._app = ControllerApplication(
                config={
                    "device": {
                        "path": self.radio_path,
                        "baudrate": self.baud,
                    },
                    "ota": {"enabled": False},  # 禁用 OTA 简化
                }
            )
            logger.info(f"bellows 启动: {self.radio_path} @ {self.baud}")
            return True
        except ImportError:
            logger.warning("bellows 未装（pip install bellows）")
            return False
        except Exception as e:
            logger.error(f"bellows 启动失败: {e}")
            return False

    async def start(self) -> None:
        if self._app:
            try:
                await self._app.start()
            except Exception as e:
                logger.error(f"bellows.start 失败: {e}")

    def get_devices(self) -> list[dict]:
        """bellows 内部 devices dict"""
        if not self._app:
            return []
        try:
            # bellows 0.38: self._app.devices = {ieee: Device}
            return [
                {
                    "ieee": str(dev.ieee),
                    "nwk": dev.nwk,
                    "manufacturer": dev.manufacturer,
                    "model": dev.model,
                    "name": dev.model if hasattr(dev, 'model') else str(dev.ieee),
                    "endpoints": {
                        ep_id: ep for ep_id, ep in (dev.endpoints or {}).items()
                    },
                    "online": dev.node_info is not None,
                }
                for dev in self._app.devices.values()
            ]
        except Exception as e:
            logger.error(f"bellows get_devices 失败: {e}")
            return []


# ============================================================
# zigpy 直接封装（备选）
# ============================================================


class ZigpyBackend:
    """v2.1.1 zigpy 直接使用（更底层）"""

    def __init__(self, radio_path: str = "/dev/ttyUSB0", baud: int = 57600):
        self.radio_path = radio_path
        self.baud = baud
        self._app = None

    def connect(self) -> bool:
        try:
            import zigpy.application
            # 串口 radio
            from zigpy.serial import Serial

            self._app = zigpy.application.ControllerApplication(
                config={
                    "device": {
                        "path": self.radio_path,
                        "baudrate": self.baud,
                    }
                }
            )
            return True
        except Exception as e:
            logger.error(f"zigpy 启动失败: {e}")
            return False


# ============================================================
# Cluster capability 映射
# ============================================================


# Cluster ID → bellows/zigpy cluster 引用（标准库自带）
BELLOWS_STANDARD_CLUSTERS = {
    0x0006: "OnOff",
    0x0008: "LevelControl",
    0x0102: "WindowCovering",
    0x0300: "ColorControl",
    0x0400: "IlluminanceMeasurement",
    0x0402: "TemperatureMeasurement",
    0x0405: "PressureMeasurement",
    0x0408: "RelativeHumidity",
    0x0500: "OccupancySensing",
    0x0501: "IasZone",
    0x0702: "Metering",
}


# ============================================================
# Real Zigbee Adapter
# ============================================================


class RealZigbeeAdapter(EcosystemAdapter):
    """v2.1.1 ZHA 真实集成（zigpy + bellows）

    直接连 USB Zigbee 适配器：
    - TI CC2652 / CC1352
    - ConBee II（deCONZ 协议）
    - ZBT-1（Zigbee 3.0）
    """

    def __init__(self, config: dict):
        super().__init__("zigbee", config)
        self.backend_type = config.get("backend", "bellows")  # 'bellows' | 'zigpy' | 'stub'
        self.radio_path = config.get("radio_path", "/dev/ttyUSB0")
        self.baud = config.get("baud", 57600)
        self.backend = None

    def connect(self) -> bool:
        if self.backend_type == "bellows":
            self.backend = BellowsBackend(self.radio_path, self.baud)
        elif self.backend_type == "zigpy":
            self.backend = ZigpyBackend(self.radio_path, self.baud)
        else:
            self._healthy = True
            logger.warning("Zigbee backend: stub（v2.1.1 真实需 USB 适配器）")
            return True

        ok = self.backend.connect()
        self._healthy = ok
        return ok

    def disconnect(self) -> None:
        self._healthy = False

    def discover(self) -> list[EcosystemDevice]:
        if not self.backend:
            return []
        if not hasattr(self.backend, "get_devices"):
            return []
        devices_raw = self.backend.get_devices()
        devices = []
        for raw in devices_raw:
            devices.append(self._bellows_to_device(raw))
        return devices

    def _bellows_to_device(self, raw: dict) -> EcosystemDevice:
        """bellows 设备 → EcosystemDevice"""
        ieee = raw.get("ieee", "")
        endpoints = raw.get("endpoints", {})

        # 收集 capability
        caps = []
        for ep_id, ep in endpoints.items():
            for cluster_id in getattr(ep, "in_clusters", []) or []:
                if cluster_id in ZIGBEE_CLUSTER_TO_CAPABILITY:
                    cap_name = ZIGBEE_CLUSTER_TO_CAPABILITY[cluster_id]
                    if not any(c.name == cap_name for c in caps):
                        caps.append(Capability(
                            name=cap_name, access="rw", source_ecosystem="zigbee",
                        ))

        # 推断类型
        type_str = "unknown"
        if any("light.toggle" in c.name for c in caps):
            type_str = "light"
        elif any("lock." in c.name for c in caps):
            type_str = "lock"
        elif any("curtain" in c.name for c in caps):
            type_str = "curtain"
        elif any("sensor.temperature" in c.name for c in caps):
            type_str = "sensor_temperature"
        elif any("sensor.ias_zone" in c.name for c in caps):
            type_str = "sensor_ias"
        elif any("sensor.water_leak" in c.name for c in caps):
            type_str = "sensor_water_leak"

        return EcosystemDevice(
            ecosystem="zigbee",
            ecosystem_id=ieee,
            name=raw.get("name", ieee[-6:]),
            type=type_str,
            online=raw.get("online", True),
            capabilities=caps,
            room="",
            model=raw.get("model", ""),
            raw_state=raw,
        )

    def get_capability(self, device_id: str) -> list[Capability]:
        for dev in self._devices.values():
            if dev.ecosystem_id == device_id:
                return dev.capabilities
        return []

    def execute_action(self, device_id: str, action: str, params=None) -> dict:
        """v2.1.1 bellows 调用 cluster command"""
        if not self.backend:
            return {"success": False, "message": "ZHA backend 未连接"}
        try:
            if self.backend_type == "bellows":
                return self._execute_bellows(device_id, action, params or {})
            return {"success": False, "message": f"{self.backend_type} 需自行实现"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def _execute_bellows(self, ieee: str, action: str, params: dict) -> dict:
        """v2.1.1 bellows 真实 cluster command"""
        if not self.backend or not self.backend._app:
            return {"success": False, "message": "bellows app 未连接"}
        try:
            device = self.backend._app.get_device(ieee)
            if not device:
                return {"success": False, "message": f"设备 {ieee} 不存在"}

            # 找 capability → cluster + command
            cluster_cmd = self._action_to_cluster_cmd(action)
            if not cluster_cmd:
                return {"success": False, "message": f"未支持: {action}"}

            cluster_name, cmd_name, value = cluster_cmd
            cluster = device.endpoints[1].in_clusters.get(cluster_name)
            if not cluster:
                return {"success": False, "message": f"设备无 {cluster_name} cluster"}

            # 调命令
            if cmd_name == "command":
                return cluster.command(cmd_name, value, **params)
            return cluster.command(cmd_name, value, **params)
        except Exception as e:
            return {"success": False, "message": str(e)}

    def _action_to_cluster_cmd(self, action: str) -> tuple | None:
        """统一 capability → bellows cluster + command"""
        MAP = {
            "light.toggle": ("OnOff", "command", "on" if True else "off"),
            "light.brightness": ("Level", "command", "move_to_level"),
            "lock.lock": ("DoorLock", "command", "lock_door"),
            "lock.unlock": ("DoorLock", "command", "unlock_door"),
            "curtain.control": ("WindowCovering", "command", "move_to_level"),
        }
        return MAP.get(action)

    def permit_join(self, duration_seconds: int = 60) -> dict:
        """v2.1.1 bellows 真实 permit_join"""
        if not self.backend or not self.backend._app:
            return {"success": False, "message": "未连接"}
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.backend._app.permit_ncp(60)  # bellows API
            loop.close()
            return {"success": True, "duration": duration_seconds}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_state(self, device_id: str) -> dict:
        if not self.backend or not self.backend._app:
            return {}
        try:
            device = self.backend._app.get_device(device_id)
            if not device:
                return {}
            # 简化为 device.__dict__ 摘要
            return {
                "ieee": str(device.ieee),
                "nwk": device.nwk,
                "manufacturer": getattr(device, "manufacturer", "unknown"),
                "model": getattr(device, "model", "unknown"),
                "endpoints": list(device.endpoints.keys()) if device.endpoints else [],
            }
        except Exception:
            return {}

    def _do_health_check(self) -> bool:
        if self.backend_type == "stub":
            return self._healthy
        return self._healthy and self.backend is not None