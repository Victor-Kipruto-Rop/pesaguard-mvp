from unittest.mock import AsyncMock

from app.core.security import issue_development_token


def test_ready_reports_redis_unavailable_when_ping_fails(client):
    client.app.state.redis = AsyncMock()
    client.app.state.redis.ping.side_effect = Exception("redis down")

    response = client.get("/ready")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "not_ready"
    assert payload["dependencies"]["redis"] == "unavailable"


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
