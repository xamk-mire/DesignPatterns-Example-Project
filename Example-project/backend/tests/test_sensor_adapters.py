from uuid import uuid4

from domain.devices.entity import Device
from infrastructure.adapters.actuators.simulation import SimulationActuatorAdapter
from infrastructure.adapters.sensors.mqtt import MqttSensorAdapter
from infrastructure.adapters.sensors.simulation import SimulationSensorAdapter
from infrastructure.adapters.sensors.vendor_stub import VendorStubSensorAdapter


def _device(device_type: str = "moisture_sensor") -> Device:
    return Device(
        id=uuid4(),
        device_type=device_type,
        role="sensor",
        device_family="simulation",
        display_name="Probe",
        default_config={"protocol": "simulation"},
    )


def test_vendor_adapter_normalizes_raw_payload() -> None:
    device = _device()
    reading = VendorStubSensorAdapter().translate_raw(device, {"milli_vwc": 410})
    assert reading.source == "vendor"
    assert reading.unit == "vwc"
    assert reading.value == 0.41
    assert reading.device_id == device.id


def test_simulation_adapter_value_in_range() -> None:
    moisture = SimulationSensorAdapter()
    light = SimulationSensorAdapter()
    for _ in range(20):
        wet = moisture.read(_device("moisture_sensor"))
        bright = light.read(_device("light_sensor"))
        assert wet.source == "simulation"
        assert wet.unit == "vwc"
        assert 0.2 <= wet.value <= 0.6
        assert bright.source == "simulation"
        assert bright.unit == "lux"
        assert 200 <= bright.value <= 2000


def test_mqtt_adapter_translates_payload() -> None:
    device = _device()
    reading = MqttSensorAdapter().translate(device, {"value": 0.41, "unit": "vwc"})
    assert reading.source == "mqtt"
    assert reading.value == 0.41
    assert reading.unit == "vwc"
    assert reading.device_id == device.id
    assert reading.recorded_at.tzinfo is not None


def test_simulation_actuator_records_apply() -> None:
    device_id = uuid4()
    adapter = SimulationActuatorAdapter()
    adapter.apply(device_id, "start_pump", {"seconds": 5})
    assert adapter.applied == [(device_id, "start_pump", {"seconds": 5})]
