"""chip-tool Python 封装（v2.2 真实集成）

依赖：
    chip-tool 需源码编译（不在 PyPI）
    编译：https://github.com/project-chip/connectedhomeip
    预计编译时间：30-60 分钟（依赖机器性能）

Windows 用户：建议 WSL2 或 Docker 跑 chip-tool
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ChipToolResult:
    """chip-tool 命令执行结果"""
    success: bool
    stdout: str
    stderr: str
    returncode: int
    data: dict = field(default_factory=dict)
    elapsed_ms: int = 0


class ChipToolAdapter:
    """v2.2 chip-tool subprocess 封装（v0.1 基础）"""

    def __init__(
        self,
        chip_tool_path: str = "chip-tool",
        fabric_id: int = 1,
        node_id: int = 1,
        default_timeout: int = 30,
    ):
        self.chip_tool = chip_tool_path
        self.fabric_id = fabric_id
        self.node_id = node_id
        self.default_timeout = default_timeout
        self._verify_installation()

    def _verify_installation(self):
        """检查 chip-tool 是否已安装"""
        try:
            result = subprocess.run(
                [self.chip_tool, "--help"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode != 0 and "error" in result.stderr.lower():
                logger.warning(
                    f"chip-tool 未安装或不可用（{self.chip_tool}）。"
                    "v2.2 需编译 connectedhomeip 源码。"
                    "Windows 用户用 WSL2 或 Docker。"
                )
        except FileNotFoundError:
            logger.warning(
                f"chip-tool 不可用：{self.chip_tool}\n"
                "v2.2 真实集成需编译 connectedhomeip。\n"
                "  编译：git clone https://github.com/project-chip/connectedhomeip\n"
                "        cd connectedhomeip && ./scripts/bootstrap.sh\n"
                "        ./scripts/build.sh\n"
                "  路径：export PATH=$PWD/out/<platform>/chip-tool:$PATH"
            )
        except Exception as e:
            logger.error(f"chip-tool 检测失败: {e}")

    def _run(
        self,
        *args,
        timeout: int | None = None,
        parse_json: bool = True,
    ) -> ChipToolResult:
        """执行 chip-tool 命令"""
        cmd = [self.chip_tool, *args]
        timeout = timeout or self.default_timeout
        t0 = time.time()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
            )
            elapsed = int((time.time() - t0) * 1000)
            data = {}
            if parse_json and result.stdout.strip().startswith("{"):
                try:
                    data = json.loads(result.stdout)
                except json.JSONDecodeError:
                    pass
            return ChipToolResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                data=data,
                elapsed_ms=elapsed,
            )
        except FileNotFoundError:
            return ChipToolResult(
                success=False,
                stdout="",
                stderr=f"chip-tool not found: {self.chip_tool}",
                returncode=-1,
            )
        except subprocess.TimeoutExpired:
            return ChipToolResult(
                success=False,
                stdout="",
                stderr=f"timeout after {timeout}s",
                returncode=-2,
            )
        except Exception as e:
            return ChipToolResult(
                success=False,
                stdout="",
                stderr=str(e),
                returncode=-3,
            )

    # ============================================================
    # v2.2 Matter 控制 API
    # ============================================================

    def onoff(
        self, node_id: int, endpoint: int, on: bool,
    ) -> ChipToolResult:
        """OnOff 集群：开/关"""
        cmd = "on" if on else "off"
        return self._run("onoff", cmd, str(node_id), str(endpoint))

    def level(
        self, node_id: int, endpoint: int, level: int,
        transition_time_ms: int = 0,
    ) -> ChipToolResult:
        """Level 集群：亮度/音量 0-254"""
        return self._run(
            "levelcontrol", "move-to-level",
            str(level), str(transition_time_ms), "0", "0",
            str(node_id), str(endpoint),
        )

    def color_temperature(
        self, node_id: int, endpoint: int, mireds: int,
    ) -> ChipToolResult:
        """ColorTemperature 集群：色温（mireds）"""
        return self._run(
            "colorcontrol", "move-to-color-temperature",
            str(mireds), "0", "0", "0",
            str(node_id), str(endpoint),
        )

    def lock_door(self, node_id: int, endpoint: int) -> ChipToolResult:
        """DoorLock 集群：锁门"""
        return self._run("doorlock", "lock-door", str(node_id), str(endpoint))

    def unlock_door(self, node_id: int, endpoint: int) -> ChipToolResult:
        """DoorLock 集群：开门"""
        return self._run("doorlock", "unlock-door", str(node_id), str(endpoint))

    def thermostat_setpoint(
        self,
        node_id: int, endpoint: int,
        target_temp_c: float,
        mode: str = "heat",
    ) -> ChipToolResult:
        """Thermostat 集群：写绝对目标温度（毫度），避免相对调温语义错误"""
        attribute = "occupied-heating-setpoint" if mode == "heat" else "occupied-cooling-setpoint"
        return self._run(
            "thermostat", "write", attribute,
            str(int(round(target_temp_c * 100))),
            str(node_id), str(endpoint),
        )

    def read_attribute(
        self, node_id: int, endpoint: int, cluster: str, attribute: str,
    ) -> ChipToolResult:
        """读 cluster attribute"""
        return self._run(
            self._cluster_to_path(cluster), "read",
            attribute, str(node_id), str(endpoint),
        )

    def _cluster_to_path(self, cluster: str) -> str:
        """cluster 名 → chip-tool 子命令路径"""
        MAP = {
            "OnOff": "onoff",
            "Level": "levelcontrol",
            "ColorControl": "colorcontrol",
            "DoorLock": "doorlock",
            "Thermostat": "thermostat",
            "WindowCovering": "windowcovering",
            "IlluminanceMeasurement": "illuminancemeasurement",
            "TemperatureMeasurement": "temperaturemeasurement",
        }
        return MAP.get(cluster, cluster.lower())

    # ============================================================
    # v2.2 Commissioning
    # ============================================================

    def commission(
        self, setup_passcode: int, discriminator: int = 3840,
        node_id: int | None = None, thread_dataset_hex: str | None = None,
        timeout: int = 120,
    ) -> ChipToolResult:
        """Matter commissioning（BLE + Thread：node [hex:dataset] pin discriminator）"""
        args = [
            "pairing", "ble-thread",
            str(node_id if node_id is not None else self.node_id),
        ]
        if thread_dataset_hex:
            dataset = thread_dataset_hex if thread_dataset_hex.startswith("hex:") else f"hex:{thread_dataset_hex}"
            args.append(dataset)
        args.extend([str(setup_passcode), str(discriminator)])
        return self._run(
            *args,
            timeout=timeout,
        )

    def pair_ble_wifi(
        self,
        node_id: int, ssid: str, password: str,
        setup_passcode: int, discriminator: int = 3840,
        timeout: int = 180,
    ) -> ChipToolResult:
        """Matter commissioning（BLE + Wi-Fi：node ssid password pin discriminator）"""
        return self._run(
            "pairing", "ble-wifi",
            str(node_id), ssid, password,
            str(setup_passcode), str(discriminator),
            timeout=timeout,
        )

    def list_nodes(self) -> ChipToolResult:
        """列出 fabric 内所有节点"""
        return self._run("discovery", "list-nodes")


# ============================================================
# 健康检查
# ============================================================


def is_chip_tool_available(chip_tool_path: str = "chip-tool") -> bool:
    """检查 chip-tool 是否可用"""
    try:
        result = subprocess.run(
            [chip_tool_path, "--help"],
            capture_output=True, timeout=5,
        )
        if result.returncode != 0:
            return False
        return (
            "Usage" in result.stdout
            or "Commands" in result.stdout
            or "usage" in result.stdout.lower()
        )
    except Exception:
        return False
