"""OpenThread 真实集成（v2.1.1）

v2.1.1 路线（无 PyPI 库）：
1. **ot-ctl subprocess**（推荐 / 生产）
   - OpenThread 官方 CLI 工具
   - 装：https://github.com/openthread/openthread (build ot-cli-ftd)
2. **REST API 桥接**（v2.1.0 fallback）
   - OTBR HTTP API（已在 thread_adapter.py 实现）
3. **完全 stub**（v2.1.0 默认）

依赖：
    # ot-cli-ftd 需从源码编译：
    #   git clone https://github.com/openthread/openthread
    #   cd openthread && ./script/bootstrap
    #   ./script/build platform/raspbian
"""
from __future__ import annotations

import json
import logging
import subprocess
import time
from typing import Any

from .ecosystem import Capability, EcosystemAdapter, EcosystemDevice

logger = logging.getLogger(__name__)


# Thread channel 11-26
THREAD_CHANNELS = list(range(11, 27))


class OtCtlBackend:
    """v2.1.1 通过 ot-ctl 子进程控制真实 OpenThread Border Router"""

    def __init__(self, ot_ctl_path: str = "ot-ctl"):
        self.ot_ctl = ot_ctl_path
        self._verify()

    def _verify(self) -> None:
        try:
            result = subprocess.run(
                [self.ot_ctl, "version"], capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                logger.info(f"ot-ctl 可用: {result.stdout.strip()}")
            else:
                logger.warning(f"ot-ctl 异常: {result.stderr.strip()[:200]}")
        except FileNotFoundError:
            logger.warning(
                f"ot-ctl 未找到（{self.ot_ctl}）。"
                "v2.1.1 需编译 openthread 源码"
            )
        except Exception as e:
            logger.error(f"ot-ctl 验证失败: {e}")

    def _run(self, *args, timeout: int = 10) -> dict:
        try:
            result = subprocess.run(
                [self.ot_ctl, *args],
                input="\n", capture_output=True, text=True, timeout=timeout,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            }
        except FileNotFoundError:
            return {"success": False, "error": "ot-ctl not installed"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "ot-ctl timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================
    # Network
    # ============================================================

    def get_state(self) -> dict:
        """Thread 节点状态"""
        return self._run("state")

    def get_role(self) -> str:
        """leader / router / child / disabled"""
        result = self._run("role")
        return result.get("stdout", "").split()[-1] if result.get("success") else "unknown"

    def get_dataset_active(self) -> dict:
        """active dataset 完整内容"""
        result = self._run("dataset", "active", "-x")
        if not result.get("success"):
            return {}
        # ot-ctl dataset active -x 返回 hex / TLV
        return {"raw": result.get("stdout", "")}

    def get_dataset_active_b64(self) -> str:
        result = self._run("dataset", "active", "-")
        return result.get("stdout", "").strip() if result.get("success") else ""

    def set_dataset_active_b64(self, dataset_b64: str) -> bool:
        result = self._run("dataset", "set", "active", dataset_b64)
        if not result.get("success"):
            return False
        result = self._run("dataset", "commit", "active")
        return result.get("success", False)

    def set_channel(self, channel: int) -> bool:
        if channel not in THREAD_CHANNELS:
            logger.error(f"invalid channel: {channel}")
            return False
        return self._run("channel", str(channel)).get("success", False)

    def set_network_key(self, key_hex: str) -> bool:
        return self._run("networkkey", key_hex).get("success", False)

    def set_panid(self, panid_hex: str) -> bool:
        return self._run("panid", panid_hex).get("success", False)

    def set_network_name(self, name: str) -> bool:
        return self._run("networkname", name).get("success", False)

    # ============================================================
    # Nodes (mesh members)
    # ============================================================

    def list_children(self) -> list[dict]:
        """子节点（End Devices + Sleepy End Devices）"""
        result = self._run("child", "list")
        if not result.get("success"):
            return []
        # 解析 ot-ctl 输出（按行）
        children = []
        for line in result.get("stdout", "").split("\n"):
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 4:
                children.append({
                    "child_id": parts[0],
                    "rloc16": parts[1] if len(parts) > 1 else "",
                    "ext_addr": parts[2] if len(parts) > 2 else "",
                    "age": parts[3] if len(parts) > 3 else "",
                    "lq": parts[4] if len(parts) > 4 else "",
                })
        return children

    def list_routers(self) -> list[dict]:
        result = self._run("router", "list")
        if not result.get("success"):
            return []
        routers = []
        for line in result.get("stdout", "").split("\n"):
            if not line.strip() or "Router" in line or "----" in line:
                continue
            parts = line.split()
            if len(parts) >= 3:
                routers.append({
                    "router_id": parts[0],
                    "rloc16": parts[1] if len(parts) > 1 else "",
                    "next_hop": parts[2] if len(parts) > 2 else "",
                    "path_cost": parts[3] if len(parts) > 3 else "",
                })
        return routers

    def get_neighbors(self) -> list[dict]:
        result = self._run("neighbor", "list")
        return [{"raw": line} for line in result.get("stdout", "").split("\n") if line.strip()]


# ============================================================
# Real Thread Adapter
# ============================================================


class RealThreadAdapter(EcosystemAdapter):
    """v2.1.1 Thread Border Router 真实集成

    三档 backend：
    1. ot-ctl subprocess（生产）
    2. REST API（v2.1.0，via thread_adapter.py）
    3. 完全 stub
    """

    def __init__(self, config: dict):
        super().__init__("thread", config)
        self.backend_type = config.get("backend", "stub")  # 'ot_ctl' | 'rest' | 'stub'
        self.ot_ctl_path = config.get("ot_ctl_path", "ot-ctl")
        self.network_name = config.get("network_name", "myhome-thread")
        self.channel = config.get("channel", 20)
        self.backend = None

    def connect(self) -> bool:
        if self.backend_type == "ot_ctl":
            self.backend = OtCtlBackend(self.ot_ctl_path)
            self._healthy = True
            logger.info("Thread backend: ot-ctl")
            return True
        elif self.backend_type == "rest":
            from .thread_adapter import ThreadAdapter
            self.backend = ThreadAdapter(self.config)
            ok = self.backend.connect()
            self._healthy = ok
            return ok
        else:
            self._healthy = True
            logger.warning("Thread backend: stub（v2.1.1 真实集成需编译 OpenThread）")
            return True

    def disconnect(self) -> None:
        self._healthy = False

    def get_dataset(self) -> dict:
        if not self.backend or self.backend_type != "ot_ctl":
            return {}
        return self.backend.get_dataset_active()

    def get_dataset_active_b64(self) -> str:
        if not self.backend or self.backend_type != "ot_ctl":
            return ""
        return self.backend.get_dataset_active_b64()

    def set_dataset_active_b64(self, dataset_b64: str) -> bool:
        if not self.backend or self.backend_type != "ot_ctl":
            return False
        return self.backend.set_dataset_active_b64(dataset_b64)

    def discover(self) -> list[EcosystemDevice]:
        if not self.backend or self.backend_type != "ot_ctl":
            return []
        devices = []

        # Children
        for child in self.backend.list_children():
            devices.append(EcosystemDevice(
                ecosystem="thread",
                ecosystem_id=child.get("ext_addr", child.get("child_id", "")),
                name=f"Thread Child {child.get('child_id', '')}",
                type="end_device",
                online=True,
                capabilities=[
                    Capability(name="mesh.routing", access="rw", source_ecosystem="thread")
                ],
                room="",
                model="Thread v1.3",
                raw_state=child,
            ))

        # Routers
        for router in self.backend.list_routers():
            devices.append(EcosystemDevice(
                ecosystem="thread",
                ecosystem_id=router.get("router_id", ""),
                name=f"Thread Router {router.get('router_id', '')}",
                type="router_node",
                online=True,
                capabilities=[
                    Capability(name="mesh.routing", access="rw", source_ecosystem="thread")
                ],
                room="",
                model="Thread v1.3",
                raw_state=router,
            ))

        return devices

    def get_capability(self, device_id: str) -> list[Capability]:
        return [Capability(name="mesh.routing", access="rw", source_ecosystem="thread")]

    def execute_action(self, device_id: str, action: str, params=None) -> dict:
        if not self.backend or self.backend_type != "ot_ctl":
            return {"success": False, "message": "ot-ctl backend required"}
        params = params or {}
        if action == "mesh.set_channel":
            return self.backend.set_channel(params.get("channel", 20))
        if action == "mesh.commit_dataset":
            return self.backend.set_dataset_active_b64(params.get("dataset_b64", ""))
        return {"success": False, "message": f"未支持: {action}"}

    def get_state(self, device_id: str) -> dict:
        if not self.backend or self.backend_type != "ot_ctl":
            return {}
        return self.backend.get_state()

    def _do_health_check(self) -> bool:
        if self.backend_type == "stub":
            return self._healthy
        return self._healthy and self.backend is not None
