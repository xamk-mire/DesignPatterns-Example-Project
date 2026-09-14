from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class Sensor:
    device_type: str
    display_name: str
    default_config: dict
    id: uuid.UUID | None = None
