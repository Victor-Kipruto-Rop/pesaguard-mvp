from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from app.core.security import issue_development_token
from app.config.settings import Settings
from app.main import create_app


def test_ready_reports_redis_unavailable_when_ping_fails(client):
    client.app.state.redis = AsyncMock()
    client.app.state.redis.ping.side_effect = Exception("redis down")

    response = client.get("/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["dependencies"]["redis"] == "unavailable"
    assert payload["dependencies"]["rate_limit"] == "local_fallback"


def test_ready_is_unhealthy_in_production_when_redis_unavailable_and_fail_open_disabled():
    settings = Settings(
        environment="production",
        allowed_hosts=["testserver"],
        docs_enabled=False,
        redis_url="redis://localhost:6379",
        rate_limit_fail_open=False,
        jwt_algorithm="RS256",
        jwt_jwks_url="https://issuer.example.com/.well-known/jwks.json",
        jwt_audience="pesaguard-api",
        jwt_issuer="https://issuer.example.com",
    )
    with TestClient(create_app(settings)) as production_client:
        production_client.app.state.redis = AsyncMock()
        production_client.app.state.redis.ping.side_effect = Exception("redis down")

        response = production_client.get("/ready")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "not_ready"
    assert payload["dependencies"]["redis"] == "unavailable"
    assert payload["dependencies"]["rate_limit"] == "unavailable"


def test_payment_idempotency_returns_unavailable_when_redis_lookup_fails(client, settings):
    client.app.state.redis = AsyncMock()
    client.app.state.redis.get.side_effect = Exception("redis unavailable")
    client.app.state.redis.set.side_effect = Exception("redis unavailable")

    token = issue_development_token("test", settings, ["payments:write"])
    response = client.post(
        "/api/v1/payments",
        json={"amount": "100"},
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "abc123"},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "IDEMPOTENCY_UNAVAILABLE"
