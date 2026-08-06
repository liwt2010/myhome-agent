"""Zigbee 桥接 Adapter（v2.1）

Zigbee = 智能家居最成熟的 mesh 协议（1998 起，10+ 亿设备）。
v2.1 支持 3 种桥接：
- Zigbee2MQTT（推荐，开源）
- deCONZ（Phoscon，REST API）
- ZHA（Home Assistant 内置）

依赖硬件：USB Zigbee 适配器（TI CC2652 / ConBee II / ZBT-1）。
"""
from __future__ import annotations

import logging
import time
from typing import Any

from .ecosystem import Capability, EcosystemAdapter, EcosystemDevice

logger = logging.getLogger(__name__)


# Zigbee Cluster IDs
ZIGBEE_CLUSTERS = {
    0x0000: "Basic",
    0x0001: "PowerConfiguration",
    0x0003: "Identify",
    0x0004: "Groups",
    0x0005: "Scenes",
    0x0006: "OnOff",
    0x0008: "LevelControl",
    0x0102: "WindowCovering",
    0x0200: "PollControl",
    0x0201: "GreenPower",
    0x0202: "AnalogInput",
    0x0204: "AnalogOutput",
    0x0300: "ColorControl",
    0x0400: "IlluminanceMeasurement",
    0x0402: "TemperatureMeasurement",
    0x0405: "PressureMeasurement",
    0x0406: "FlowMeasurement",
    0x0408: "RelativeHumidity",
    0x0500: "OccupancySensing",
    0x0501: "IASZone",          # 安全传感器
    0x0502: "IASACE",
    0x0503: "IASWD",
    0x0702: "Metering",
    0x0B04: "ElectricalMeasurement",
}

# Cluster → 统一 capability
ZIGBEE_CLUSTER_TO_CAPABILITY = {
    0x0006: "light.toggle",
    0x0008: "light.brightness",
    0x0102: "curtain.control",
    0x0300: "light.color",
    0x0400: "sensor.illuminance",
    0x0402: "sensor.temperature",
    0x0408: "sensor.humidity",
    0x0500: "sensor.occupancy",
    0x0501: "sensor.ias_zone",   # 门 / 窗 / 烟雾 / 漏水
    0x0702: "sensor.power",
    0x0B04: "sensor.power",
}


class ZigbeeAdapter(EcosystemAdapter):
    """v2.1 Zigbee 桥接 adapter（Zigbee2MQTT / deCONZ / ZHA）"""

    def __init__(self, config: dict):
        super().__init__("zigbee", config)
        self.bridge_type = config.get("bridge_type", "zigbee2mqtt")  # 'zigbee2mqtt'|'deconz'|'zha'
        self.bridge_url = config.get("bridge_url", "http://localhost:8080")
        self.mqtt_broker = config.get("mqtt_broker", "localhost")
        self.mqtt_port = config.get("mqtt_port", 1883)
        self._client = None

    # ============================================================
    # 连接
    # ============================================================

    def connect(self) -> bool:
        if self.bridge_type == "zigbee2mqtt":
            return self._connect_z2m()
        elif self.bridge_type == "deconz":
            return self._connect_deconz()
        elif self.bridge_type == "zha":
            return self._connect_zha()
        else:
            logger.error(f"未知 bridge_type: {self.bridge_type}")
            return False

    def disconnect(self) -> None:
        self._healthy = False
        if self._client and self.bridge_type == "zigbee2mqtt":
            try:
                self._client.loop_stop()
                self._client.disconnect()
            except Exception:
                pass

    def _connect_z2m(self) -> bool:
        """v2.1 Zigbee2MQTT 桥接（推荐）"""
        try:
            import requests
            r = requests.get(f"{self.bridge_url}/api/health", timeout=5)
            if r.status_code == 200:
                self._healthy = True
                logger.info(f"Zigbee2MQTT 连接成功 ({self.bridge_url})")
                return True
            return False
        except Exception as e:
            logger.error(f"Zigbee2MQTT 连接失败: {e}")
            return False

    def _connect_deconz(self) -> bool:
        try:
            import requests
            r = requests.get(f"{self.bridge_url}/api", timeout=5)
            if r.status_code == 200:
                self._healthy = True
                return True
            return False
        except Exception as e:
            logger.error(f"deCONZ 连接失败: {e}")
            return False

    def _connect_zha(self) -> bool:
        """ZHA（Home Assistant 内置）— v2.1.1 真实集成"""
        try:
            import requests
            r = requests.get(f"{self.bridge_url}/api/services", timeout=5)
            self._healthy = r.status_code == 200
            return self._healthy
        except Exception as e:
            logger.error(f"ZHA 连接失败: {e}")
            return False

    # ============================================================
    # 设备发现
    # ============================================================

    def discover(self) -> list[EcosystemDevice]:
        if self.bridge_type == "zigbee2mqtt":
            return self._discover_z2m()
        elif self.bridge_type == "deconz":
            return self._discover_deconz()
        return []

    def _discover_z2m(self) -> list[EcosystemDevice]:
        try:
            import requests
            r = requests.get(f"{self.bridge_url}/api/devices", timeout=10)
            devices_data = r.json()
        except Exception as e:
            logger.error(f"Z2M discover 失败: {e}")
            return []

        devices = []
        for ieee, info in devices_data.items():
            dev = self._z2m_to_device(ieee, info)
            devices.append(dev)
            self.register_device(dev)
        return devices

    def _z2m_to_device(self, ieee: str, info: dict) -> EcosystemDevice:
        """Zigbee2MQTT device → EcosystemDevice"""
        friendly_name = info.get("friendly_name", ieee)
        definition = info.get("definition", {})
        model = definition.get("model", "Unknown")
        vendor = definition.get("vendor", "")
        exposes = definition.get("exposes", [])

        # 类型推断（基于 exposes）
        type_str = "unknown"
        caps = []
        for ex in exposes:
            feature = ex.get("type", "")
            name = ex.get("property", "")
            if feature == "binary":
                type_str = "light" if "state" in name else "sensor_binary"
                caps.append(Capability(
                    name="light.toggle" if "state" in name else f"sensor.{name}",
                    access="rw" if type_str == "light" else "r",
                    source_ecosystem="zigbee",
                ))
            elif feature == "numeric":
                caps.append(Capability(
                    name=f"sensor.{name}",
                    access="r",
                    source_ecosystem="zigbee",
                ))
            elif feature == "enum":
                caps.append(Capability(
                    name=f"sensor.{name}",
                    access="r",
                    source_ecosystem="zigbee",
                ))

        # 特殊设备类型映射
        if "lock" in friendly_name.lower():
            type_str = "lock"
            caps = [Capability(name="lock.lock", access="rw", source_ecosystem="zigbee"),
                    Capability(name="lock.unlock", access="rw", source_ecosystem="zigbee")]
        elif "curtain" in friendly_name.lower() or "blind" in friendly_name.lower():
            type_str = "curtain"
            caps = [Capability(name="curtain.control", access="rw", source_ecosystem="zigbee")]
        elif "water" in friendly_name.lower() and "leak" in friendly_name.lower():
            type_str = "sensor_water_leak"
            caps = [Capability(name="sensor.water_leak", access="r", source_ecosystem="zigbee")]

        return EcosystemDevice(
            ecosystem="zigbee",
            ecosystem_id=ieee,
            name=friendly_name,
            type=type_str,
            online=info.get("state", "offline") == "online",
            capabilities=caps,
            room=info.get("room", ""),
            model=f"{vendor} {model}".strip(),
            raw_state=info.get("state", {}),
        )

    def _discover_deconz(self) -> list[EcosystemDevice]:
        try:
            import requests
            r = requests.get(f"{self.bridge_url}/api", timeout=10)
            return []  # 简化：需 API key
        except Exception:
            return []

    # ============================================================
    # 控制
    # ============================================================

    def execute_action(self, device_id: str, action: str, params=None) -> dict:
        if self.bridge_type == "zigbee2mqtt":
            return self._execute_z2m(device_id, action, params or {})
        return {"success": False, "message": f"{self.bridge_type} 执行未实现"}

    def _execute_z2m(self, ieee: str, action: str, params: dict) -> dict:
        """Z2M 控制：POST /api/devices/{ieee}/command"""
        try:
            import requests
            # 统一 capability → Z2M state 名
            z2m_state = self._action_to_z2m(action)
            if not z2m_state:
                return {"success": False, "message": f"未支持的动作: {action}"}

            payload = {"state": z2m_state}
            payload.update(params)

            r = requests.post(
                f"{self.bridge_url}/api/devices/{ieee}/command",
                json=payload, timeout=10,
            )
            if r.status_code == 200:
                return {"success": True, "state": payload, "message": "OK"}
            return {"success": False, "message": f"Z2M 失败: {r.text}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def _action_to_z2m(self, action: str) -> str | None:
        MAP = {
            "light.toggle": "state",
            "light.brightness": "brightness",
            "light.color": "color",
            "lock.lock": "lock",
            "lock.unlock": "unlock",
            "curtain.control": "position",
        }
        return MAP.get(action)

    def get_state(self, device_id: str) -> dict:
        if self.bridge_type != "zigbee2mqtt":
            return {}
        try:
            import requests
            r = requests.get(f"{self.bridge_url}/api/devices/{device_id}", timeout=5)
            return r.json() if r.status_code == 200 else {}
        except Exception:
            return {}

    def _do_health_check(self) -> bool:
        try:
            import requests
            r = requests.get(f"{self.bridge_url}/api/health", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    # ============================================================
    # 配对（v2.1.1 真实，v2.1.0 stub）
    # ============================================================

    def permit_join(self, duration_seconds: int = 60) -> dict:
        """允许新设备加入网络（Zigbee 标准配对）"""
        if self.bridge_type != "zigbee2mqtt":
            return {"success": False, "message": "Not implemented"}
        try:
            import requests
            r = requests.post(
                f"{self.bridge_url}/api/permit_join",
                json={"value": True, "time": duration_seconds},
                timeout=5,
            )
            return {"success": r.status_code == 200, "duration": duration_seconds}
        except Exception as e:
            return {"success": False, "message": str(e)}