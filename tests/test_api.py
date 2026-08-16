from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint_without_database_startup() -> None:
    with TestClient(create_app(enable_runtime=False)) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_is_served() -> None:
    with TestClient(create_app(enable_runtime=False)) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert "Collection intelligence" in response.text
