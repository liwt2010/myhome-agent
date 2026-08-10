"""Matter 3 类设备实测（v2.4，2026-08-07 修订）

3 类设备(OnOff Light / Thermostat / DoorLock)端到端 + commission + 控制 + 读属性。
chip-tool 未装或 MATTER_MOCK=1 时使用 FakeChipToolAdapter 完整走一遍命令构造，
真机就绪后去掉 mock 即为真实联调脚本。

用法：
    python scripts/test_real_matter.py            # 真机（需 chip-tool）
    MATTER_MOCK=1 python scripts/test_real_matter.py  # mock 命令构造
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, ".")

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

_IS_MOCK = os.getenv("MATTER_MOCK") == "1"


class _FakeChipToolAdapter:
    """MATTER_MOCK 模式：记录命令、返回成功，用于锁定命令构造。"""

    def __init__(self, *args, **kwargs):
        self.chip_tool = "fake"
        self.calls: list[list[str]] = []
        self.success = True
        self.stdout = ""
        self.stderr = ""
        self.elapsed_ms = 0

    def _run(self, *args):
        self.calls.append(list(args))
        return self

    def onoff(self, node_id, endpoint, on):
        return self._run("onoff", "on" if on else "off", str(node_id), str(endpoint))

    def level(self, node_id, endpoint, level):
        return self._run(
            "levelcontrol", "move-to-level",
            str(level), "0", "0", "0", str(node_id), str(endpoint),
        )

    def color_temperature(self, node_id, endpoint, mireds):
        return self._run(
            "colorcontrol", "move-to-color-temperature",
            str(mireds), "0", "0", "0", str(node_id), str(endpoint),
        )

    def lock_door(self, node_id, endpoint):
        return self._run("doorlock", "lock-door", str(node_id), str(endpoint))

    def unlock_door(self, node_id, endpoint):
        return self._run("doorlock", "unlock-door", str(node_id), str(endpoint))

    def thermostat_setpoint(self, node_id, endpoint, target_temp_c, mode="heat"):
        attr = "occupied-heating-setpoint" if mode == "heat" else "occupied-cooling-setpoint"
        return self._run(
            "thermostat", "write", attr,
            str(int(round(target_temp_c * 100))),
            str(node_id), str(endpoint),
        )

    def read_attribute(self, node_id, endpoint, cluster, attribute):
        return self._run(cluster.lower(), "read", attribute, str(node_id), str(endpoint))

    def commission(self, setup_passcode, discriminator=3840, node_id=None,
                   thread_dataset_hex=None, timeout=120):
        args = ["pairing", "ble-thread", str(node_id or 1)]
        if thread_dataset_hex:
            dataset = thread_dataset_hex if thread_dataset_hex.startswith("hex:") else f"hex:{thread_dataset_hex}"
            args.append(dataset)
        args.extend([str(setup_passcode), str(discriminator)])
        return self._run(*args)

    def pair_ble_wifi(self, node_id, ssid, password, setup_passcode,
                      discriminator=3840, timeout=180):
        return self._run(
            "pairing", "ble-wifi",
            str(node_id), ssid, password, str(setup_passcode), str(discriminator),
        )


def _pick_adapter():
    from myhome_agent.collectors.chip_tool_wrapper import ChipToolAdapter, is_chip_tool_available

    if _IS_MOCK:
        print("  ⚠️  MATTER_MOCK=1：使用 FakeChipToolAdapter 验证命令构造")
        return _FakeChipToolAdapter(), True
    adapter = ChipToolAdapter()
    if is_chip_tool_available(adapter.chip_tool):
        return adapter, False
    print("  ⚠️  chip-tool 未装：降级为 FakeChipToolAdapter（命令构造验证）")
    return _FakeChipToolAdapter(), True


def _show_calls(adapter):
    for call in getattr(adapter, "calls", []):
        print(f"     chip-tool {' '.join(call)}")


def test_onoff_light():
    print("=" * 70)
    print("  v2.4 Matter OnOff Light 实测")
    print("=" * 70)
    adapter, is_mock = _pick_adapter()

    print("\n  1. Commissioning（跳过真机配网）")
    print("     chip-tool pairing ble-thread <node-id> <discriminator> <passcode>")

    print("\n  2. 控制 + 读状态：")
    for cmd, on in [("on", True), ("off", False)]:
        result = adapter.onoff(1, 1, on)
        print(f"     {cmd}: success={result.success}")
    result = adapter.read_attribute(1, 1, "OnOff", "OnOff")
    print(f"     读 OnOff: success={result.success}")

    if is_mock:
        _show_calls(adapter)


def test_thermostat():
    print()
    print("=" * 70)
    print("  v2.4 Matter Thermostat 实测")
    print("=" * 70)
    adapter, is_mock = _pick_adapter()

    print("\n  1. 设目标温度 24°C（写 occupied-heating-setpoint，毫度）")
    result = adapter.thermostat_setpoint(1, 1, 24.0)
    print(f"     set: success={result.success}")

    print("\n  2. 读当前温度：")
    result = adapter.read_attribute(1, 1, "TemperatureMeasurement", "MeasuredValue")
    print(f"     temp: success={result.success}")

    if is_mock:
        _show_calls(adapter)


def test_door_lock():
    print()
    print("=" * 70)
    print("  v2.4 Matter DoorLock 实测")
    print("=" * 70)
    adapter, is_mock = _pick_adapter()

    print("\n  1. 上锁 / 开锁：")
    result = adapter.lock_door(1, 1)
    print(f"     lock: success={result.success}")
    result = adapter.unlock_door(1, 1)
    print(f"     unlock: success={result.success}")

    print("\n  2. 状态：")
    result = adapter.read_attribute(1, 1, "DoorLock", "LockState")
    print(f"     state: success={result.success}")

    if is_mock:
        _show_calls(adapter)


def performance_summary():
    print()
    print("=" * 70)
    print("  v2.4 性能基准（目标值，需真机实测确认）")
    print("=" * 70)
    print(f"  OnOff 控制延迟            < 200ms")
    print(f"  Thermostat 设温延迟        < 500ms")
    print(f"  DoorLock 上锁延迟          < 1000ms")
    print(f"  状态读回                  < 100ms")
    print(f"  100 设备并发 (chip-tool)    待实测")
    print(f"  3 类设备组合 multi-admin Fabric   待实测")


def main():
    test_onoff_light()
    test_thermostat()
    test_door_lock()
    performance_summary()


if __name__ == "__main__":
    main()
