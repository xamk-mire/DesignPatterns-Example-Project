from domain.devices.entity import Device
from domain.devices.family_factory import get_family_factory
from infrastructure.persistence.actuator_state_repository import ActuatorStateRepository
from infrastructure.persistence.device_repository import DeviceRepository


class DeviceFamilyService:
    def __init__(self, repo: DeviceRepository, states: ActuatorStateRepository | None = None) -> None:
        self._repo = repo
        self._states = states

    def provision_family(self, family: str) -> list[Device]:
        factory = get_family_factory(family)
        devices = self._repo.save_devices(factory.create_device_set())
        if self._states is not None:
            self._states.ensure_idle(
                [device.id for device in devices if device.role == "actuator" and device.id is not None]
            )
        return devices

    def list_devices(
        self,
        *,
        device_family: str | None = None,
        role: str | None = None,
    ) -> list[Device]:
        return self._repo.list_devices(device_family=device_family, role=role)
