from dataclasses import replace
from datetime import datetime
from uuid import UUID

from domain.sensors.reading import Reading
from infrastructure.adapters.sensors.selector import AdapterSelectionError, sensor_port_for
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.reading_repository import ReadingRepository

from application.readings.dto import ReadingDto


class DeviceNotFound(Exception):
    """No device row for this id."""


class ReadingRejected(Exception):
    """Adapter or payload cannot produce a reading."""


class ReadingIngest:
    def __init__(self, devices: DeviceRepository, readings: ReadingRepository) -> None:
        self._devices = devices
        self._readings = readings

    def take_reading(self, device_id: UUID, recorded_at: datetime | None = None) -> ReadingDto:
        device = self._devices.get_device(device_id)
        if device is None:
            raise DeviceNotFound("Device not found")
        try:
            port = sensor_port_for(device)
            reading = port.read(device)
        except (AdapterSelectionError, ValueError) as exc:
            raise ReadingRejected(str(exc)) from exc
        if recorded_at is not None:
            reading = replace(reading, recorded_at=recorded_at)
        return _to_dto(self._readings.insert(reading))

    def record(self, device_id: UUID, reading: Reading) -> ReadingDto:
        if self._devices.get_device(device_id) is None:
            raise DeviceNotFound("Device not found")
        if reading.device_id != device_id:
            raise ReadingRejected("Reading device_id does not match")
        return _to_dto(self._readings.insert(reading))

    def list_readings(self, device_id: UUID, limit: int = 20) -> list[ReadingDto]:
        if self._devices.get_device(device_id) is None:
            raise DeviceNotFound("Device not found")
        return [_to_dto(reading) for reading in self._readings.list_for_device(device_id, limit)]


def _to_dto(reading: Reading) -> ReadingDto:
    return ReadingDto(
        device_id=reading.device_id,
        value=reading.value,
        unit=reading.unit,
        source=reading.source,
        recorded_at=reading.recorded_at,
    )
