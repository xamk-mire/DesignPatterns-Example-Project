from __future__ import annotations

from datetime import datetime, timezone

from domain.devices.entity import Device
from domain.sensors.reading import Reading


class MqttSensorAdapter:
    """Translate an inbound payload dict. This phase does not open a broker socket."""

    def translate(self, device: Device, payload: dict) -> Reading:
        if device.id is None:
            raise ValueError("Device id is required")
        if "value" not in payload or "unit" not in payload:
            raise ValueError("MQTT payload requires value and unit")
        return Reading(
            device_id=device.id,
            value=float(payload["value"]),
            unit=str(payload["unit"]),
            source="mqtt",
            recorded_at=datetime.now(timezone.utc),
        )
