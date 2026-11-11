from uuid import UUID

from application.devices.dto import DeviceDto
from application.devices.mappers import device_to_dto
from domain.actuators.state import ActuatorContext
from domain.events.bus import EventBus
from domain.events.events import ActuatorEnteredError
from infrastructure.persistence.actuator_state_repository import ActuatorStateRepository
from infrastructure.persistence.device_repository import DeviceRepository


class ActuatorNotFound(Exception):
    pass


class ActuatorTransitionService:
    def __init__(
        self,
        devices: DeviceRepository,
        states: ActuatorStateRepository,
        bus: EventBus | None = None,
    ) -> None:
        self._devices = devices
        self._states = states
        self._bus = bus

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
        if context.state == "error":
            self._publish(
                ActuatorEnteredError(
                    device_id=device.id,
                    location_id=device.location_id,
                    zone_id=device.zone_id,
                )
            )
        return device_to_dto(device, context.state)

    def _publish(self, event: ActuatorEnteredError) -> None:
        bus = self._bus
        if bus is None:
            from application.alerts.wiring import get_event_bus

            bus = get_event_bus()
        bus.publish(event)
