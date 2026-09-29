from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Device:
    id: UUID | None
    device_type: str
    role: str
    device_family: str
    display_name: str
    default_config: dict
    sampling_interval_seconds: int = 300
    tracking_enabled: bool = True
