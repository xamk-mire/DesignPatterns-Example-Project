from __future__ import annotations

from abc import ABC, abstractmethod

from domain.devices.entity import Device
from domain.sensors.creators import LightSensorCreator, MoistureSensorCreator
from domain.sensors.entity import Sensor


def _sensor_to_device(sensor: Sensor, family: str, protocol: str, name_prefix: str) -> Device:
    return Device(
        id=None,
        device_type=sensor.device_type,
        role="sensor",
        device_family=family,
        display_name=f"{name_prefix} {sensor.display_name}",
        default_config={**sensor.default_config, "protocol": protocol},
    )


def _actuator(
    family: str,
    protocol: str,
    device_type: str,
    display_name: str,
) -> Device:
    return Device(
        id=None,
        device_type=device_type,
        role="actuator",
        device_family=family,
        display_name=display_name,
        default_config={"protocol": protocol},
    )


class DeviceFamilyFactory(ABC):
    @property
    @abstractmethod
    def family_key(self) -> str:
        ...

    @abstractmethod
    def create_device_set(self) -> list[Device]:
        ...


class SimulationDeviceFactory(DeviceFamilyFactory):
    @property
    def family_key(self) -> str:
        return "simulation"

    def create_device_set(self) -> list[Device]:
        protocol = "sim"
        prefix = "Sim"
        moisture = MoistureSensorCreator().create_sensor()
        light = LightSensorCreator().create_sensor()
        return [
            _sensor_to_device(moisture, self.family_key, protocol, prefix),
            _sensor_to_device(light, self.family_key, protocol, prefix),
            _actuator(self.family_key, protocol, "water_pump", "Sim irrigation pump"),
            _actuator(self.family_key, protocol, "grow_light", "Sim grow light"),
        ]


class EdgeHardwareFactory(DeviceFamilyFactory):
    @property
    def family_key(self) -> str:
        return "edge"

    def create_device_set(self) -> list[Device]:
        protocol = "gpio-stub"
        prefix = "Edge"
        moisture = MoistureSensorCreator().create_sensor()
        light = LightSensorCreator().create_sensor()
        return [
            _sensor_to_device(moisture, self.family_key, protocol, prefix),
            _sensor_to_device(light, self.family_key, protocol, prefix),
            _actuator(self.family_key, protocol, "water_pump", "Edge irrigation pump"),
            _actuator(self.family_key, protocol, "grow_light", "Edge grow light"),
        ]


_FACTORIES: dict[str, DeviceFamilyFactory] = {
    "simulation": SimulationDeviceFactory(),
    "edge": EdgeHardwareFactory(),
}


def get_family_factory(family: str) -> DeviceFamilyFactory:
    try:
        return _FACTORIES[family]
    except KeyError:
        raise ValueError(f"Unknown device family: {family}") from None
