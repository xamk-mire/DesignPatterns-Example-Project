from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from infrastructure.db import SessionLocal
from infrastructure.dev_seed import SeedData
from infrastructure.persistence.models import DeviceRow
from main import app

client = TestClient(app)


def _other_location() -> str:
    created = client.post(
        "/api/locations/config",
        json={
            "location_name": "Other Site",
            "zones": [
                {
                    "name": "Bench 9",
                    "moisture_threshold_low": 0.2,
                    "moisture_threshold_high": 0.45,
                }
            ],
        },
    )
    assert created.status_code == 201, created.text
    return created.json()["location"]["id"]


def _zone_device_ids(location_id: str, zone_id: str) -> set[str]:
    listed = client.get(f"/api/locations/{location_id}/zones/{zone_id}/devices")
    assert listed.status_code == 200, listed.text
    return {device["id"] for device in listed.json()}


def _device_row(device_id: str) -> DeviceRow:
    session: Session = SessionLocal()
    try:
        row = session.get(DeviceRow, UUID(device_id))
        assert row is not None
        session.expunge(row)
        return row
    finally:
        session.close()


def test_assign_devices_to_zone(seed: SeedData) -> None:
    location_id = str(seed.location_id)
    zones = {name: str(zone_id) for name, zone_id in seed.zone_ids.items()}
    other_location_id = _other_location()
    first, second = (str(device_id) for device_id in seed.unassigned_device_ids[:2])
    moisture_id = str(seed.moisture_device_id)

    missing_device = client.patch(
        f"/api/devices/{uuid4()}/zone",
        json={"zone_id": zones["Bench 2"]},
    )
    assert missing_device.status_code == 404

    missing_zone = client.patch(
        f"/api/devices/{first}/zone",
        json={"zone_id": str(uuid4())},
    )
    assert missing_zone.status_code == 404

    wrong_location = client.get(
        f"/api/locations/{other_location_id}/zones/{zones['Bench 2']}/devices"
    )
    assert wrong_location.status_code == 404

    for device_id in (first, second):
        assigned = client.patch(
            f"/api/devices/{device_id}/zone",
            json={"zone_id": zones["Bench 2"]},
        )
        assert assigned.status_code == 204, assigned.text

    assert _zone_device_ids(location_id, zones["Bench 2"]) == {first, second}
    assert _zone_device_ids(location_id, zones["Bench 1"]) == {moisture_id}

    moved = client.patch(
        f"/api/devices/{first}/zone",
        json={"zone_id": zones["Bench 1"]},
    )
    assert moved.status_code == 204, moved.text
    assert _zone_device_ids(location_id, zones["Bench 2"]) == {second}
    assert _zone_device_ids(location_id, zones["Bench 1"]) == {moisture_id, first}

    row = _device_row(second)
    assert str(row.zone_id) == zones["Bench 2"]
    assert str(row.location_id) == location_id


def test_unassign_clears_zone_and_location(seed: SeedData) -> None:
    location_id = str(seed.location_id)
    zones = {name: str(zone_id) for name, zone_id in seed.zone_ids.items()}
    device_id = str(seed.moisture_device_id)

    cleared = client.patch(f"/api/devices/{device_id}/zone", json={"zone_id": None})
    assert cleared.status_code == 204, cleared.text

    row = _device_row(device_id)
    assert row.zone_id is None
    assert row.location_id is None
    assert device_id not in _zone_device_ids(location_id, zones["Bench 1"])
    assert device_id not in _zone_device_ids(location_id, zones["Bench 2"])
