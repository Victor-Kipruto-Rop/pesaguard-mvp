from fastapi.testclient import TestClient

from app.main import create_app


def test_health_and_config() -> None:
    app = create_app()
    with TestClient(app) as client:
        health_response = client.get("/health")
        config_response = client.get("/config")
        assert health_response.status_code == 200
        assert config_response.status_code == 200
        assert health_response.json()["status"] == "ok"
        assert "profiles" in config_response.json()
