from domain.devices.family_factory import (
    EdgeHardwareFactory,
    SimulationDeviceFactory,
    get_family_factory,
)


def test_simulation_factory_returns_four_devices() -> None:
    devices = SimulationDeviceFactory().create_device_set()
    assert len(devices) == 4
    assert {device.device_family for device in devices} == {"simulation"}
    assert {device.role for device in devices} == {"sensor", "actuator"}
    assert sum(1 for device in devices if device.role == "sensor") == 2
    assert sum(1 for device in devices if device.role == "actuator") == 2


def test_edge_factory_differs_from_simulation() -> None:
    simulation = SimulationDeviceFactory().create_device_set()
    edge = EdgeHardwareFactory().create_device_set()
    assert {device.device_family for device in edge} == {"edge"}
    assert len(edge) == 4
    sim_protocol = simulation[0].default_config["protocol"]
    edge_protocol = edge[0].default_config["protocol"]
    assert sim_protocol != edge_protocol
    assert sim_protocol == "simulation"
    assert edge_protocol == "mqtt"


def test_unknown_family_raises() -> None:
    try:
        get_family_factory("live")
    except ValueError as exc:
        assert "Unknown device family" in str(exc)
    else:
        raise AssertionError("expected ValueError")
