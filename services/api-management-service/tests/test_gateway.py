from fastapi.testclient import TestClient

from app.main import create_app


def test_liveness_and_readiness() -> None:
    app = create_app()
    with TestClient(app) as client:
        live = client.get("/api/v1/health/live")
        ready = client.get("/api/v1/health/ready")
        assert live.status_code == 200
        assert ready.status_code == 200
        assert live.json()["status"] == "alive"
        assert ready.json()["status"] == "ready"


def test_metrics_endpoint() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "gateway_requests_total" in response.text
