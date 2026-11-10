from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from uuid import UUID

from domain.actuators.ports import ActuatorPort
from infrastructure.persistence.actuator_state_repository import ActuatorStateRepository

MAX_RUN = timedelta(minutes=30)


class MaxRunTimeExceeded(Exception):
    def __init__(self) -> None:
        super().__init__("Max run time exceeded")


class MaxRunTimeActuatorDecorator(ActuatorPort):
    def __init__(
        self,
        inner: ActuatorPort,
        states: ActuatorStateRepository,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._inner = inner
        self._states = states
        self._now = now or (lambda: datetime.now(timezone.utc))

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        snapshot = self._states.snapshot(device_id)
        if snapshot is not None:
            state, updated_at = snapshot
            moment = self._now()
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)
            if state == "running" and moment - updated_at >= MAX_RUN:
                raise MaxRunTimeExceeded
        self._inner.apply(device_id, command, payload)
