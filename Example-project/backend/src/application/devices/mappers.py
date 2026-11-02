from uuid import UUID

from application.devices.dto import DeviceDto
from domain.actuators.state import ActuatorContext
from domain.devices.entity import Device


def device_to_dto(device: Device, state: str | None = None) -> DeviceDto:
    if device.id is None:
        raise RuntimeError("Persisted device is missing an id")
    commands: list[str] = []
    targets: list[str] = []
    persisted = state if device.role == "actuator" else None
    if persisted is not None:
        context = ActuatorContext(persisted, device.device_type)
        commands = context.allowed_commands()
        targets = context.allowed_targets()
    return DeviceDto(
        id=device.id,
        device_type=device.device_type,
        role=device.role,
        device_family=device.device_family,
        display_name=device.display_name,
        default_config=device.default_config,
        state=persisted,
        allowed_commands=commands,
        allowed_targets=targets,
    )


def devices_to_dtos(devices: list[Device], states: dict[UUID, str] | None = None) -> list[DeviceDto]:
    saved = states or {}
    return [
        device_to_dto(device, saved.get(device.id) if device.id is not None else None)
        for device in devices
    ]
