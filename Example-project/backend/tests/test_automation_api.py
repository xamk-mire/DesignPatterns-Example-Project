from datetime import datetime, timezone

from fastapi.testclient import TestClient

from domain.sensors.reading import Reading
from infrastructure.db import SessionLocal
from infrastructure.dev_seed import SeedData
from infrastructure.persistence.reading_repository import ReadingRepository
from main import app

client = TestClient(app)


def test_evaluate_changes_with_saved_strategy(seed: SeedData) -> None:
    session = SessionLocal()
    try:
        ReadingRepository(session).insert(
            Reading(
                device_id=seed.moisture_device_id,
                value=0.30,
                unit="vwc",
                source="simulation",
                recorded_at=datetime(2026, 10, 7, 8, 0, tzinfo=timezone.utc),
            )
        )
    finally:
        session.close()

    location = f"/api/locations/{seed.location_id}/automation"
    missing = client.post(f"{location}/evaluate")
    assert missing.status_code == 400, missing.text

    saved = client.put(location, json={"strategy_key": "conservative"})
    assert saved.status_code == 200, saved.text

    conservative = client.post(f"{location}/evaluate")
    assert conservative.status_code == 200, conservative.text
    assert conservative.json()["action"] == "wait"
    assert conservative.json()["strategy_key"] == "conservative"

    switched = client.put(location, json={"strategy_key": "aggressive"})
    assert switched.status_code == 200, switched.text

    aggressive = client.post(f"{location}/evaluate")
    assert aggressive.status_code == 200, aggressive.text
    body = aggressive.json()
    assert body["action"] == "irrigate"
    assert body["strategy_key"] == "aggressive"
    assert "Bench 1" in body["reason"]

    unknown = client.put(location, json={"strategy_key": "timed"})
    assert unknown.status_code == 400, unknown.text
