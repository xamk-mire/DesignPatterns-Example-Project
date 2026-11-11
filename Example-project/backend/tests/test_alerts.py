from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from application.alerts.wiring import get_event_bus
from application.readings.service import ReadingIngest
from domain.events.bus import EventBus
from domain.events.events import ReadingCreated, ThresholdCrossed
from domain.sensors.reading import Reading
from infrastructure.db import SessionLocal
from infrastructure.dev_seed import SeedData
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.models import ActuatorStateRow
from infrastructure.persistence.reading_repository import ReadingRepository
from main import app

client = TestClient(app)
_SRC = Path(__file__).resolve().parents[1] / "src"


def _record(seed: SeedData, bus: EventBus | None, value: float) -> None:
    session = SessionLocal()
    try:
        recorded_at = datetime.now(timezone.utc)
        ReadingIngest(DeviceRepository(session), ReadingRepository(session), bus).record(
            seed.moisture_device_id,
            Reading(
                device_id=seed.moisture_device_id,
                value=value,
                unit="vwc",
                source="simulation",
                recorded_at=recorded_at,
            ),
        )
    finally:
        session.close()


def test_record_publishes_when_tracking_is_on(seed: SeedData) -> None:
    bus = EventBus()
    seen: list[ReadingCreated] = []
    bus.subscribe(ReadingCreated, seen.append)
    _record(seed, bus, 0.5)
    assert len(seen) == 1
    assert seen[0].device_id == seed.moisture_device_id
    assert seen[0].location_id == seed.location_id
    assert seen[0].zone_id == seed.zone_ids["Bench 1"]
    assert seen[0].value == 0.5


def test_record_skips_publish_when_tracking_is_off(seed: SeedData) -> None:
    updated = client.patch(
        f"/api/devices/{seed.moisture_device_id}/sampling",
        json={"sampling_interval_seconds": 300, "tracking_enabled": False},
    )
    assert updated.status_code == 200, updated.text
    bus = EventBus()
    seen: list[ReadingCreated] = []
    bus.subscribe(ReadingCreated, seen.append)
    _record(seed, bus, 0.1)
    assert seen == []
    listed = client.get(f"/api/sensors/{seed.moisture_device_id}/readings")
    assert listed.status_code == 200, listed.text
    assert len(listed.json()) == 1


def test_low_moisture_alert_is_filtered_by_zone(seed: SeedData) -> None:
    _record(seed, None, 0.10)
    get_event_bus().publish(
        ThresholdCrossed(
            device_id=seed.light_device_id,
            location_id=seed.location_id,
            zone_id=seed.zone_ids["Bench 2"],
        )
    )
    bench_1 = client.get("/api/alerts", params={"zone_id": str(seed.zone_ids["Bench 1"])})
    assert bench_1.status_code == 200, bench_1.text
    rows = bench_1.json()
    assert len(rows) == 1
    assert rows[0]["event_type"] == "threshold.crossed"
    assert rows[0]["location_id"] == str(seed.location_id)
    assert rows[0]["zone_id"] == str(seed.zone_ids["Bench 1"])
    assert rows[0]["message"] == "Moisture below zone low"

    bench_2 = client.get("/api/alerts", params={"zone_id": str(seed.zone_ids["Bench 2"])})
    assert bench_2.status_code == 200, bench_2.text
    other = bench_2.json()
    assert other
    assert all(row["zone_id"] == str(seed.zone_ids["Bench 2"]) for row in other)
    assert all(row["zone_id"] != str(seed.zone_ids["Bench 1"]) for row in other)


def test_failed_command_alert_leaves_ids_null(seed: SeedData) -> None:
    listed = client.get("/api/devices?role=actuator")
    pump = next(device for device in listed.json() if device["device_type"] == "water_pump")
    moved = client.post(f"/api/devices/{pump['id']}/transition", json={"target": "running"})
    assert moved.status_code == 200, moved.text
    session = SessionLocal()
    try:
        row = session.get(ActuatorStateRow, UUID(pump["id"]))
        assert row is not None
        row.updated_at = datetime.now(timezone.utc) - timedelta(minutes=31)
        session.commit()
    finally:
        session.close()
    failed = client.post("/api/commands", json={"command_type": "stop_pump", "device_id": pump["id"]})
    assert failed.status_code == 200, failed.text
    assert failed.json()["status"] == "failed"
    alerts = client.get("/api/alerts")
    match = next(item for item in alerts.json() if item["event_type"] == "command.failed")
    assert match["device_id"] == pump["id"]
    assert match["location_id"] is None
    assert match["zone_id"] is None
    assert match["message"] == "Max run time exceeded"


def test_error_transition_inserts_state_alert(seed: SeedData) -> None:
    listed = client.get("/api/devices?role=actuator")
    pump = next(device for device in listed.json() if device["device_type"] == "water_pump")
    moved = client.post(f"/api/devices/{pump['id']}/transition", json={"target": "error"})
    assert moved.status_code == 200, moved.text
    alerts = client.get("/api/alerts")
    match = next(item for item in alerts.json() if item["event_type"] == "state.changed")
    assert match["severity"] == "critical"
    assert match["message"] == "Actuator entered error"
    assert match["device_id"] == pump["id"]


def test_publishers_do_not_import_alert_repository() -> None:
    paths = [
        _SRC / "application" / "readings" / "service.py",
        _SRC / "application" / "commands" / "service.py",
        _SRC / "application" / "devices" / "transition_service.py",
    ]
    for path in paths:
        assert "AlertRepository" not in path.read_text(encoding="utf-8")
