"""Matter v1.3 Controller Adapter（v2.1）

Matter = 智能家居统一协议（CSA，Apple/Google/Amazon/Samsung 等共同支持）。
v1.3 支持：Wi-Fi / Thread / Ethernet 三种底层。

v2.1 实现：
- matter controller（依赖 python-matter 库，v2.1.1 真实集成）
- Commissioning（配网流程）
- Device types 映射（light / lock / thermostat / sensor）
- Cluster 映射到统一 capability
- Multi-admin fabric（多管理员场景）

v2.1.0 stub：依赖未装时降级 + capability 映射表完整。
"""
from __future__ import annotations

import logging
import time
from typing import Any

from .ecosystem import Capability, EcosystemAdapter, EcosystemDevice

logger = logging.getLogger(__name__)


# ============================================================
# Matter Device Types 与 Cluster
# ============================================================


# Matter Device Type IDs（v1.3）
MATTER_DEVICE_TYPES = {
    0x0001: "OnOffLight",
    0x0101: "OnOffLightSwitch",
    0x0103: "LightSensor",
    0x0202: "Thermostat",
    0x0204: "TemperatureSensor",
    0x0301: "DoorLock",
    0x0106: "LightSwitch",
    0x0107: "LightDimmerSwitch",
    0x0302: "DoorLockController",
    0x0100: "GenericSwitch",
    0x0201: "HeatingCoolingUnit",
    0x0500: "GenericSensor",
    0x0010: "GenericCamera",
    0x0042: "WaterLeakDetector",
    0x0043: "SmokeCoAlarm",
    0x0051: "AirQualitySensor",
}


# Matter Cluster IDs（v1.3）
MATTER_CLUSTERS = {
    0x0003: ("Identify", "r"),
    0x0004: ("Groups", "rw"),
    0x0006: ("OnOff", "rw"),
    0x0008: ("Level", "rw"),
    0x0102: "WindowCovering",
    0x0104: "ColorControl",
    0x0200: "Thermostat",
    0x0201: "TemperatureMeasurement",
    0x0202: "OccupancySensing",
    0x0204: "ThermostatUserInterface",
    0x0206: "TemperatureControl",
    0x0300: "DoorLock",
    0x0402: "IlluminanceMeasurement",
    0x0405: "HumidityMeasurement",
    0x0406: "OccupancySensing",
    0x0050: "AirQuality",
    0x0051: "CarbonMonoxideConcentrationMeasurement",
    0x0052: "CarbonDioxideConcentrationMeasurement",
    0x0098: "SmokeAlarm",
    0x0099: "WaterFreezeDetector",
    0x009A: "WaterLeakDetector",
}


# Device Type → 统一 type + 推荐 capability
MATTER_TO_UNIFIED_TYPE = {
    "OnOffLight": ("light", ["light.toggle", "light.brightness"]),
    "DimmableLight": ("light", ["light.toggle", "light.brightness"]),
    "ColorTemperatureLight": ("light", ["light.toggle", "light.brightness", "light.color_temp"]),
    "OnOffLightSwitch": ("controller", []),
    "Thermostat": ("ac", ["ac.target_temp", "ac.mode", "ac.fan_mode"]),
    "TemperatureSensor": ("sensor_temperature", ["sensor.temperature"]),
    "HumiditySensor": ("sensor_humidity", ["sensor.humidity"]),
    "DoorLock": ("lock", ["lock.lock", "lock.unlock"]),
    "LightSensor": ("sensor_light", ["sensor.illuminance"]),
    "OccupancySensor": ("sensor_occupancy", ["sensor.occupancy"]),
    "WaterLeakDetector": ("sensor_water_leak", ["sensor.water_leak"]),
    "SmokeAlarm": ("smoke_detector", ["sensor.smoke"]),
    "AirQualitySensor": ("sensor_air_quality", ["sensor.air_quality"]),
}


# Cluster ID → 统一 capability
CLUSTER_TO_CAPABILITY = {
    0x0006: "light.toggle",          # OnOff
    0x0008: "light.brightness",      # Level
    0x0104: "light.color_temp",      # ColorControl
    0x0200: "ac.target_temp",        # Thermostat
    0x0201: "sensor.temperature",    # TemperatureMeasurement
    0x0300: "lock.lock",             # DoorLock
    0x0402: "sensor.illuminance",    # IlluminanceMeasurement
    0x0405: "sensor.humidity",       # HumidityMeasurement
    0x0050: "sensor.air_quality",    # AirQuality
    0x0098: "sensor.smoke",          # SmokeAlarm
    0x009A: "sensor.water_leak",     # WaterLeakDetector
}


# ============================================================
# Adapter 实现
# ============================================================


class MatterAdapter(EcosystemAdapter):
    """v2.1 Matter controller adapter"""

    def __init__(self, config: dict):
        super().__init__("matter", config)
        self.node_id = config.get("node_id", 1)  # fabric node id
        self.fabric_id = config.get("fabric_id", "")
        self.commissioning_passcode = config.get("passcode", 20202021)
        self.commissioning_discriminator = config.get("discriminator", 3840)
        self.controller = None
        self.chip_tool_path = config.get("chip_tool_path", "chip-tool")
        self.controller = None
        self._chip_tool = None

    # ============================================================
    # 连接 / Commissioning
    # ============================================================

    def connect(self) -> bool:
        # v2.2 优先：chip-tool subprocess 真实集成
        try:
            from .chip_tool_wrapper import ChipToolAdapter, is_chip_tool_available
            if is_chip_tool_available(self.chip_tool_path):
                self._chip_tool = ChipToolAdapter(
                    chip_tool_path=self.chip_tool_path,
                    fabric_id=int(self.fabric_id) if str(self.fabric_id).isdigit() else 1,
                    node_id=self.node_id,
                )
                self._healthy = True
                logger.info(f"Matter v2.2 chip-tool 真实集成 (fabric={self.fabric_id})")
                return True
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"chip-tool 集成失败: {e}")

        # v2.1.1 fallback：python-matter SDK
        try:
            from matter_controller import MatterController  # type: ignore
            self.controller = MatterController(node_id=self.node_id, fabric_id=self.fabric_id)
            self._healthy = True
            logger.info(f"Matter controller 连接成功 (fabric={self.fabric_id})")
            return True
        except ImportError:
            logger.warning("matter-controller 未装；v2.1.0 stub 模式（仅 capability 映射）")
            self._healthy = True
            return True
        except Exception as e:
            logger.error(f"Matter controller 连接失败: {e}")
            return False


    def disconnect(self) -> None:
        self._healthy = False

    def commission(self, setup_passcode: int, device_discriminator: int = 3840) -> bool:
        """v2.1 配网流程（commissioning）"""
        if not self.controller:
            return False
        try:
            # 真实配网流程：BLE → Wi-Fi/Thread → CASE 认证 → OperationalCredentials
            return self.controller.commission(
                setup_passcode=setup_passcode,
                discriminator=device_discriminator,
            )
        except Exception as e:
            logger.error(f"Matter commission 失败: {e}")
            return False

    # ============================================================
    # 设备发现
    # ============================================================

    def discover(self) -> list[EcosystemDevice]:
        if not self.controller:
            return []
        try:
            nodes = self.controller.get_nodes()
        except Exception as e:
            logger.error(f"Matter discover 失败: {e}")
            return []

        devices = []
        for node in nodes:
            dev = self._node_to_device(node)
            devices.append(dev)
            self.register_device(dev)
        return devices

    def _node_to_device(self, node) -> EcosystemDevice:
        """Matter Node → EcosystemDevice"""
        dt_id = getattr(node, "device_type_id", 0x0001)
        dt_name = MATTER_DEVICE_TYPES.get(dt_id, "Unknown")
        type_str, cap_names = MATTER_TO_UNIFIED_TYPE.get(dt_name, ("unknown", []))

        # 提取 cluster capabilities
        caps = []
        for cluster_id in getattr(node, "clusters", []):
            cap_name = CLUSTER_TO_CAPABILITY.get(cluster_id)
            if cap_name:
                caps.append(Capability(
                    name=cap_name,
                    access="rw",
                    source_ecosystem="matter",
                    source_device_id=str(getattr(node, "node_id", "")),
                ))
        # 设备类型默认 capabilities
        for cn in cap_names:
            if not any(c.name == cn for c in caps):
                caps.append(Capability(
                    name=cn, access="rw", source_ecosystem="matter",
                ))

        return EcosystemDevice(
            ecosystem="matter",
            ecosystem_id=str(getattr(node, "node_id", "")),
            name=getattr(node, "name", f"Matter Device {dt_id:#06x}"),
            type=type_str,
            online=getattr(node, "online", True),
            capabilities=caps,
            room=getattr(node, "room", ""),
            model=getattr(node, "model", ""),
            raw_state={},
        )

    # ============================================================
    # 能力查询
    # ============================================================

    def get_capability(self, device_id: str) -> list[Capability]:
        for dev in self._devices.values():
            if dev.ecosystem_id == device_id:
                return dev.capabilities
        return []

    # ============================================================
    # 控制
    # ============================================================

    def execute_action(self, device_id: str, action: str, params=None) -> dict:
        if not self.controller:
            return {"success": False, "message": "Matter controller 未初始化"}
        try:
            # 1. 找 capability 对应的 cluster
            cluster_id = self._action_to_cluster(action)
            if not cluster_id:
                return {"success": False, "message": f"未支持的动作: {action}"}

            # 2. 构造 Matter 命令
            command = self._build_command(action, params or {})
            node_id = int(device_id)

            # 3. 调用 cluster command
            self.controller.invoke_cluster_command(
                node_id=node_id,
                cluster_id=cluster_id,
                command=command,
            )
            return {"success": True, "state": {"command": command}, "message": "OK"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def _action_to_cluster(self, action: str) -> int | None:
        """统一 capability → Matter cluster ID"""
        for cluster_id, cap in CLUSTER_TO_CAPABILITY.items():
            if cap == action:
                return cluster_id
        return None

    def _build_command(self, action: str, params: dict) -> dict:
        """构造 Matter cluster command payload"""
        if action == "light.toggle":
            return {"On": {"OnOff": params.get("on", True)}}
        if action == "light.brightness":
            return {"MoveToLevel": {"Level": params.get("brightness", 100)}}
        if action == "light.color_temp":
            return {
                "MoveToColorTemperature": {
                    "ColorTemperatureMireds": params.get("color_temp", 300)
                }
            }
        if action == "lock.lock":
            return {"LockDoor": {}}
        if action == "lock.unlock":
            return {"UnlockDoor": {}}
        if action == "ac.target_temp":
            return {"SetpointRaiseLower": {
                "Amount": int((params.get("target_temp", 22) - 22) * 100),
                "Mode": 0,  # Heat
            }}
        return {}

    def get_state(self, device_id: str) -> dict:
        if not self.controller:
            return {}
        try:
            node_id = int(device_id)
            return self.controller.read_all_attributes(node_id=node_id)
        except Exception:
            return {}

    def _do_health_check(self) -> bool:
        return self._healthy and self.controller is not None