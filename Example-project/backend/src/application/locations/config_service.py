from uuid import UUID

from application.locations.dto import (
    BuildLocationConfigRequestDto,
    LocationConfigDto,
    LocationSummaryDto,
    ZoneDto,
    ZoneRequestDto,
)
from application.locations.mappers import location_config_to_dto, zone_to_dto
from domain.locations.config_builder import LocationConfigBuilder, reject_duplicate_zone_name, validate_zone_fields
from domain.locations.errors import ConfigurationError
from infrastructure.persistence.location_repository import LocationRepository


class LocationConfigService:
    def __init__(self, repo: LocationRepository) -> None:
        self._repo = repo

    def build_and_save(self, request: BuildLocationConfigRequestDto) -> LocationConfigDto:
        builder = LocationConfigBuilder().with_location_name(request.location_name)
        for zone in request.zones:
            builder.add_zone(
                name=zone.name,
                moisture_threshold_low=zone.moisture_threshold_low,
                moisture_threshold_high=zone.moisture_threshold_high,
                schedule=zone.schedule,
            )
        saved = self._repo.save_config(builder.build())
        return location_config_to_dto(saved)

    def get_config(self, location_id: UUID) -> LocationConfigDto | None:
        config = self._repo.get_config(location_id)
        if config is None:
            return None
        return location_config_to_dto(config)

    def list_locations(self) -> list[LocationSummaryDto]:
        return [LocationSummaryDto(id=location_id, name=name) for location_id, name in self._repo.list_locations()]

    def delete_location(self, location_id: UUID) -> bool:
        return self._repo.delete_location(location_id)

    def add_zone(self, location_id: UUID, request: ZoneRequestDto) -> ZoneDto | None:
        name, low, high = validate_zone_fields(
            request.name,
            request.moisture_threshold_low,
            request.moisture_threshold_high,
        )
        existing = self._repo.zone_names(location_id)
        if existing is None:
            return None
        reject_duplicate_zone_name(name, existing)
        zone = self._repo.add_zone(
            location_id,
            name=name,
            moisture_threshold_low=low,
            moisture_threshold_high=high,
            schedule=request.schedule,
        )
        if zone is None:
            return None
        return zone_to_dto(zone, location_id)

    def update_zone(self, location_id: UUID, zone_id: UUID, request: ZoneRequestDto) -> ZoneDto | None:
        name, low, high = validate_zone_fields(
            request.name,
            request.moisture_threshold_low,
            request.moisture_threshold_high,
        )
        if self._repo.get_zone_location_id(zone_id) != location_id:
            return None
        existing = self._repo.zone_names(location_id, exclude_zone_id=zone_id)
        if existing is None:
            return None
        reject_duplicate_zone_name(name, existing)
        zone = self._repo.update_zone(
            location_id,
            zone_id,
            name=name,
            moisture_threshold_low=low,
            moisture_threshold_high=high,
            schedule=request.schedule,
        )
        if zone is None:
            return None
        return zone_to_dto(zone, location_id)

    def delete_zone(self, location_id: UUID, zone_id: UUID) -> bool:
        count = self._repo.zone_count(location_id)
        if count is None:
            return False
        if self._repo.get_zone_location_id(zone_id) != location_id:
            return False
        if count <= 1:
            raise ConfigurationError("A location must keep at least one zone")
        return self._repo.delete_zone(location_id, zone_id)
