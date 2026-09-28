from uuid import UUID

from domain.devices.entity import Device
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.location_repository import LocationRepository


class AssignmentNotFound(Exception):
    """Device or zone is missing, or the zone is not in the requested location."""


class ZoneAssignmentService:
    def __init__(self, devices: DeviceRepository, locations: LocationRepository) -> None:
        self._devices = devices
        self._locations = locations

    def assign(self, device_id: UUID, zone_id: UUID | None) -> None:
        if self._devices.get_device(device_id) is None:
            raise AssignmentNotFound("Device not found")
        location_id: UUID | None = None
        if zone_id is not None:
            location_id = self._locations.get_zone_location_id(zone_id)
            if location_id is None:
                raise AssignmentNotFound("Zone not found")
        self._devices.set_zone(device_id, zone_id=zone_id, location_id=location_id)

    def list_devices(self, location_id: UUID, zone_id: UUID) -> list[Device]:
        zone_location_id = self._locations.get_zone_location_id(zone_id)
        if zone_location_id is None or zone_location_id != location_id:
            raise AssignmentNotFound("Zone not found")
        return self._devices.list_devices(zone_id=zone_id)
