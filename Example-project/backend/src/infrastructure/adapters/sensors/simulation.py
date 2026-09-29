from __future__ import annotations

import random
from datetime import datetime, timezone

from domain.devices.entity import Device
from domain.sensors.ports import SensorPort
from domain.sensors.reading import Reading

_RANGES: dict[str, tuple[float, float, str]] = {
    "moisture_sensor": (0.2, 0.6, "vwc"),
    "light_sensor": (200.0, 2000.0, "lux"),
}


class SimulationSensorAdapter(SensorPort):
    def read(self, device: Device) -> Reading:
        if device.id is None:
            raise ValueError("Device id is required")
        low, high, unit = _RANGES.get(device.device_type, (0.0, 1.0, "unit"))
        return Reading(
            device_id=device.id,
            value=random.uniform(low, high),
            unit=unit,
            source="simulation",
            recorded_at=datetime.now(timezone.utc),
        )
