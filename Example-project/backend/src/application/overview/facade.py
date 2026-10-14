from uuid import UUID

from sqlalchemy.orm import Session

from application.automation.service import AutomationService, LocationNotFound
from application.locations.dto import LocationSummaryDto
from application.overview.dto import (
    DeviceCountsDto,
    LocationOverviewDto,
    OverviewDeviceDto,
    OverviewReadingDto,
    OverviewZoneDto,
    RecommendationDto,
)
from infrastructure.persistence.automation_repository import AutomationRepository
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.location_repository import LocationRepository
from infrastructure.persistence.reading_repository import ReadingRepository


class LocationOverviewFacade:
    def __init__(
        self,
        locations: LocationRepository,
        devices: DeviceRepository,
        readings: ReadingRepository,
        rules: AutomationRepository,
        automation: AutomationService,
    ) -> None:
        self._locations = locations
        self._devices = devices
        self._readings = readings
        self._rules = rules
        self._automation = automation

    def get_overview(self, location_id: UUID) -> LocationOverviewDto:
        config = self._locations.get_config(location_id)
        if config is None or config.location.id is None:
            raise LocationNotFound(str(location_id))
        assigned = self._devices.list_assigned(location_id)
        latest = {
            reading.device_id: reading
            for reading in self._readings.latest_for_devices(
                [device.id for device in assigned if device.id is not None]
            )
        }
        sensor_count = 0
        actuator_count = 0
        zones: list[OverviewZoneDto] = []
        for zone in config.location.zones:
            if zone.id is None:
                continue
            zone_devices = [device for device in assigned if device.zone_id == zone.id and device.id is not None]
            sensor_count += sum(1 for device in zone_devices if device.role == "sensor")
            actuator_count += sum(1 for device in zone_devices if device.role == "actuator")
            readings: list[OverviewReadingDto] = []
            for device in zone_devices:
                assert device.id is not None
                reading = latest.get(device.id)
                if reading is None:
                    continue
                readings.append(
                    OverviewReadingDto(
                        device_id=device.id,
                        value=reading.value,
                        unit=reading.unit,
                        recorded_at=reading.recorded_at,
                        tracking_enabled=device.tracking_enabled,
                        sampling_interval_seconds=device.sampling_interval_seconds,
                    )
                )
            zones.append(
                OverviewZoneDto(
                    id=zone.id,
                    name=zone.name,
                    moisture_threshold_low=zone.moisture_threshold_low,
                    moisture_threshold_high=zone.moisture_threshold_high,
                    devices=[
                        OverviewDeviceDto(
                            id=device.id,
                            device_type=device.device_type,
                            role=device.role,
                            display_name=device.display_name,
                        )
                        for device in zone_devices
                        if device.id is not None
                    ],
                    latest_readings=readings,
                )
            )
        strategy_key = self._rules.get_key(location_id)
        recommendation = None
        if strategy_key is not None:
            evaluation = self._automation.evaluate(location_id)
            recommendation = RecommendationDto(action=evaluation.action, reason=evaluation.reason)
        return LocationOverviewDto(
            location=LocationSummaryDto(id=config.location.id, name=config.location.name),
            device_counts=DeviceCountsDto(sensor=sensor_count, actuator=actuator_count),
            zones=zones,
            strategy_key=strategy_key,
            last_recommendation=recommendation,
        )


def build_overview_facade(session: Session) -> LocationOverviewFacade:
    locations = LocationRepository(session)
    devices = DeviceRepository(session)
    readings = ReadingRepository(session)
    rules = AutomationRepository(session)
    return LocationOverviewFacade(
        locations,
        devices,
        readings,
        rules,
        AutomationService(locations, rules, readings),
    )
