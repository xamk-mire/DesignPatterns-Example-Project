from domain.devices.entity import Device
from domain.sensors.ports import SensorPort
from infrastructure.adapters.sensors.simulation import SimulationSensorAdapter
from infrastructure.adapters.sensors.vendor_stub import VendorStubSensorAdapter


class AdapterSelectionError(Exception):
    """No one-shot sensor port matches this device."""


def sensor_port_for(device: Device) -> SensorPort:
    """Pick a SensorPort for POST /read.

    ``default_config.vendor_stub`` true selects the vendor stub so it does not
    collide with ``protocol`` ``simulation`` or ``mqtt``. MQTT devices are
    translate-only: pass the payload to ``MqttSensorAdapter.translate``.
    """
    config = device.default_config or {}
    if config.get("vendor_stub") is True:
        return VendorStubSensorAdapter()
    protocol = config.get("protocol")
    if protocol == "simulation":
        return SimulationSensorAdapter()
    if protocol == "mqtt":
        raise AdapterSelectionError("MQTT devices accept a translated payload, not a one-shot read")
    raise AdapterSelectionError(f"No sensor adapter for protocol {protocol!r}")
