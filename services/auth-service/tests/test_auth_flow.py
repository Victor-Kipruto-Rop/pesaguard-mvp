from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.main import create_app


@pytest.fixture()
def client() -> TestClient:
    db_path = Path("/tmp/pesaguard-auth-test.db")
    if db_path.exists():
        db_path.unlink()
    settings = Settings(
        database_url=f"sqlite:///{db_path}",
        secret_key="test-secret-key",
        jwt_algorithm="HS256",
        access_token_ttl_minutes=15,
        refresh_token_ttl_days=7,
        environment="test",
    )
    app = create_app(settings=settings)
    with TestClient(app) as test_client:
        yield test_client


def test_user_registration_login_and_refresh(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "demo@example.com",
            "password": "StrongPassword123!",
            "full_name": "Demo User",
            "username": "demouser",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["email"] == "demo@example.com"

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "demo@example.com",
            "password": "StrongPassword123!",
        },
    )
    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert "access_token" in login_payload
    assert "refresh_token" in login_payload

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_payload["refresh_token"]},
    )
    assert refresh_response.status_code == 200
    refresh_payload = refresh_response.json()
    assert "access_token" in refresh_payload


def test_password_reset_request(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "reset@example.com",
            "password": "StrongPassword123!",
            "full_name": "Reset User",
            "username": "resetuser",
        },
    )

    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "reset@example.com"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Password reset instructions sent"
