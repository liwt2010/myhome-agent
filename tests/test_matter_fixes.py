"""Matter 修复回归测试（2026-08-07）。"""
from __future__ import annotations


class _FakeResult:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _patch_run(monkeypatch, commands, returncode=0, stdout=""):
    def fake_run(cmd, **kwargs):
        commands.append(cmd)
        return _FakeResult(returncode=returncode, stdout=stdout)

    monkeypatch.setattr("subprocess.run", fake_run)


class TestIdTables:
    def test_device_and_cluster_ids(self):
        from myhome_agent.collectors.matter_adapter import (
            CLUSTER_TO_CAPABILITY,
            MATTER_CLUSTERS,
            MATTER_DEVICE_TYPES,
        )

        assert MATTER_DEVICE_TYPES[0x0100] == "OnOffLight"
        assert MATTER_DEVICE_TYPES[0x0301] == "Thermostat"
        assert MATTER_DEVICE_TYPES[0x0011] == "PowerSource"
        assert MATTER_DEVICE_TYPES[0x0142] == "Camera"
        assert 0x0101 in MATTER_CLUSTERS       # DoorLock
        assert 0x0201 in MATTER_CLUSTERS       # Thermostat
        assert 0x0402 in MATTER_CLUSTERS       # TemperatureMeasurement
        assert 0x0400 in MATTER_CLUSTERS       # IlluminanceMeasurement
        assert 0x0406 in MATTER_CLUSTERS       # OccupancySensing
        assert 0x005B in MATTER_CLUSTERS       # AirQuality
        assert 0x005C in MATTER_CLUSTERS       # SmokeCOAlarm
        assert 0x040C in MATTER_CLUSTERS       # CO concentration
        assert 0x040D in MATTER_CLUSTERS       # CO2 concentration
        assert 0x0045 in MATTER_CLUSTERS       # BooleanState
        assert CLUSTER_TO_CAPABILITY[0x0101] == "lock.lock"
        assert CLUSTER_TO_CAPABILITY[0x0201] == "ac.target_temp"
        assert CLUSTER_TO_CAPABILITY[0x0402] == "sensor.temperature"
        assert CLUSTER_TO_CAPABILITY[0x0400] == "sensor.illuminance"
        assert CLUSTER_TO_CAPABILITY[0x005B] == "sensor.air_quality"
        assert CLUSTER_TO_CAPABILITY[0x005C] == "sensor.smoke"
        assert CLUSTER_TO_CAPABILITY[0x0045] == "sensor.water_leak"


class TestChipToolWrapper:
    def test_command_construction(self, monkeypatch):
        from myhome_agent.collectors.chip_tool_wrapper import ChipToolAdapter

        commands = []
        _patch_run(monkeypatch, commands, stdout="Usage: chip-tool")
        adapter = ChipToolAdapter()
        commands.clear()

        adapter.onoff(1, 2, True)
        adapter.level(1, 2, 100)
        adapter.color_temperature(1, 2, 300)
        adapter.lock_door(1, 2)
        adapter.unlock_door(1, 2)
        adapter.thermostat_setpoint(1, 2, 24.0)
        adapter.read_attribute(1, 2, "Thermostat", "OccupiedHeatingSetpoint")
        adapter.commission(20202021, discriminator=3840, node_id=5, thread_dataset_hex="abcd")
        adapter.pair_ble_wifi(5, "ssid", "pass", 20202021, 3840)

        assert ["chip-tool", "onoff", "on", "1", "2"] in commands
        assert ["chip-tool", "levelcontrol", "move-to-level", "100", "0", "0", "0", "1", "2"] in commands
        assert ["chip-tool", "thermostat", "write", "occupied-heating-setpoint", "2400", "1", "2"] in commands
        assert ["chip-tool", "thermostat", "read", "OccupiedHeatingSetpoint", "1", "2"] in commands
        assert ["chip-tool", "pairing", "ble-thread", "5", "hex:abcd", "20202021", "3840"] in commands
        assert ["chip-tool", "pairing", "ble-wifi", "5", "ssid", "pass", "20202021", "3840"] in commands


class TestRealMatterAdapter:
    def test_execute_action_contract(self, monkeypatch):
        from myhome_agent.collectors.matter_real import RealMatterAdapter

        commands = []
        _patch_run(monkeypatch, commands, stdout="Usage: chip-tool")
        adapter = RealMatterAdapter({"backend": "chip_tool"})
        assert adapter.connect() is True
        commands.clear()

        result = adapter.execute_action("1/2", "light.toggle", {"on": True})
        assert result["success"] is True
        assert "state" in result and "message" in result
        assert commands[0][:3] == ["chip-tool", "onoff", "on"]
        assert adapter._do_health_check() is True

    def test_health_false_when_chip_tool_missing(self, monkeypatch):
        from myhome_agent.collectors.matter_real import RealMatterAdapter

        def raise_not_found(*args, **kwargs):
            raise FileNotFoundError()

        monkeypatch.setattr("subprocess.run", raise_not_found)
        adapter = RealMatterAdapter({"backend": "chip_tool"})
        assert adapter.connect() is False
        assert adapter._do_health_check() is False

    def test_discover_parses_list_nodes(self, monkeypatch):
        from myhome_agent.collectors.matter_real import RealMatterAdapter

        def fake_run(cmd, **kwargs):
            stdout = "NodeId: 0x1234\nNodeId: 0xabcd\n" if "list-nodes" in cmd else "Usage: chip-tool"
            return _FakeResult(returncode=0, stdout=stdout)

        monkeypatch.setattr("subprocess.run", fake_run)
        adapter = RealMatterAdapter({"backend": "chip_tool"})
        assert adapter.connect() is True
        devices = adapter.discover()
        assert {d.ecosystem_id for d in devices} == {"0x1234", "0xabcd"}

    def test_get_state_reads_multiple_clusters(self, monkeypatch):
        from myhome_agent.collectors.matter_real import RealMatterAdapter

        def fake_run(cmd, **kwargs):
            stdout = "Usage: chip-tool" if "--help" in cmd else "42"
            return _FakeResult(returncode=0, stdout=stdout)

        monkeypatch.setattr("subprocess.run", fake_run)
        adapter = RealMatterAdapter({"backend": "chip_tool"})
        assert adapter.connect() is True
        state = adapter.get_state("1/2")
        assert "OnOff.OnOff" in state
        assert "DoorLock.LockState" in state
        assert "TemperatureMeasurement.MeasuredValue" in state


class TestMatterAdapter:
    def test_chip_tool_delegation(self, monkeypatch):
        from myhome_agent.collectors.matter_adapter import MatterAdapter

        commands = []
        _patch_run(monkeypatch, commands, stdout="Usage: chip-tool")
        adapter = MatterAdapter({"chip_tool_path": "chip-tool"})
        assert adapter.connect() is True
        assert adapter._chip_tool is not None
        commands.clear()

        result = adapter.execute_action("1/2", "lock.lock")
        assert result["success"] is True
        assert "message" in result and "state" in result
        assert commands[0][:3] == ["chip-tool", "doorlock", "lock-door"]
        assert adapter._do_health_check() is True


class TestCreateAdapter:
    def test_matter_zigbee_thread_factory(self):
        from myhome_agent.collectors.ecosystem import create_adapter

        for ecosystem in ("matter", "zigbee", "thread"):
            adapter = create_adapter(ecosystem, {"backend": "stub"})
            assert adapter is not None
