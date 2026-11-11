from domain.events.bus import EventBus
from domain.events.events import (
    ActuatorEnteredError,
    CommandFailed,
    ReadingCreated,
    ThresholdCrossed,
)
from infrastructure.db import SessionLocal
from infrastructure.persistence.alert_repository import AlertRepository
from infrastructure.persistence.location_repository import LocationRepository


class MoistureThresholdSubscriber:
    def __init__(self, bus: EventBus) -> None:
        self._bus = bus

    def subscribe(self) -> None:
        self._bus.subscribe(ReadingCreated, self.on_reading)

    def on_reading(self, event: ReadingCreated) -> None:
        if event.unit != "vwc" or event.zone_id is None:
            return
        session = SessionLocal()
        try:
            zone = LocationRepository(session).get_zone(event.zone_id)
        finally:
            session.close()
        if zone is None or event.value >= zone.moisture_threshold_low:
            return
        self._bus.publish(
            ThresholdCrossed(
                device_id=event.device_id,
                location_id=event.location_id,
                zone_id=event.zone_id,
            )
        )


class AlertPersistenceSubscriber:
    def __init__(self, bus: EventBus) -> None:
        self._bus = bus

    def subscribe(self) -> None:
        self._bus.subscribe(ThresholdCrossed, self.on_threshold)
        self._bus.subscribe(CommandFailed, self.on_command)
        self._bus.subscribe(ActuatorEnteredError, self.on_fault)

    def on_threshold(self, event: ThresholdCrossed) -> None:
        self._insert(
            location_id=event.location_id,
            zone_id=event.zone_id,
            device_id=event.device_id,
            severity="warning",
            message="Moisture below zone low",
            event_type="threshold.crossed",
        )

    def on_command(self, event: CommandFailed) -> None:
        self._insert(
            location_id=event.location_id,
            zone_id=event.zone_id,
            device_id=event.device_id,
            severity="warning",
            message=event.message,
            event_type="command.failed",
        )

    def on_fault(self, event: ActuatorEnteredError) -> None:
        self._insert(
            location_id=event.location_id,
            zone_id=event.zone_id,
            device_id=event.device_id,
            severity="critical",
            message="Actuator entered error",
            event_type="state.changed",
        )

    def _insert(
        self,
        *,
        location_id,
        zone_id,
        device_id,
        severity: str,
        message: str,
        event_type: str,
    ) -> None:
        session = SessionLocal()
        try:
            AlertRepository(session).insert(
                location_id=location_id,
                zone_id=zone_id,
                device_id=device_id,
                severity=severity,
                message=message,
                event_type=event_type,
            )
        finally:
            session.close()
