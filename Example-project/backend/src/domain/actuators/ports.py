from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class ActuatorPort(ABC):
    @abstractmethod
    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        """Apply a command. This phase only stubs the call."""
