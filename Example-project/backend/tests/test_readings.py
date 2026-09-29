from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from application.readings.sampler import SimulationSampler
from application.readings.service import ReadingIngest
from infrastructure.db import SessionLocal
from infrastructure.dev_seed import SeedData
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.models import DeviceRow
from infrastructure.persistence.reading_repository import ReadingRepository
from main import app

client = TestClient(app)


def _count(device_id: str) -> int:
    listed = client.get(f"/api/sensors/{device_id}/readings?limit=50")
    assert listed.status_code == 200, listed.text
    return len(listed.json())


def test_sampler_respects_interval_and_tracking(seed: SeedData) -> None:
    session: Session = SessionLocal()
    try:
        devices = DeviceRepository(session)
        readings = ReadingRepository(session)
        sampler = SimulationSampler(devices, readings, ReadingIngest(devices, readings))
        devices.update_sampling(
            seed.light_device_id,
            sampling_interval_seconds=60,
            tracking_enabled=False,
        )
        now = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)
        sampler.run_once(now)
        assert _count(str(seed.moisture_device_id)) == 1
        assert _count(str(seed.light_device_id)) == 0

        sampler.run_once(now + timedelta(seconds=30))
        assert _count(str(seed.moisture_device_id)) == 1

        sampler.run_once(now + timedelta(seconds=300))
        assert _count(str(seed.moisture_device_id)) == 2

        devices.update_sampling(
            seed.moisture_device_id,
            sampling_interval_seconds=300,
            tracking_enabled=False,
        )
        sampler.run_once(now + timedelta(seconds=900))
        assert _count(str(seed.moisture_device_id)) == 2

        row = session.get(DeviceRow, seed.moisture_device_id)
        assert row is not None
        row.tracking_enabled = True
        row.default_config = {**dict(row.default_config or {}), "protocol": "mqtt"}
        session.commit()
        sampler.run_once(now + timedelta(seconds=1200))
        assert _count(str(seed.moisture_device_id)) == 2
    finally:
        session.close()


def test_read_inserts_sensor_reading(seed: SeedData) -> None:
    device_id = str(seed.moisture_device_id)
    first = client.post(f"/api/sensors/{device_id}/read")
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["device_id"] == device_id
    assert body["source"] == "simulation"
    assert body["unit"] == "vwc"
    assert 0.2 <= body["value"] <= 0.6

    second = client.post(f"/api/sensors/{device_id}/read")
    assert second.status_code == 200, second.text
    listed = client.get(f"/api/sensors/{device_id}/readings?limit=10")
    assert listed.status_code == 200, listed.text
    assert len(listed.json()) == 2
