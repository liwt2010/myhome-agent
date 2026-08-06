"""HomeKit Bridge Adapter（v2.0）

将 myhome-agent 设备作为 HomeKit accessory 暴露给 iOS Home app。
依赖 HAP-python（纯 Python HomeKit Accessory Protocol 实现）。

用法：
    config = {
        'persist_file': '~/.myhome/homekit.db',  # pairing 数据
        'port': 51823,
    }
    bridge = HomeKitAdapter(config)
    bridge.start()  # 启动 mDNS + HAP server
"""
from __future__ import annotations

import logging
import os
from typing import Any

from .ecosystem import Capability, EcosystemAdapter, EcosystemDevice

logger = logging.getLogger(__name__)


class HomeKitAdapter(EcosystemAdapter):
    """v2.0 HomeKit bridge（用 HAP-python）"""

    def __init__(self, config: dict):
        super().__init__("homekit", config)
        self.persist_file = config.get("persist_file", "~/.myhome/homekit.db")
        self.port = config.get("port", 51823)
        self.bridge = None

    # ============================================================
    # Bridge 生命周期
    # ============================================================

    def connect(self) -> bool:
        try:
            from pyhap.accessory import Bridge
            from pyhap.accessory_driver import AccessoryDriver
            from pyhap.const import STANDALONE
        except ImportError:
            logger.error("HAP-python 未装：`pip install HAP-python[QRCode]`（清华镜像）")
            return False

        try:
            persist_path = os.path.expanduser(self.persist_file)
            os.makedirs(os.path.dirname(persist_path), exist_ok=True)

            self.bridge = Bridge()
            driver = AccessoryDriver(
                self.bridge,
                persist_file=persist_path,
                port=self.port,
                address=None,  # 监听所有接口
                advertised_address=None,
            )
            self._driver = driver
            self._healthy = True
            logger.info(f"HomeKit Bridge 启动（端口 {self.port}）")
            return True
        except Exception as e:
            logger.error(f"HomeKit Bridge 启动失败: {e}")
            return False

    def disconnect(self) -> None:
        if self._driver:
            try:
                self._driver.stop()
            except Exception:
                pass

    def start(self) -> None:
        """v2.0 实际启动（run_forever 在子线程）"""
        if self.bridge:
            try:
                self._driver.start()
            except Exception as e:
                logger.error(f"HomeKit start 失败: {e}")

    # ============================================================
    # 添加 accessory（米家 / Tuya / Hue 设备作为 HomeKit 暴露）
    # ============================================================

    def add_light_accessory(self, device: EcosystemDevice) -> bool:
        """把 light 设备添加为 HomeKit Lightbulb accessory"""
        try:
            from pyhap.accessory import Accessory
            from pyhap.characteristic import Characteristic
            from pyhap.const import (
                CATEGORY_SWITCH,
                CHAR_ON,
                CHAR_BRIGHTNESS,
                CHAR_HUE,
                CHAR_SATURATION,
            )
            from pyhap.services import Service

            acc = Accessory(self._driver, device.name)
            acc.category = CATEGORY_SWITCH

            service = acc.add_service(Service.Lightbulb)
            on_char = service.configure_char(CHAR_ON, value=False)

            # 回调：当 iOS 改灯状态
            def on_change(char):
                if char == on_char:
                    new_state = char.value
                    # 回调到原 ecosystem
                    self.execute_action(
                        device.ecosystem_id, "light.toggle",
                        {"on": new_state},
                    )

            on_char.setter_callback = on_change

            self.bridge.add_accessory(acc)
            self.register_device(device)
            return True
        except Exception as e:
            logger.error(f"HomeKit add_light_accessory 失败: {e}")
            return False

    def add_thermostat_accessory(self, device: EcosystemDevice) -> bool:
        """v2.0 简化：只暴露恒温器读数"""
        try:
            from pyhap.accessory import Accessory
            from pyhap.characteristic import Characteristic
            from pyhap.const import CATEGORY_THERMOSTAT, CHAR_CURRENT_TEMPERATURE
            from pyhap.services import Service

            acc = Accessory(self._driver, device.name)
            acc.category = CATEGORY_THERMOSTAT
            service = acc.add_service(Service.Thermostat)
            service.configure_char(CHAR_CURRENT_TEMPERATURE, value=20.0)

            self.bridge.add_accessory(acc)
            return True
        except Exception as e:
            logger.error(f"HomeKit add_thermostat_accessory 失败: {e}")
            return False

    # ============================================================
    # EcosystemAdapter 接口
    # ============================================================

    def discover(self) -> list[EcosystemDevice]:
        return []  # HomeKit 是被动桥接，无主动发现

    def get_capability(self, device_id: str) -> list[Capability]:
        return []

    def execute_action(self, device_id: str, action: str, params=None) -> dict:
        return {"success": False, "message": "HomeKit bridge 不支持直接调用"}

    def get_state(self, device_id: str) -> dict:
        return {}

    def _do_health_check(self) -> bool:
        return self._healthy and self.bridge is not None