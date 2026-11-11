from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi.testclient import TestClient

from infrastructure.db import SessionLocal
from infrastructure.persistence.models import ActuatorStateRow
from main import app

client = TestClient(app)


def _pump() -> dict:
    listed = client.get("/api/devices?role=actuator")
    assert listed.status_code == 200, listed.text
    return next(device for device in listed.json() if device["device_type"] == "water_pump")


def test_illegal_command_rejected_logged() -> None:
    pump = _pump()
    rejected = client.post(
        "/api/commands",
        json={"command_type": "stop_pump", "device_id": pump["id"]},
    )
    assert rejected.status_code == 409, rejected.text
    assert rejected.json()["status"] == "rejected"

    history = client.get("/api/commands")
    assert history.status_code == 200, history.text
    row = next(item for item in history.json() if item["device_id"] == pump["id"])
    assert row["status"] == "rejected"
    assert row["command_type"] == "stop_pump"

    listed = client.get("/api/devices?role=actuator")
    again = next(device for device in listed.json() if device["id"] == pump["id"])
    assert again["state"] == "idle"


def test_start_pump_transitions_to_running() -> None:
    pump = _pump()
    started = client.post(
        "/api/commands",
        json={"command_type": "start_pump", "device_id": pump["id"]},
    )
    assert started.status_code == 200, started.text
    assert started.json()["status"] == "success"

    listed = client.get("/api/devices?role=actuator")
    running = next(device for device in listed.json() if device["id"] == pump["id"])
    assert running["state"] == "running"
    assert "stop_pump" in running["allowed_commands"]

    stopped = client.post(
        "/api/commands",
        json={"command_type": "stop_pump", "device_id": pump["id"]},
    )
    assert stopped.status_code == 200, stopped.text
    assert stopped.json()["status"] == "success"


def test_stop_pump_fails_when_max_run_time_exceeded() -> None:
    pump = _pump()
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

    failed = client.post(
        "/api/commands",
        json={"command_type": "stop_pump", "device_id": pump["id"]},
    )
    assert failed.status_code == 200, failed.text
    assert failed.json()["status"] == "failed"

    listed = client.get("/api/devices?role=actuator")
    still = next(device for device in listed.json() if device["id"] == pump["id"])
    assert still["state"] == "running"

    executions = client.get("/api/actuators/executions")
    match = next(item for item in executions.json() if item["device_id"] == pump["id"])
    assert match["success"] is False
