def test_protected_route_requires_credentials(client):
    response = client.get("/api/v1/payments")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_unknown_service_is_not_found_after_authentication(client, settings):
    from app.core.security import issue_development_token
    response = client.get("/api/v1/unknown", headers={"Authorization": f"Bearer {issue_development_token('test', settings)}"})
    assert response.status_code == 404
