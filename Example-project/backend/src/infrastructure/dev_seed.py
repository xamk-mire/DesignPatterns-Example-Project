"""Known dashboard data for local reset and pytest. Not the later Phase 12 seed."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from application.devices.family_service import DeviceFamilyService
from application.locations.config_service import LocationConfigService
from application.locations.dto import BuildLocationConfigRequestDto, ZoneRequestDto
from application.locations.zone_assignment_service import ZoneAssignmentService
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.location_repository import LocationRepository

TRUNCATE_BUSINESS_TABLES = (
    "TRUNCATE TABLE sensor_readings, devices, automation_rules, zones, locations RESTART IDENTITY CASCADE"
)


@dataclass(frozen=True)
class SeedData:
    location_id: UUID
    zone_ids: dict[str, UUID]
    moisture_device_id: UUID
    light_device_id: UUID
    unassigned_device_ids: tuple[UUID, ...]


def truncate_business_tables(session: Session) -> None:
    session.execute(text(TRUNCATE_BUSINESS_TABLES))
    session.commit()


def seed_database(session: Session) -> SeedData:
    locations = LocationRepository(session)
    saved = LocationConfigService(locations).build_and_save(
        BuildLocationConfigRequestDto(
            location_name="Lab Site Seed",
            zones=[
                ZoneRequestDto(
                    name="Bench 1",
                    moisture_threshold_low=0.2,
                    moisture_threshold_high=0.45,
                    schedule={"watering": "08:00"},
                ),
                ZoneRequestDto(
                    name="Bench 2",
                    moisture_threshold_low=0.3,
                    moisture_threshold_high=0.6,
                ),
            ],
        )
    )
    devices = DeviceFamilyService(DeviceRepository(session)).provision_family("simulation")
    moisture = next(device for device in devices if device.device_type == "moisture_sensor")
    light = next(device for device in devices if device.device_type == "light_sensor")
    bench_1 = next(zone for zone in saved.zones if zone.name == "Bench 1")
    assert moisture.id is not None
    ZoneAssignmentService(DeviceRepository(session), locations).assign(moisture.id, bench_1.id)
    unassigned = tuple(device.id for device in devices if device.id != moisture.id and device.id is not None)
    assert light.id is not None
    return SeedData(
        location_id=saved.location.id,
        zone_ids={zone.name: zone.id for zone in saved.zones},
        moisture_device_id=moisture.id,
        light_device_id=light.id,
        unassigned_device_ids=unassigned,
    )
