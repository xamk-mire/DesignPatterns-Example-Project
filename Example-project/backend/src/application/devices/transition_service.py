from uuid import UUID

from application.devices.dto import DeviceDto
from application.devices.mappers import device_to_dto
from domain.actuators.state import ActuatorContext
from infrastructure.persistence.actuator_state_repository import ActuatorStateRepository
from infrastructure.persistence.device_repository import DeviceRepository


class ActuatorNotFound(Exception):
    pass


class ActuatorTransitionService:
    def __init__(self, devices: DeviceRepository, states: ActuatorStateRepository) -> None:
        self._devices = devices
        self._states = states

    def transition(self, device_id: UUID, target: str) -> DeviceDto:
        device = self._devices.get_device(device_id)
        if device is None or device.role != "actuator" or device.id is None:
            raise ActuatorNotFound(str(device_id))
        current = self._states.get(device.id)
        if current is None:
            raise ActuatorNotFound(str(device_id))
        context = ActuatorContext(current, device.device_type)
        context.transition(target)
        self._states.save(device.id, context.state)
        return device_to_dto(device, context.state)
