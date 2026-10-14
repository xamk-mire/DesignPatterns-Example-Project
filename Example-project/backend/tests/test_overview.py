from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from domain.sensors.reading import Reading
from infrastructure.db import SessionLocal
from infrastructure.dev_seed import SeedData
from infrastructure.persistence.reading_repository import ReadingRepository
from main import app

client = TestClient(app)


def test_overview_returns_strategy_and_readings(seed: SeedData) -> None:
    session = SessionLocal()
    try:
        ReadingRepository(session).insert(
            Reading(
                device_id=seed.moisture_device_id,
                value=0.30,
                unit="vwc",
                source="simulation",
                recorded_at=datetime(2026, 10, 13, 9, 0, tzinfo=timezone.utc),
            )
        )
    finally:
        session.close()

    missing = client.get(f"/api/locations/{uuid4()}/overview")
    assert missing.status_code == 404, missing.text

    path = f"/api/locations/{seed.location_id}/overview"
    before = client.get(path)
    assert before.status_code == 200, before.text
    body = before.json()
    assert body["location"]["name"] == "Lab Site Seed"
    assert body["strategy_key"] is None
    assert body["last_recommendation"] is None
    assert body["device_counts"] == {"sensor": 1, "actuator": 0}

    zones = {zone["name"]: zone for zone in body["zones"]}
    bench_1 = zones["Bench 1"]
    device_ids = [device["id"] for device in bench_1["devices"]]
    assert str(seed.moisture_device_id) in device_ids
    assert str(seed.light_device_id) not in device_ids
    for zone in body["zones"]:
        listed = {device["id"] for device in zone["devices"]}
        assert str(seed.light_device_id) not in listed
        for unassigned in seed.unassigned_device_ids:
            assert str(unassigned) not in listed
    readings = bench_1["latest_readings"]
    assert len(readings) == 1
    assert readings[0]["device_id"] == str(seed.moisture_device_id)
    assert readings[0]["value"] == 0.3
    assert readings[0]["unit"] == "vwc"
    assert readings[0]["tracking_enabled"] is True
    assert readings[0]["sampling_interval_seconds"] == 300
    assert zones["Bench 2"]["devices"] == []
    assert zones["Bench 2"]["latest_readings"] == []

    saved = client.put(
        f"/api/locations/{seed.location_id}/automation",
        json={"strategy_key": "conservative"},
    )
    assert saved.status_code == 200, saved.text
    evaluated = client.post(f"/api/locations/{seed.location_id}/automation/evaluate")
    assert evaluated.status_code == 200, evaluated.text

    after = client.get(path)
    assert after.status_code == 200, after.text
    overview = after.json()
    assert overview["strategy_key"] == "conservative"
    assert overview["last_recommendation"]["action"] == evaluated.json()["action"]
    assert overview["last_recommendation"]["reason"] == evaluated.json()["reason"]
