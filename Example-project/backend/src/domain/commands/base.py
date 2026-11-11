from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.actuators.ports import ActuatorPort


class Command(ABC):
    command_type: str
    target_state: str | None

    def __init__(self, device_id: UUID, payload: dict) -> None:
        self.device_id = device_id
        self.payload = payload

    @abstractmethod
    def execute(self, port: ActuatorPort) -> None:
        """Run this command through the actuator port."""


class UnknownCommand(Exception):
    pass
