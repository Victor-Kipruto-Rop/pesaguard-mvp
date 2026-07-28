from unittest.mock import AsyncMock
from app.core.security import issue_development_token


def test_health_returns_service_metadata(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "gateway"
    assert response.headers["x-request-id"]


def test_readiness_succeeds_without_optional_dependencies(client):
    assert client.get("/ready").json()["status"] == "ready"


def test_ready_probes_discovered_downstream_services(client, monkeypatch):
    monkeypatch.setenv("PESAGUARD_AUTH_SERVICE_URL", "https://auth.example.com")
    client.app.state.service_client.request = AsyncMock(return_value=type("Response", (), {"status_code": 200}))

    response = client.get("/ready")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "ready"
    assert payload["dependencies"]["service:auth"] == "ok"


def test_proxy_rejects_methods_not_supported_by_route_config(client, settings):
    token = issue_development_token("test", settings, ["auth:write"])
    response = client.put(
        "/api/v1/auth",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 405
    assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"

def test_metrics_exposes_prometheus_data(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "pesaguard_gateway_requests_total" in response.text
