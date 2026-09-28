from __future__ import annotations

from domain.locations.entity import Location, LocationConfig, Zone
from domain.locations.errors import ConfigurationError

_MIN_VWC = 0.0
_MAX_VWC = 1.0


class LocationConfigBuilder:
    def __init__(self) -> None:
        self._name: str | None = None
        self._zones: list[Zone] = []

    def with_location_name(self, name: str) -> LocationConfigBuilder:
        self._name = name
        return self

    def add_zone(
        self,
        name: str,
        moisture_threshold_low: float,
        moisture_threshold_high: float,
        schedule: dict | None = None,
    ) -> LocationConfigBuilder:
        self._zones.append(
            Zone(
                name=name.strip(),
                moisture_threshold_low=float(moisture_threshold_low),
                moisture_threshold_high=float(moisture_threshold_high),
                schedule=dict(schedule or {}),
            )
        )
        return self

    def build(self) -> LocationConfig:
        name = (self._name or "").strip()
        if not name:
            raise ConfigurationError("Location name is required")
        if not self._zones:
            raise ConfigurationError("At least one zone is required")
        checked: list[Zone] = []
        for zone in self._zones:
            prepared = _checked_zone(zone)
            reject_duplicate_zone_name(prepared.name, [item.name for item in checked])
            checked.append(prepared)
        return LocationConfig(location=Location(name=name, zones=tuple(checked)))


def reject_duplicate_zone_name(name: str, existing_names: list[str]) -> None:
    if name in existing_names:
        raise ConfigurationError("Zone name must be unique within the location")


def validate_zone_fields(
    name: str,
    moisture_threshold_low: float,
    moisture_threshold_high: float,
) -> tuple[str, float, float]:
    cleaned = name.strip()
    if not cleaned:
        raise ConfigurationError("Zone name is required")
    low = float(moisture_threshold_low)
    high = float(moisture_threshold_high)
    _validate_thresholds(low, high)
    return cleaned, low, high


def _checked_zone(zone: Zone) -> Zone:
    name, low, high = validate_zone_fields(
        zone.name,
        zone.moisture_threshold_low,
        zone.moisture_threshold_high,
    )
    return Zone(name=name, moisture_threshold_low=low, moisture_threshold_high=high, schedule=dict(zone.schedule))


def _validate_thresholds(low: float, high: float) -> None:
    if not (_MIN_VWC <= low <= _MAX_VWC) or not (_MIN_VWC <= high <= _MAX_VWC):
        raise ConfigurationError("Moisture thresholds must be between 0 and 1")
    if low >= high:
        raise ConfigurationError("Moisture threshold low must be strictly less than high")
