from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from application.actuators.compose import simulation_adapter
from domain.actuators.ports import ActuatorPort
from infrastructure.adapters.actuators.max_runtime_decorator import (
    MaxRunTimeActuatorDecorator,
    MaxRunTimeExceeded,
)
from infrastructure.db import SessionLocal
from infrastructure.persistence.models import ActuatorStateRow
from main import app

client = TestClient(app)


class _Inner(ActuatorPort):
    def __init__(self) -> None:
        self.applied: list[UUID] = []

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        self.applied.append(device_id)


class _RunningTooLong:
    def snapshot(self, device_id: UUID) -> tuple[str, datetime]:
        return "running", datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_max_runtime_does_not_call_inner() -> None:
    inner = _Inner()
    decorator = MaxRunTimeActuatorDecorator(
        inner,
        _RunningTooLong(),  # type: ignore[arg-type]
        now=lambda: datetime(2026, 1, 1, 0, 30, tzinfo=timezone.utc),
    )
    try:
        decorator.apply(uuid4(), "stop_pump", {})
    except MaxRunTimeExceeded:
        assert inner.applied == []
        return
    raise AssertionError("max run time should block the inner adapter")


def test_failed_policy_writes_execution_row() -> None:
    listed = client.get("/api/devices?role=actuator")
    assert listed.status_code == 200, listed.text
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

    simulation_adapter.applied.clear()
    blocked = client.post(
        f"/api/actuators/{pump['id']}/apply",
        json={"command": "stop_pump"},
    )
    assert blocked.status_code == 409, blocked.text
    assert simulation_adapter.applied == []

    executions = client.get("/api/actuators/executions")
    assert executions.status_code == 200, executions.text
    match = next(item for item in executions.json() if item["device_id"] == pump["id"])
    assert match["success"] is False
    assert match["policy_applied"] == ["maxRunTime", "logging"]
    assert match["message"] == "Max run time exceeded"
