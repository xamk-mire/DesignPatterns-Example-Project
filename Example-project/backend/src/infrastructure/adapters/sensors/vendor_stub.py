from __future__ import annotations

from datetime import datetime, timezone

from domain.devices.entity import Device
from domain.sensors.ports import SensorPort
from domain.sensors.reading import Reading


class VendorStubSensorAdapter(SensorPort):
    """Translates a vendor raw shape. The router never sees that shape."""

    def read(self, device: Device) -> Reading:
        if device.device_type == "light_sensor":
            raw = {"lux_tenths": 8500}
        else:
            raw = {"milli_vwc": 410}
        return self.translate_raw(device, raw)

    def translate_raw(self, device: Device, raw: dict) -> Reading:
        if device.id is None:
            raise ValueError("Device id is required")
        value, unit = _normalize(raw)
        return Reading(
            device_id=device.id,
            value=value,
            unit=unit,
            source="vendor",
            recorded_at=datetime.now(timezone.utc),
        )


def _normalize(raw: dict) -> tuple[float, str]:
    if "milli_vwc" in raw:
        return float(raw["milli_vwc"]) / 1000.0, "vwc"
    if "lux_tenths" in raw:
        return float(raw["lux_tenths"]) / 10.0, "lux"
    raise ValueError("Unrecognized vendor payload")
