from uuid import UUID

from fastapi.testclient import TestClient

from domain.actuators.state import ActuatorContext, IllegalTransitionError
from infrastructure.db import SessionLocal
from infrastructure.dev_seed import SeedData
from infrastructure.persistence.actuator_state_repository import ActuatorStateRepository
from main import app

client = TestClient(app)


def test_idle_to_running_allowed() -> None:
    context = ActuatorContext("idle", "water_pump")
    context.transition("running")
    assert context.state == "running"
    assert "stop_pump" in context.allowed_commands()


def test_running_to_maintenance_rejected() -> None:
    context = ActuatorContext("running", "water_pump")
    try:
        context.transition("maintenance")
    except IllegalTransitionError:
        assert context.state == "running"
        return
    raise AssertionError("running to maintenance should be rejected")


def test_illegal_transition_does_not_update_row(seed: SeedData) -> None:
    listed = client.get("/api/devices?role=actuator")
    assert listed.status_code == 200, listed.text
    pump = next(device for device in listed.json() if device["device_type"] == "water_pump")
    assert pump["state"] == "idle"
    assert str(pump["id"]) in {str(device_id) for device_id in seed.unassigned_device_ids}

    moved = client.post(f"/api/devices/{pump['id']}/transition", json={"target": "running"})
    assert moved.status_code == 200, moved.text
    assert moved.json()["state"] == "running"

    rejected = client.post(f"/api/devices/{pump['id']}/transition", json={"target": "maintenance"})
    assert rejected.status_code == 409, rejected.text

    session = SessionLocal()
    try:
        assert ActuatorStateRepository(session).get(UUID(pump["id"])) == "running"
    finally:
        session.close()
