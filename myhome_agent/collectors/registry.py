"""统一设备注册表：串起云端发现、本地轮询与控制策略。"""
from __future__ import annotations

import logging
from typing import Any

from ..memory.store import Store
from .cloud_api import MiCloudCollector
from .local_miio import LocalMiioCollector

logger = logging.getLogger(__name__)

# 离散事件型指标：写入 events 而不是 readings
EVENT_METRICS = {"motion", "door_open", "water_leak", "gas_leak", "smoke", "button"}


class DeviceRegistry:
    def __init__(self, store: Store, cloud: MiCloudCollector | None):
        self.store = store
        self.cloud = cloud
        self.local = LocalMiioCollector()

    def sync_from_cloud(self) -> int:
        """从米家云端同步设备清单（含 token/IP），写入设备表。"""
        if not self.cloud:
            logger.warning("未配置米家账号，跳过云端同步")
            return 0
        devices = self.cloud.fetch_devices()
        for d in devices:
            self.store.upsert_device(d)
        return len(devices)

    def poll_all_local(self) -> dict[str, Any]:
        """轮询所有有 ip+token 的设备，写入时序库。返回 {device_id: status|error}。"""
        results: dict[str, Any] = {}
        for dev in self.store.list_devices():
            if not dev.get("ip") or not dev.get("token"):
                continue
            try:
                status = self.local.poll(dev)
                for metric, value in status.items():
                    if metric in EVENT_METRICS and value in (1, True, "1", "on"):
                        self.store.add_event(kind=metric, device_id=dev["id"])
                    else:
                        self.store.add_reading(dev["id"], metric, value)
                dev["online"] = 1
                self.store.upsert_device(dev)
                results[dev["id"]] = status
            except Exception as e:
                results[dev["id"]] = f"error: {e}"
                logger.debug("轮询失败 %s: %s", dev["name"], e)
        return results

    def control(self, device_id: str, action: str, params: list | None = None) -> Any:
        """控制设备。action 支持 'on'/'off' 或原始 miio 指令名。"""
        dev = self.store.get_device(device_id) or self.store.find_device_by_name(device_id)
        if not dev:
            raise ValueError(f"找不到设备: {device_id}")
        if action in ("on", "off"):
            result = self.local.set_power(dev, action == "on")
        else:
            result = self.local.send_command(dev, action, params)
        self.store.add_event(kind="control", device_id=dev["id"],
                             detail={"action": action, "params": params, "result": str(result)})
        return result
