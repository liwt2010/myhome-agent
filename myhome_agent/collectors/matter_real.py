"""Matter Controller - 真实集成（统一 chip-tool 后端）

后端策略：
1. chip-tool（生产）：统一委托 `chip_tool_wrapper.ChipToolAdapter`
2. mDNS（开发）：zeroconf 探测（仅发现，不做协议）
3. stub（默认）：明确返回不可用
"""
from __future__ import annotations

import logging
import time
from typing import Any

from .chip_tool_wrapper import ChipToolAdapter, is_chip_tool_available, parse_node_ids
from .ecosystem import Capability, EcosystemAdapter, EcosystemDevice
from .matter_adapter import MATTER_DEVICE_TYPES, MATTER_TO_UNIFIED_TYPE

logger = logging.getLogger(__name__)


class MdnsBackend:
    """zeroconf mDNS 探测 Matter 设备（_matter._tcp.local.）"""

    def __init__(self):
        self._zeroconf = None
        self._browsers: dict[str, Any] = {}

    def connect(self) -> bool:
        try:
            from zeroconf import ServiceBrowser, Zeroconf

            self._zeroconf = Zeroconf()
            self._browsers["_matter._tcp.local."] = ServiceBrowser(
                self._zeroconf, "_matter._tcp.local.",
                handlers=[self._on_service_state_change],
            )
            logger.info("mDNS 浏览器启动 (_matter._tcp.local.)")
            return True
        except ImportError:
            logger.warning("zeroconf 未装")
            return False
        except Exception as e:
            logger.error(f"mDNS 启动失败: {e}")
            return False

    def _on_service_state_change(self, zeroconf, service_type, name, state_change):
        if state_change.name in ("ServiceAdded", "ServiceUpdated"):
            info = zeroconf.get_service_info(service_type, name)
            if info:
                logger.info(f"发现 Matter 设备: {name} @ {info.parsed_addresses()}")

    def discover(self, timeout_seconds: int = 5) -> list[dict]:
        time.sleep(timeout_seconds)
        services = []
        if not self._zeroconf:
            return services
        for browser in self._browsers.values():
            for svc in browser.services:
                info = self._zeroconf.get_service_info(svc[0], svc[0])
                if info:
                    services.append({
                        "name": info.name,
                        "addresses": [str(a) for a in info.parsed_addresses()],
                        "port": info.port,
                        "properties": dict(info.properties) if info.properties else {},
                    })
        return services

    def close(self) -> None:
        if self._zeroconf:
            self._zeroconf.close()


class RealMatterAdapter(EcosystemAdapter):
    """Matter controller 真实集成（chip-tool 统一后端）"""

    def __init__(self, config: dict):
        super().__init__("matter", config)
        self.backend_type = config.get("backend", "stub")  # 'chip_tool' | 'mdns' | 'stub'
        self.chip_tool_path = config.get("chip_tool_path", "chip-tool")
        self.node_id = config.get("node_id", 1)
        self.fabric_id = config.get("fabric_id", "")
        self.commissioning_passcode = config.get("passcode", 20202021)
        self.commissioning_discriminator = config.get("discriminator", 3840)
        self.backend = None
        self.mdns = None

    def connect(self) -> bool:
        if self.backend_type == "chip_tool":
            if not is_chip_tool_available(self.chip_tool_path):
                self._healthy = False
                logger.warning("chip-tool 不可用（%s）", self.chip_tool_path)
                return False
            self.backend = ChipToolAdapter(
                chip_tool_path=self.chip_tool_path,
                fabric_id=int(self.fabric_id) if str(self.fabric_id).isdigit() else 1,
                node_id=self.node_id,
            )
            self._healthy = True
            logger.info("Matter backend: chip-tool")
            return True
        if self.backend_type == "mdns":
            self.mdns = MdnsBackend()
            ok = self.mdns.connect()
            self._healthy = ok
            logger.info(f"Matter backend: mDNS (healthy={ok})")
            return ok
        logger.warning("Matter backend: stub（无可用后端，connect 失败）")
        self._healthy = False
        return False

    def disconnect(self) -> None:
        self._healthy = False
        if self.mdns:
            self.mdns.close()

    def commission(
        self,
        setup_passcode: int,
        discriminator: int = 3840,
        thread_dataset_hex: str | None = None,
    ) -> bool:
        if self.backend_type == "chip_tool" and self.backend:
            result = self.backend.commission(
                setup_passcode,
                discriminator,
                node_id=self.node_id,
                thread_dataset_hex=thread_dataset_hex,
            )
            return bool(result.success)
        return False

    def discover(self) -> list[EcosystemDevice]:
        if self.backend_type == "mdns" and self.mdns:
            services = self.mdns.discover(timeout_seconds=5)
            devices = [self._mdns_to_device(s) for s in services]
            for dev in devices:
                self.register_device(dev)
            return devices
        if self.backend_type == "chip_tool" and self.backend:
            result = self.backend.list_nodes()
            if not result.success:
                logger.warning("Matter chip-tool list-nodes 失败: %s", result.stderr[:200])
                return []
            devices = []
            for node_id in parse_node_ids(result.stdout):
                dev = self._node_to_device(node_id)
                devices.append(dev)
                self.register_device(dev)
            return devices
        return []

    @staticmethod
    def _node_to_device(node_id: str) -> EcosystemDevice:
        return EcosystemDevice(
            ecosystem="matter",
            ecosystem_id=node_id,
            name=f"Matter Node {node_id}",
            type="unknown",
            online=True,
            capabilities=[],
            room="",
            model="",
            raw_state={},
        )

    def _mdns_to_device(self, service: dict) -> EcosystemDevice:
        name = service.get("name", "Unknown")
        addresses = service.get("addresses", [])
        port = service.get("port", 5540)
        props = service.get("properties", {})

        def _prop(key: str, default: str = "") -> str:
            value = props.get(key, default)
            if isinstance(value, (bytes, bytearray)):
                return value.decode("utf-8", "replace")
            return str(value)

        dt_raw = _prop("d", "0x0100")
        try:
            dt_id = int(dt_raw, 16)
        except (TypeError, ValueError):
            dt_id = 0x0100
        dt_name = MATTER_DEVICE_TYPES.get(dt_id, "Unknown")
        type_str, cap_names = MATTER_TO_UNIFIED_TYPE.get(dt_name, ("unknown", []))
        caps = [
            Capability(name=cn, access="rw", source_ecosystem="matter")
            for cn in cap_names
        ]
        return EcosystemDevice(
            ecosystem="matter",
            ecosystem_id=_prop("id", addresses[0] if addresses else "unknown"),
            name=name,
            type=type_str,
            online=bool(addresses),
            capabilities=caps,
            room=_prop("room", ""),
            model=_prop("md", ""),
            raw_state={"addresses": addresses, "port": port},
        )

    def get_capability(self, device_id: str) -> list[Capability]:
        for dev in self._devices.values():
            if dev.ecosystem_id == device_id:
                return dev.capabilities
        return []

    def execute_action(self, device_id: str, action: str, params=None) -> dict:
        if not self.backend or self.backend_type != "chip_tool":
            return {"success": False, "state": None, "message": "chip-tool backend required"}
        try:
            node_id, endpoint = self._parse_device_id(device_id)
        except Exception as e:
            return {"success": False, "state": None, "message": f"device_id 格式错: {e}"}

        params = params or {}
        if action == "light.toggle":
            raw = self.backend.onoff(node_id, endpoint, params.get("on", True))
        elif action == "light.brightness":
            raw = self.backend.level(node_id, endpoint, params.get("brightness", 100))
        elif action == "light.color_temp":
            raw = self.backend.color_temperature(node_id, endpoint, params.get("color_temp", 300))
        elif action == "lock.lock":
            raw = self.backend.lock_door(node_id, endpoint)
        elif action == "lock.unlock":
            raw = self.backend.unlock_door(node_id, endpoint)
        elif action == "ac.target_temp":
            raw = self.backend.thermostat_setpoint(node_id, endpoint, params.get("target_temp", 22))
        else:
            return {"success": False, "state": None, "message": f"未支持: {action}"}
        return self._wrap_result(raw)

    @staticmethod
    def _parse_device_id(device_id: str) -> tuple[int, int]:
        if "/" in device_id:
            node, ep = device_id.split("/", 1)
            return int(node), int(ep)
        return int(device_id), 1

    @staticmethod
    def _wrap_result(raw) -> dict:
        if hasattr(raw, "success"):
            ok = bool(raw.success)
            stdout = getattr(raw, "stdout", "")
            stderr = getattr(raw, "stderr", "")
            message = "OK" if ok else "chip-tool 命令失败"
        else:
            ok = bool(raw.get("success", False))
            stdout = raw.get("stdout", "")
            stderr = raw.get("stderr", "")
            message = "OK" if ok else raw.get("error", "chip-tool 命令失败")
        return {
            "success": ok,
            "state": {"stdout": stdout, "stderr": stderr},
            "message": message,
        }

    def get_state(self, device_id: str) -> dict:
        if not self.backend or self.backend_type != "chip_tool":
            return {}
        try:
            node_id, endpoint = self._parse_device_id(device_id)
        except Exception:
            return {}

        reads = [
            ("OnOff", "OnOff"),
            ("Level", "CurrentLevel"),
            ("DoorLock", "LockState"),
            ("Thermostat", "OccupiedHeatingSetpoint"),
            ("TemperatureMeasurement", "MeasuredValue"),
        ]
        state = {}
        for cluster, attribute in reads:
            raw = self.backend.read_attribute(node_id, endpoint, cluster, attribute)
            wrapped = self._wrap_result(raw)
            if wrapped["success"]:
                state[f"{cluster}.{attribute}"] = wrapped["state"]["stdout"].strip()[:200]
        return state

    def _do_health_check(self) -> bool:
        if self.backend_type == "chip_tool":
            return self._healthy and self.backend is not None and is_chip_tool_available(self.chip_tool_path)
        if self.backend_type == "mdns":
            return self._healthy and self.mdns is not None
        return False
