from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_returns_status_and_db() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in ("ok", "degraded")
    assert body["db"] in ("ok", "fail")


def test_root_points_at_scalar() -> None:
    body = client.get("/").json()
    assert body["api_reference"] == "/scalar"
    assert body["openapi"] == "/openapi.json"


def test_scalar_is_served_and_swagger_docs_are_disabled() -> None:
    scalar = client.get("/scalar")
    assert scalar.status_code == 200
    assert "text/html" in scalar.headers.get("content-type", "")
    assert client.get("/docs").status_code == 404
    assert "/health" in client.get("/openapi.json").json()["paths"]
