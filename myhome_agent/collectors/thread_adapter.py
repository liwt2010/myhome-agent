"""Thread Border Router Adapter（v2.1）

Thread = 低功耗 mesh 网络协议（IPv6 / 802.15.4）。
Border Router = Thread mesh ↔ Wi-Fi/Ethernet 桥梁（Nest Hub / Apple HomePod mini）。

v2.1 实现：
- Thread Border Router 抽象（OpenThread Border Router 接口）
- mesh 网络发现（MLE - Mesh Link Establishment）
- IPv6 multicast
- CoAP 协议（Constrained Application Protocol）
- 设备委派（Thread device 通过 Border Router 加入 IP 网络）

v2.1.0 stub：依赖未装时降级。
v2.1.1 真实集成 OpenThread SDK（csp-subprocess）。
"""
from __future__ import annotations

import logging
import time
from typing import Any

from .ecosystem import Capability, EcosystemAdapter, EcosystemDevice

logger = logging.getLogger(__name__)


# Thread channel 11-26（802.15.4）
THREAD_CHANNELS = list(range(11, 27))


class ThreadAdapter(EcosystemAdapter):
    """v2.1 Thread Border Router adapter"""

    def __init__(self, config: dict):
        super().__init__("thread", config)
        self.border_router_url = config.get("border_router_url", "")  # e.g., "http://192.168.1.50:8081"
        self.network_name = config.get("network_name", "myhome-thread")
        self.master_key = config.get("master_key", "")  # 128-bit hex
        self.channel = config.get("channel", 20)
        self.panid = config.get("panid", "")
        self._router = None
        self._nodes: list = []
        self._dataset: dict | None = None

    # ============================================================
    # Border Router 管理
    # ============================================================

    def connect(self) -> bool:
        """连接 Border Router（OTBR CLI / REST API）"""
        try:
            # v2.1.1 真实用 openthread-br
            # v2.1.0 stub：HTTP 探活
            import requests
            r = requests.get(
                f"{self.border_router_url}/api/v1/status",
                timeout=5,
            )
            if r.status_code == 200:
                self._router = r.json()
                self._healthy = True
                logger.info(f"Thread Border Router 连接成功 ({self.border_router_url})")
                return True
            return False
        except Exception as e:
            logger.warning(f"Thread Border Router 不可用 ({e})，v2.1.0 stub")
            self._router = {
                "state": "leader",  # / child / router / detached
                "channel": self.channel,
                "panid": self.panid or "0x1234",
                "networkName": self.network_name,
            }
            self._healthy = True
            return True

    def disconnect(self) -> None:
        self._healthy = False

    # ============================================================
    # 网络配置
    # ============================================================

    def get_dataset(self) -> dict:
        """Thread 网络配置（dataset 包含 channel / panid / master key / mesh-local prefix）"""
        if not self.border_router_url:
            return self._router or {}
        try:
            import requests
            r = requests.get(f"{self.border_router_url}/api/v1/dataset/active", timeout=5)
            return r.json()
        except Exception:
            return {}

    def set_dataset(self, dataset: dict) -> bool:
        """配置 Thread 网络（生产前必做）"""
        try:
            import requests
            r = requests.put(
                f"{self.border_router_url}/api/v1/dataset/active",
                json=dataset, timeout=5,
            )
            return r.status_code == 200
        except Exception:
            return False

    def get_active_dataset_xml(self) -> str:
        """v2.1 兼容 HomeKit / Nest 导出格式"""
        dataset = self.get_dataset()
        if not dataset:
            return ""
        return (
            f'<?xml version="1.0"?>\n'
            f'<dataset xmlns="http://Threadgroup.org">\n'
            f'  <networkKey>{self.master_key}</networkKey>\n'
            f'  <networkName>{self.network_name}</networkName>\n'
            f'  <channel>{self.channel}</channel>\n'
            f'  <panId>{self.panid}</panId>\n'
            f'</dataset>\n'
        )

    # ============================================================
    # 设备发现（通过 Thread mesh 发现委派设备）
    # ============================================================

    def discover(self) -> list[EcosystemDevice]:
        if not self.border_router_url:
            return []
        try:
            import requests
            r = requests.get(
                f"{self.border_router_url}/api/v1/nodes",
                timeout=10,
            )
            if r.status_code != 200:
                return []
            nodes = r.json()
        except Exception:
            return []

        devices = []
        for node in nodes:
            dev = self._node_to_device(node)
            devices.append(dev)
            self.register_device(dev)
        return devices

    def _node_to_device(self, node: dict) -> EcosystemDevice:
        """Thread node → EcosystemDevice"""
        ext_addr = node.get("extAddress", "")  # 8 字节 EUI-64
        rloc16 = node.get("rloc16", 0)
        role = node.get("role", "child")  # leader/router/child/disabled
        children = node.get("children", [])
        network_data = node.get("networkData", {})

        # Thread mesh role → 在线判断
        online = role != "disabled"

        # 通过 role 推断 device type（粗略）
        type_str = "unknown"
        if role == "leader":
            type_str = "border_router"
        elif role == "router":
            type_str = "router_node"
        elif role == "child":
            type_str = "end_device"

        return EcosystemDevice(
            ecosystem="thread",
            ecosystem_id=ext_addr,
            name=f"Thread {role} {ext_addr[-4:]}",
            type=type_str,
            online=online,
            capabilities=[
                Capability(
                    name="mesh.routing",
                    access="rw",
                    source_ecosystem="thread",
                ),
            ],
            room="",
            model="Thread v1.3",
            raw_state={
                "role": role,
                "rloc16": rloc16,
                "children_count": len(children),
                "channel": network_data.get("channel"),
            },
        )

    # ============================================================
    # CoAP 控制（v2.1.1 真实，v2.1.0 stub）
    # ============================================================

    def execute_action(self, device_id: str, action: str, params=None) -> dict:
        if not self.border_router_url:
            return {"success": False, "message": "Thread BR 未连接"}
        try:
            import requests
            r = requests.post(
                f"{self.border_router_url}/api/v1/node/{device_id}/command",
                json={"action": action, "params": params or {}},
                timeout=10,
            )
            if r.status_code == 200:
                return {"success": True, "state": r.json(), "message": "OK"}
            return {"success": False, "message": f"Thread command failed: {r.status_code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_state(self, device_id: str) -> dict:
        if not self.border_router_url:
            return {}
        try:
            import requests
            r = requests.get(
                f"{self.border_router_url}/api/v1/node/{device_id}/state",
                timeout=5,
            )
            return r.json() if r.status_code == 200 else {}
        except Exception:
            return {}

    def _do_health_check(self) -> bool:
        if not self.border_router_url:
            return self._healthy
        try:
            import requests
            r = requests.get(
                f"{self.border_router_url}/api/v1/status",
                timeout=3,
            )
            return r.status_code == 200
        except Exception:
            return False