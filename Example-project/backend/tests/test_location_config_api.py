from uuid import uuid4

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_create_and_get_location_config() -> None:
    created = client.post(
        "/api/locations/config",
        json={
            "location_name": "Lab Site A",
            "zones": [
                {
                    "name": "Bench 1",
                    "moisture_threshold_low": 0.2,
                    "moisture_threshold_high": 0.45,
                    "schedule": {"watering": "08:00"},
                },
                {
                    "name": "Bench 2",
                    "moisture_threshold_low": 0.3,
                    "moisture_threshold_high": 0.6,
                },
            ],
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    location_id = body["location"]["id"]
    assert body["location"]["name"] == "Lab Site A"
    assert len(body["zones"]) == 2
    assert {zone["location_id"] for zone in body["zones"]} == {location_id}
    assert {zone["name"] for zone in body["zones"]} == {"Bench 1", "Bench 2"}

    fetched = client.get(f"/api/locations/{location_id}/config")
    assert fetched.status_code == 200, fetched.text
    again = fetched.json()
    assert again["location"]["id"] == location_id
    assert {zone["location_id"] for zone in again["zones"]} == {location_id}
    listed = client.get("/api/locations")
    assert listed.status_code == 200, listed.text
    assert "Lab Site Seed" in {item["name"] for item in listed.json()}


def test_create_config_rejects_invalid_thresholds() -> None:
    response = client.post(
        "/api/locations/config",
        json={
            "location_name": "Bad Site",
            "zones": [
                {
                    "name": "Bench",
                    "moisture_threshold_low": 0.8,
                    "moisture_threshold_high": 0.2,
                }
            ],
        },
    )
    assert response.status_code == 400
    assert "strictly less" in response.json()["detail"]


def test_get_missing_location_is_404() -> None:
    response = client.get(f"/api/locations/{uuid4()}/config")
    assert response.status_code == 404


def test_openapi_documents_location_config() -> None:
    schema = client.get("/openapi.json").json()
    assert "/api/locations/config" in schema["paths"]
    assert "/api/locations/{location_id}/config" in schema["paths"]
    assert "/api/locations/{location_id}/zones/{zone_id}/devices" in schema["paths"]
    assert "/api/devices/{device_id}/zone" in schema["paths"]
    assert "patch" in schema["paths"]["/api/devices/{device_id}/zone"]
    assert "LocationConfigDto" in schema["components"]["schemas"]
    zone_props = schema["components"]["schemas"]["ZoneDto"]["properties"]
    assert "location_id" in zone_props
