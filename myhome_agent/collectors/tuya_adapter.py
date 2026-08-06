"""涂鸦 (Tuya) OpenAPI v2 Adapter（v2.0）

涂鸦 OpenAPI v2:
- OAuth2 client_credentials / token 认证
- 设备控制 + 状态查询 + 设备发现
- 区域：cn / us / eu / w（西）/ in（印度）

用法：
    config = {
        'access_id': 'xxx',
        'access_secret': 'xxx',
        'endpoint': 'https://openapi.tuyaus.com',  # 美区
        'region': 'us',
    }
    adapter = TuyaAdapter(config)
    adapter.connect()
    devices = adapter.discover()
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any

from .ecosystem import Capability, EcosystemAdapter, EcosystemDevice

logger = logging.getLogger(__name__)


class TuyaAdapter(EcosystemAdapter):
    """v2.0 涂鸦 OpenAPI v2 接入"""

    def __init__(self, config: dict):
        super().__init__("tuya", config)
        self.access_id = config.get("access_id", "")
        self.access_secret = config.get("access_secret", "")
        self.endpoint = config.get("endpoint", "https://openapi.tuyaus.com")
        self.region = config.get("region", "us")
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    # ============================================================
    # OAuth2
    # ============================================================

    def connect(self) -> bool:
        if not self.access_id or not self.access_secret:
            logger.error("Tuya access_id / access_secret 未配置")
            return False
        try:
            self._refresh_token()
            self._healthy = True
            logger.info(f"Tuya adapter 连接成功 ({self.region})")
            return True
        except Exception as e:
            logger.error(f"Tuya 连接失败: {e}")
            return False

    def disconnect(self) -> None:
        self._access_token = None
        self._token_expires_at = 0
        self._healthy = False

    def _refresh_token(self):
        """OAuth2 client_credentials"""
        import requests

        ts = str(int(time.time() * 1000))
        nonce = ""
        method = "GET"
        path = "/v1.0/token?grant_type=1"
        body = ""

        # Sign = HMAC-SHA256(access_secret, method + '\n' + sha256(body) + '\n' + path + '\n' + ts)
        body_hash = hashlib.sha256(body.encode()).hexdigest()
        string_to_sign = f"{method}\n{body_hash}\n{path}\n{ts}"
        sign = hmac.new(
            self.access_secret.encode(),
            string_to_sign.encode(),
            hashlib.sha256,
        ).hexdigest().upper()

        headers = {
            "client_id": self.access_id,
            "sign": sign,
            "t": ts,
            "sign_method": "HMAC-SHA256",
        }

        resp = requests.get(f"{self.endpoint}{path}", headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("success") is not True:
            raise RuntimeError(f"Tuya auth 失败: {data}")

        result = data["result"]
        self._access_token = result["access_token"]
        self._token_expires_at = time.time() + result.get("expire_time", 7200) - 60
        logger.info("Tuya access_token 已刷新")

    def _ensure_token(self):
        if not self._access_token or time.time() >= self._token_expires_at:
            self._refresh_token()

    # ============================================================
    # API 调用
    # ============================================================

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        import requests

        self._ensure_token()
        ts = str(int(time.time() * 1000))
        body_str = json.dumps(body or {}, separators=(",", ":")) if body else ""

        body_hash = hashlib.sha256(body_str.encode()).hexdigest()
        string_to_sign = f"{method}\n{body_hash}\n{path}\n{ts}"
        sign = hmac.new(
            self.access_secret.encode(),
            string_to_sign.encode(),
            hashlib.sha256,
        ).hexdigest().upper()

        headers = {
            "client_id": self.access_id,
            "access_token": self._access_token,
            "sign": sign,
            "t": ts,
            "sign_method": "HMAC-SHA256",
            "Content-Type": "application/json",
        }

        resp = requests.request(
            method, f"{self.endpoint}{path}",
            headers=headers, data=body_str, timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("success") is not True:
            raise RuntimeError(f"Tuya API 失败: {path} {data.get('msg')}")
        return data.get("result", {})

    # ============================================================
    # 设备发现
    # ============================================================

    def discover(self) -> list[EcosystemDevice]:
        try:
            data = self._request("GET", "/v1.0/iot-03/devices")
        except Exception as e:
            logger.error(f"Tuya discover 失败: {e}")
            return []

        devices = []
        for item in data.get("list", []):
            caps = [
                Capability(
                    name=self.normalize_capability(s) or s,
                    access="rw",
                    source_ecosystem="tuya",
                    source_device_id=item.get("id", ""),
                )
                for s in item.get("status", [])
            ]
            dev = EcosystemDevice(
                ecosystem="tuya",
                ecosystem_id=item.get("id", ""),
                name=item.get("name", "Unknown"),
                type=self._map_type(item.get("category", "")),
                online=item.get("online", False),
                capabilities=caps,
                room=item.get("room_name", ""),
                model=item.get("product_name", ""),
                raw_state=item.get("status", {}),
            )
            devices.append(dev)
            self.register_device(dev)

        return devices

    def _map_type(self, category: str) -> str:
        """涂鸦 category → 统一 type"""
        MAP = {
            "dj": "light",
            "kt": "ac",
            "sd": "sensor_motion",
            "ms": "lock",
            "sp": "plug",
            "wn": "curtain",
        }
        return MAP.get(category, "unknown")

    # ============================================================
    # 能力查询
    # ============================================================

    def get_capability(self, device_id: str) -> list[Capability]:
        try:
            data = self._request("GET", f"/v1.0/iot-03/devices/{device_id}/status")
            return [
                Capability(
                    name=self.normalize_capability(s["code"]) or s["code"],
                    access="rw",
                    source_ecosystem="tuya",
                    source_device_id=device_id,
                    params=s.get("custom_name", ""),
                )
                for s in data
            ]
        except Exception:
            return []

    # ============================================================
    # 控制
    # ============================================================

    def execute_action(self, device_id: str, action: str, params: dict | None = None) -> dict:
        try:
            commands = [{"code": self._reverse_normalize(action), "value": params or True}]
            data = self._request(
                "POST",
                f"/v1.0/iot-03/devices/{device_id}/commands",
                body={"commands": commands},
            )
            return {"success": True, "state": data, "message": "OK"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def _reverse_normalize(self, unified: str) -> str:
        """统一 capability → 涂鸦 status code"""
        MAP = {
            "light.toggle": "switch_1",
            "light.brightness": "bright_value",
            "light.color_temp": "temp_value",
            "light.color": "colour_data",
        }
        return MAP.get(unified, unified)

    def get_state(self, device_id: str) -> dict:
        try:
            return self._request("GET", f"/v1.0/iot-03/devices/{device_id}/status")
        except Exception:
            return {}

    def _do_health_check(self) -> bool:
        """Ping Tuya API"""
        try:
            self._ensure_token()
            return bool(self._access_token)
        except Exception:
            return False


# json import 在 _request 内
import json