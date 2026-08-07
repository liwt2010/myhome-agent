"""Philips Hue Bridge API v2 Adapter（v2.0）

Hue Bridge v2 API:
- HTTPS + 客户端配对（link button）
- 流式事件（EventSource / SSE）
- Entertainment API（Hue HDMI）

用法：
    config = {
        'bridge_ip': '192.168.1.50',
        'username': 'myhome-agent',  # 配对生成的 token
        'client_key': 'xxx',         # v2 流式事件
    }
    adapter = HueAdapter(config)
"""
from __future__ import annotations

import logging
import time
from typing import Any

from .ecosystem import Capability, EcosystemAdapter, EcosystemDevice

logger = logging.getLogger(__name__)


class HueAdapter(EcosystemAdapter):
    """v2.0 Philips Hue Bridge API v2"""

    def __init__(self, config: dict):
        super().__init__("hue", config)
        self.bridge_ip = config.get("bridge_ip", "")
        self.username = config.get("username", "")
        self.client_key = config.get("client_key", "")
        self.verify_tls = bool(config.get("verify_tls", True))
        self.ca_cert = config.get("ca_cert", "")
        self.base_url = f"https://{self.bridge_ip}/clip/v2"

    # ============================================================
    # 连接 + 配对
    # ============================================================

    def connect(self) -> bool:
        if not self.bridge_ip:
            logger.error("Hue bridge_ip 未配置")
            return False
        try:
            import requests
            r = requests.get(f"{self.base_url}/resource", timeout=5)
            r.raise_for_status()
            self._healthy = True
            logger.info(f"Hue Bridge 连接成功 ({self.bridge_ip})")
            return True
        except Exception as e:
            logger.error(f"Hue 连接失败: {e}")
            return False

    def disconnect(self) -> None:
        self._healthy = False

    @staticmethod
    def pair(bridge_ip: str, devicetype: str = "myhome-agent#nas") -> str:
        """v2.0 一次性配对：按 Bridge 按钮后调用

        Returns:
            username token
        """
        import requests
        r = requests.post(
            f"https://{bridge_ip}/api",
            json={"devicetype": devicetype},
            timeout=10,
        )
        data = r.json()[0]
        if "success" in data:
            return data["success"]["username"]
        raise RuntimeError(f"Hue 配对失败: {data}")

    # ============================================================
    # API 调用
    # ============================================================

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        import requests
        headers = {"hue-application-key": self.username}
        r = requests.request(
            method, f"{self.base_url}{path}",
            headers=headers, json=body, timeout=10,
            verify=self.ca_cert or self.verify_tls,
        )
        r.raise_for_status()
        return r.json() if r.text else {}

    # ============================================================
    # 设备发现
    # ============================================================

    def discover(self) -> list[EcosystemDevice]:
        try:
            data = self._request("GET", "/resource/device")
        except Exception as e:
            logger.error(f"Hue discover 失败: {e}")
            return []

        devices = []
        for item in data:
            if "light" not in item:
                continue
            caps = []
            for ctrl in item["light"][0].get("capabilities", []):
                uname = self.normalize_capability(ctrl) or ctrl
                caps.append(Capability(name=uname, access="rw", source_ecosystem="hue"))

            dev = EcosystemDevice(
                ecosystem="hue",
                ecosystem_id=item["id"],
                name=item["metadata"]["name"],
                type="light",
                online=item["services"][0]["rt"].count("_connected") > 0,
                capabilities=caps,
                room=item["metadata"].get("room", ""),
                model=item["product_data"].get("model_id", ""),
                raw_state={c: item["light"][0].get(c, {}).get("value") for c in ["on", "dimming", "color_temperature", "color"]},
            )
            devices.append(dev)
            self.register_device(dev)
        return devices

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

    def execute_action(self, device_id: str, action: str, params: dict | None = None) -> dict:
        try:
            body = self._build_command(action, params or {})
            self._request(
                "PUT",
                f"/resource/light/{device_id}",
                body=body,
            )
            return {"success": True, "state": body, "message": "OK"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def _build_command(self, action: str, params: dict) -> dict:
        """统一 capability → Hue v2 body"""
        if action == "light.toggle":
            on = params.get("on", True)
            return {"on": {"on": on}}
        if action == "light.brightness":
            bri = params.get("brightness", 100)
            return {"dimming": {"brightness": bri}}
        if action == "light.color_temp":
            ct = params.get("color_temp", 300)
            return {"color_temperature": {"mirek": ct}}
        if action == "light.color_hue":
            hue = params.get("hue", 0)
            sat = params.get("saturation", 100)
            return {"color": {"xy": {"x": 0.5, "y": 0.5}}}  # 简化
        return {}

    def get_state(self, device_id: str) -> dict:
        try:
            data = self._request("GET", f"/resource/light/{device_id}")
            if data and "light" in data:
                return data["light"][0]
        except Exception:
            pass
        return {}

    def subscribe_events(self, callback) -> bool:
        """v2.0 简化为轮询（v2.1 SSE）"""
        # 真实 Hue v2 SSE：https://{bridge_ip}/eventstream/clip/v2
        # 需 client_key，v2.0 stub
        logger.warning("Hue subscribe_events: v2.0 简化为轮询")
        return False

    def _do_health_check(self) -> bool:
        try:
            import requests
            r = requests.get(
                f"https://{self.bridge_ip}/clip/v2/resource", timeout=3,
                verify=self.ca_cert or self.verify_tls,
            )
            return r.status_code == 200
        except Exception:
            return False
