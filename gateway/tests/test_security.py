def test_protected_route_requires_credentials(client):
    response = client.get("/api/v1/payments")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_unknown_service_is_not_found_after_authentication(client, settings):
    from app.core.security import issue_development_token
    response = client.get("/api/v1/unknown", headers={"Authorization": f"Bearer {issue_development_token('test', settings)}"})
    assert response.status_code == 404


def test_authenticated_principal_requires_service_scope(client, settings):
    from app.core.security import issue_development_token
    response = client.get("/api/v1/payments", headers={"Authorization": f"Bearer {issue_development_token('test', settings)}"})
    assert response.status_code == 403


def test_cors_preflight_does_not_require_credentials(client):
    response = client.options("/api/v1/payments", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"})
    assert response.status_code == 200


def test_payment_creation_requires_idempotency_key(client, settings):
    from app.core.security import issue_development_token
    token = issue_development_token("test", settings, ["payments:write"])
    response = client.post("/api/v1/payments", json={"amount": "100"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400
