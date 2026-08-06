"""局域网 miio 采集与控制。

依赖设备的 IP + token（由云端同步写入设备表）。
读取：轮询设备状态写入 readings/events。
控制：优先本地下发指令，失败抛出异常由上层决定是否走云端。
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# 常见传感器指标名归一化
METRIC_ALIASES = {
    "temp": "temperature", "temperature": "temperature",
    "humidity": "humidity", "relative_humidity": "humidity",
    "illumination": "illumination", "lux": "illumination",
    "power": "power", "power_consume_rate": "power_load",
    "aqi": "aqi", "pm25": "pm25", "co2": "co2",
    "battery": "battery", "bright": "brightness",
}


def _normalize(k: str) -> str:
    return METRIC_ALIASES.get(k.lower(), k.lower())


class LocalMiioCollector:
    """对 python-miio 的薄封装，尽量做到与具体设备型号解耦。"""

    def __init__(self):
        self._cache: dict[str, Any] = {}  # device_id -> miio device 实例

    def _device(self, dev: dict):
        import miio
        did = dev["id"]
        if did not in self._cache:
            try:
                # DeviceFactory 会根据 miot/miio 协议自动选择实现
                self._cache[did] = miio.DeviceFactory.create(dev["ip"], dev["token"])
            except Exception:
                self._cache[did] = miio.Device(dev["ip"], dev["token"])
        return self._cache[did]

    def poll(self, dev: dict) -> dict[str, Any]:
        """读取设备当前状态，返回 {metric: value}。设备离线抛异常。"""
        if not dev.get("ip") or not dev.get("token"):
            raise ValueError(f"设备 {dev['name']} 缺少 ip/token，无法本地轮询")
        device = self._device(dev)
        result: dict[str, Any] = {}
        try:
            status = device.status()
            data = getattr(status, "data", None) or {}
            for k, v in data.items():
                if v is not None:
                    result[_normalize(str(k))] = v
        except Exception as e:
            # 部分老设备不支持 status()，退回 info 探活
            logger.debug("status() 失败 (%s)，尝试 info(): %s", dev["name"], e)
            info = device.info()
            result["online"] = 1
            result["fw_version"] = getattr(info, "firmware_version", "")
        return result

    def send_command(self, dev: dict, command: str, params: list | None = None) -> Any:
        """发送原始 miio 指令，如 set_power ['on']。"""
        if not dev.get("ip") or not dev.get("token"):
            raise ValueError(f"设备 {dev['name']} 缺少 ip/token，无法本地控制")
        device = self._device(dev)
        return device.send(command, params or [])

    # 常用高层操作：不同型号指令名不同，做多候选尝试
    POWER_COMMANDS = ["set_power", "set_properties", "toggle"]

    def set_power(self, dev: dict, on: bool) -> Any:
        errors = []
        for cmd in ("set_power",):
            try:
                return self.send_command(dev, cmd, ["on" if on else "off"])
            except Exception as e:
                errors.append(f"{cmd}: {e}")
        raise RuntimeError("本地开关指令失败: " + "; ".join(errors))
