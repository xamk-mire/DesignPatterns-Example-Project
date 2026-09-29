from uuid import UUID

from domain.actuators.ports import ActuatorPort


class SimulationActuatorAdapter(ActuatorPort):
    """Records apply calls in memory. No GPIO."""

    def __init__(self) -> None:
        self.applied: list[tuple[UUID, str, dict]] = []

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        self.applied.append((device_id, command, dict(payload)))
