from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ReadingCreated:
    device_id: UUID
    location_id: UUID | None
    zone_id: UUID | None
    value: float
    unit: str
    source: str
    recorded_at: datetime


@dataclass(frozen=True)
class ThresholdCrossed:
    device_id: UUID | None
    location_id: UUID | None
    zone_id: UUID | None


@dataclass(frozen=True)
class CommandFailed:
    device_id: UUID | None
    location_id: UUID | None
    zone_id: UUID | None
    message: str


@dataclass(frozen=True)
class ActuatorEnteredError:
    device_id: UUID | None
    location_id: UUID | None
    zone_id: UUID | None
