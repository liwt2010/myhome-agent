"""米家云端 collector（v0.5 占位，v0.1-v0.4 不实现）

v0.5 计划接入 miio + micloud。
v0.1-v0.4 用 stub：构造函数 + 占位 sync，控制直接走 LocalMiioCollector。
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class MiCloudCollector:
    """v0.5 占位——v0.1-v0.4 期间只存凭证，不实际调云端"""

    def __init__(self, username: str = "", password: str = "", region: str = "cn"):
        self.username = username
        self.password = password
        self.region = region
        logger.debug("MiCloudCollector 初始化（v0.4 stub）")

    def get_devices(self) -> list[dict[str, Any]]:
        """v0.4 stub：返回空列表"""
        logger.info("MiCloudCollector.get_devices: stub，v0.5 实现")
        return []

    def login(self) -> bool:
        """v0.4 stub：返回 False 表示未登录"""
        if not self.username or not self.password:
            return False
        logger.info("MiCloudCollector.login: stub，v0.5 实现")
        return False

    def get_token(self, did: str) -> str | None:
        """v0.4 stub：返回 None"""
        return None
