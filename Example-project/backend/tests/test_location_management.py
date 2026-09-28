from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from infrastructure.db import SessionLocal
from infrastructure.dev_seed import SeedData
from infrastructure.persistence.models import DeviceRow
from main import app

client = TestClient(app)


def _create_location(name: str, zones: list[dict] | None = None) -> dict:
    created = client.post(
        "/api/locations/config",
        json={
            "location_name": name,
            "zones": zones
            or [
                {
                    "name": "Bench 1",
                    "moisture_threshold_low": 0.2,
                    "moisture_threshold_high": 0.45,
                }
            ],
        },
    )
    assert created.status_code == 201, created.text
    return created.json()


def _device_row(device_id: str) -> DeviceRow:
    session: Session = SessionLocal()
    try:
        row = session.get(DeviceRow, UUID(device_id))
        assert row is not None
        session.expunge(row)
        return row
    finally:
        session.close()


def _lab_config(seed: SeedData) -> dict:
    fetched = client.get(f"/api/locations/{seed.location_id}/config")
    assert fetched.status_code == 200, fetched.text
    return fetched.json()


def test_list_locations(seed: SeedData) -> None:
    extra = _create_location("List Site B")
    listed = client.get("/api/locations")
    assert listed.status_code == 200, listed.text
    ids = {item["id"] for item in listed.json()}
    assert str(seed.location_id) in ids
    assert extra["location"]["id"] in ids
    assert all("name" in item for item in listed.json())


def test_delete_location_clears_assignments(seed: SeedData) -> None:
    removed = _create_location(
        "Remove Site",
        [
            {"name": "Bench 1", "moisture_threshold_low": 0.2, "moisture_threshold_high": 0.4},
            {"name": "Bench 2", "moisture_threshold_low": 0.3, "moisture_threshold_high": 0.6},
        ],
    )
    location_id = removed["location"]["id"]
    zone_id = removed["zones"][0]["id"]
    device_id = str(seed.light_device_id)
    assigned = client.patch(f"/api/devices/{device_id}/zone", json={"zone_id": zone_id})
    assert assigned.status_code == 204, assigned.text

    deleted = client.delete(f"/api/locations/{location_id}")
    assert deleted.status_code == 204, deleted.text
    assert client.get(f"/api/locations/{location_id}/config").status_code == 404
    assert client.get(f"/api/locations/{seed.location_id}/config").status_code == 200

    row = _device_row(device_id)
    assert row.zone_id is None
    assert row.location_id is None
    still_listed = client.get("/api/sensors")
    assert device_id in {item["id"] for item in still_listed.json()}


def test_add_zone_to_location(seed: SeedData) -> None:
    location_id = str(seed.location_id)
    added = client.post(
        f"/api/locations/{location_id}/zones",
        json={"name": "Bench 3", "moisture_threshold_low": 0.3, "moisture_threshold_high": 0.7},
    )
    assert added.status_code == 201, added.text
    body = added.json()
    assert body["location_id"] == location_id
    assert body["name"] == "Bench 3"
    config = client.get(f"/api/locations/{location_id}/config").json()
    assert {zone["name"] for zone in config["zones"]} == {"Bench 1", "Bench 2", "Bench 3"}


def test_update_zone_rejects_invalid_thresholds(seed: SeedData) -> None:
    location_id = str(seed.location_id)
    zone = next(item for item in _lab_config(seed)["zones"] if item["name"] == "Bench 1")
    updated = client.patch(
        f"/api/locations/{location_id}/zones/{zone['id']}",
        json={
            "name": zone["name"],
            "moisture_threshold_low": 0.8,
            "moisture_threshold_high": 0.2,
            "schedule": zone["schedule"],
        },
    )
    assert updated.status_code == 400
    stored = next(item for item in _lab_config(seed)["zones"] if item["name"] == "Bench 1")
    assert stored["moisture_threshold_low"] == zone["moisture_threshold_low"]
    assert stored["moisture_threshold_high"] == zone["moisture_threshold_high"]


def test_delete_zone_clears_assignments(seed: SeedData) -> None:
    location_id = str(seed.location_id)
    zone_id = str(seed.zone_ids["Bench 1"])
    device_id = str(seed.moisture_device_id)

    deleted = client.delete(f"/api/locations/{location_id}/zones/{zone_id}")
    assert deleted.status_code == 204, deleted.text
    config = client.get(f"/api/locations/{location_id}/config").json()
    assert [zone["name"] for zone in config["zones"]] == ["Bench 2"]
    row = _device_row(device_id)
    assert row.zone_id is None
    assert row.location_id is None


def test_duplicate_zone_name_in_one_location_is_rejected() -> None:
    before = {item["id"] for item in client.get("/api/locations").json()}
    rejected = client.post(
        "/api/locations/config",
        json={
            "location_name": "Duplicate Name Site",
            "zones": [
                {"name": "Bench 1", "moisture_threshold_low": 0.2, "moisture_threshold_high": 0.4},
                {"name": "Bench 1", "moisture_threshold_low": 0.3, "moisture_threshold_high": 0.6},
            ],
        },
    )
    assert rejected.status_code == 400
    after = {item["id"] for item in client.get("/api/locations").json()}
    assert after == before


def test_add_or_rename_zone_rejects_duplicate_name(seed: SeedData) -> None:
    location_id = str(seed.location_id)
    bench_2 = next(zone for zone in _lab_config(seed)["zones"] if zone["name"] == "Bench 2")
    added = client.post(
        f"/api/locations/{location_id}/zones",
        json={"name": "Bench 1", "moisture_threshold_low": 0.1, "moisture_threshold_high": 0.3},
    )
    assert added.status_code == 400
    renamed = client.patch(
        f"/api/locations/{location_id}/zones/{bench_2['id']}",
        json={
            "name": "Bench 1",
            "moisture_threshold_low": 0.3,
            "moisture_threshold_high": 0.6,
            "schedule": bench_2["schedule"],
        },
    )
    assert renamed.status_code == 400
    kept = client.patch(
        f"/api/locations/{location_id}/zones/{bench_2['id']}",
        json={
            "name": "Bench 2",
            "moisture_threshold_low": 0.3,
            "moisture_threshold_high": 0.6,
            "schedule": bench_2["schedule"],
        },
    )
    assert kept.status_code == 200, kept.text
    names = {zone["name"] for zone in client.get(f"/api/locations/{location_id}/config").json()["zones"]}
    assert names == {"Bench 1", "Bench 2"}


def test_same_zone_name_in_two_locations_assigns_only_the_chosen_zone(seed: SeedData) -> None:
    second = _create_location("Shared Name B")
    first_zone = str(seed.zone_ids["Bench 1"])
    second_zone = second["zones"][0]["id"]
    assert second["zones"][0]["name"] == "Bench 1"
    device_id = str(seed.moisture_device_id)

    first_devices = client.get(f"/api/locations/{seed.location_id}/zones/{first_zone}/devices")
    second_devices = client.get(f"/api/locations/{second['location']['id']}/zones/{second_zone}/devices")
    assert device_id in {item["id"] for item in first_devices.json()}
    assert device_id not in {item["id"] for item in second_devices.json()}
    row = _device_row(device_id)
    assert str(row.zone_id) == first_zone
    assert str(row.location_id) == str(seed.location_id)


def test_delete_last_zone_is_rejected(seed: SeedData) -> None:
    location_id = str(seed.location_id)
    removed = client.delete(f"/api/locations/{location_id}/zones/{seed.zone_ids['Bench 2']}")
    assert removed.status_code == 204, removed.text
    zone_id = str(seed.zone_ids["Bench 1"])
    rejected = client.delete(f"/api/locations/{location_id}/zones/{zone_id}")
    assert rejected.status_code == 400
    config = client.get(f"/api/locations/{location_id}/config").json()
    assert len(config["zones"]) == 1
    assert config["zones"][0]["id"] == zone_id
