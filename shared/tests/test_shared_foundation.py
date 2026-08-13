import json

import pytest

from shared.authentication.jwt_provider import JWTProvider, TokenExpiredError
from shared.clients.base_http_client import BaseHTTPClient
from shared.configuration.env_settings import EnvironmentSettings
from shared.exceptions.base_exception import BaseApplicationError
from shared.monitoring.health_check import HealthCheckRegistry
from shared.utilities.date_utils import as_utc, format_timestamp, minutes_ago
from shared.utilities.id_generator import generate_trace_id
from shared.utilities.string_utils import mask_sensitive, normalize_whitespace, slugify
from shared.validation.phone_validator import is_valid_phone, normalize_phone


def test_environment_settings_casts_values():
    env = {
        "APP_NAME": "pesaguard",
        "APP_PORT": "8080",
        "APP_DEBUG": "true",
        "APP_FEATURES": "payments,alerts,analytics",
    }
    settings = EnvironmentSettings(env=env)

    assert settings.get("APP_NAME") == "pesaguard"
    assert settings.get("APP_PORT", cast=int) == 8080
    assert settings.get("APP_DEBUG", cast=bool) is True
    assert settings.get("APP_FEATURES", cast=list) == ["payments", "alerts", "analytics"]


def test_jwt_provider_round_trip_and_expiry():
    provider = JWTProvider(secret_key="super-secret")
    token = provider.issue_token("user-123", expires_in=60, additional_claims={"scope": "admin"})

    payload = provider.verify_token(token)
    assert payload["sub"] == "user-123"
    assert payload["scope"] == "admin"

    expired_token = provider.issue_token("user-321", expires_in=-1)
    with pytest.raises(TokenExpiredError):
        provider.verify_token(expired_token)


def test_base_application_error_serializes_clearly():
    err = BaseApplicationError("validation failed", error_code="VALIDATION_FAILED", status_code=422, details={"field": "phone"})

    payload = err.to_dict()
    assert payload["error_code"] == "VALIDATION_FAILED"
    assert payload["status_code"] == 422
    assert payload["details"]["field"] == "phone"


def test_http_client_retries_and_returns_json(monkeypatch):
    calls = []

    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def read(self):
            return json.dumps(self._payload).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(request, timeout=None):
        calls.append((request.full_url, timeout))
        if len(calls) == 1:
            raise RuntimeError("temporary")
        return FakeResponse({"ok": True})

    monkeypatch.setattr("shared.clients.base_http_client.urlopen", fake_urlopen)
    client = BaseHTTPClient(retries=2, backoff_factor=0.0)

    response = client.get("https://example.test/health")
    assert response["ok"] is True
    assert len(calls) == 2


def test_health_registry_collects_results():
    registry = HealthCheckRegistry()
    registry.add_check("database", lambda: {"status": "ok"})
    registry.add_check("cache", lambda: (_ for _ in ()).throw(RuntimeError("down")))

    results = registry.run_all()
    assert results["database"].status == "ok"
    assert results["cache"].status == "unhealthy"


def test_date_and_string_helpers_are_stable():
    now = as_utc()
    assert format_timestamp(now) is not None
    assert minutes_ago(now, 5) <= now
    assert normalize_whitespace("  hello   world  ") == "hello world"
    assert slugify("Premium Modern API") == "premium-modern-api"
    assert mask_sensitive("sk_live_123456") == "sk_live_******"
    assert len(generate_trace_id()) >= 8
    assert is_valid_phone("+254712345678") is True
    assert normalize_phone("0712345678", country="KE") == "+254712345678"
