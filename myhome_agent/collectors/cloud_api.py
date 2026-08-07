"""米家云 collector：优先真实 micloud 实现，依赖缺失时保持空列表 + 告警。"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _map_type(model: str) -> str:
    m = (model or "").lower()
    if "lock" in m:
        return "lock"
    if "camera" in m or "gateway.camera" in m:
        return "camera"
    if "sensor" in m:
        return "sensor_ht"
    if "plug" in m or "switch" in m:
        return "plug"
    if "vacuum" in m or "roborock" in m or "sweep" in m:
        return "vacuum"
    if "light" in m or "lamp" in m:
        return "light"
    return "unknown"


class MiCloudCollector:
    """v0.5 真实云同步（micloud 包）；未安装时降级为空列表。"""

    def __init__(self, username: str = "", password: str = "", region: str = "cn"):
        self.username = username
        self.password = password
        self.region = region
        self._cloud = None

    def login(self) -> bool:
        if self._cloud is not None:
            return True
        try:
            from micloud import MiCloud
        except ImportError:
            logger.warning("未安装 micloud，云同步不可用（pip install micloud）")
            return False
        try:
            try:
                cloud = MiCloud(self.username, self.password)
            except TypeError:
                cloud = MiCloud(self.username, self.password, country=self.region)
            cloud.login()
            self._cloud = cloud
            return True
        except Exception as e:
            logger.error("米家登录失败: %s", e)
            return False

    def get_devices(self) -> list[dict[str, Any]]:
        if not self.login():
            return []
        try:
            homes = self._cloud.get_home_device_list()
        except Exception as e:
            logger.error("获取米家设备列表失败: %s", e)
            return []

        devices: list[dict[str, Any]] = []
        for home in ((homes.get("result") or {}).get("homelist", []) or []):
            for item in (home.get("device_list", []) or home.get("devices", []) or []):
                devices.append({
                    "id": str(item.get("did", "")),
                    "name": item.get("name") or item.get("alias") or str(item.get("did", "")),
                    "model": item.get("model", ""),
                    "type": _map_type(item.get("model", "")),
                    "room": item.get("room_name") or item.get("room", "") or "",
                    "ip": item.get("localip", "") or "",
                    "token": item.get("token", "") or "",
                    "source": "cloud",
                    "online": 1 if item.get("isOnline", False) else 0,
                    "extra": {
                        "home": home.get("name", ""),
                        "device_type": item.get("device_type", ""),
                    },
                })
        logger.info("米家云同步完成：%d 台设备", len(devices))
        return devices

    def fetch_devices(self) -> list[dict[str, Any]]:
        """registry 使用的同步入口。"""
        return self.get_devices()

    def get_token(self, did: str) -> str | None:
        if not self.login():
            return None
        for dev in self.get_devices():
            if dev["id"] == did:
                return dev.get("token")
        return None
