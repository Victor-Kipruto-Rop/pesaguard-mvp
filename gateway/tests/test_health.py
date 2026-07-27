def test_health_returns_service_metadata(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "gateway"
    assert response.headers["x-request-id"]


def test_readiness_succeeds_without_optional_dependencies(client):
    assert client.get("/ready").json()["status"] == "ready"


def test_metrics_exposes_prometheus_data(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "pesaguard_gateway_requests_total" in response.text
