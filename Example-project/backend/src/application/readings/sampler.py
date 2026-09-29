from datetime import datetime

from application.readings.service import ReadingIngest
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.reading_repository import ReadingRepository


class SimulationSampler:
    def __init__(
        self,
        devices: DeviceRepository,
        readings: ReadingRepository,
        ingest: ReadingIngest,
    ) -> None:
        self._devices = devices
        self._readings = readings
        self._ingest = ingest

    def run_once(self, now: datetime) -> None:
        for device in self._devices.list_tracked_simulation_sensors():
            if device.id is None:
                continue
            last = self._readings.latest_recorded_at(device.id)
            if last is not None:
                elapsed = (now - last).total_seconds()
                if elapsed < device.sampling_interval_seconds:
                    continue
            self._ingest.take_reading(device.id, recorded_at=now)
