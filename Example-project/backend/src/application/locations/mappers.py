from uuid import UUID

from application.locations.dto import LocationConfigDto, LocationSummaryDto, ZoneDto
from domain.locations.entity import LocationConfig, Zone


def location_config_to_dto(config: LocationConfig) -> LocationConfigDto:
    location = config.location
    if location.id is None:
        raise RuntimeError("Persisted location is missing an id")
    zones: list[ZoneDto] = []
    for zone in location.zones:
        if zone.id is None:
            raise RuntimeError("Persisted zone is missing an id")
        zones.append(
            ZoneDto(
                id=zone.id,
                location_id=location.id,
                name=zone.name,
                moisture_threshold_low=zone.moisture_threshold_low,
                moisture_threshold_high=zone.moisture_threshold_high,
                schedule=zone.schedule,
            )
        )
    return LocationConfigDto(
        location=LocationSummaryDto(id=location.id, name=location.name),
        zones=zones,
    )


def zone_to_dto(zone: Zone, location_id: UUID) -> ZoneDto:
    if zone.id is None:
        raise RuntimeError("Persisted zone is missing an id")
    return ZoneDto(
        id=zone.id,
        location_id=location_id,
        name=zone.name,
        moisture_threshold_low=zone.moisture_threshold_low,
        moisture_threshold_high=zone.moisture_threshold_high,
        schedule=zone.schedule,
    )
