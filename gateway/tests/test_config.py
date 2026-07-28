import os
from pathlib import Path
import tempfile

import pytest
from pydantic import ValidationError

from app.config.routes import RouteConfig
from app.config.settings import Settings


def test_production_requires_strong_secret():
    with pytest.raises(ValidationError):
        Settings(environment="production", jwt_secret="short")


def test_production_requires_redis_and_disabled_docs():
    with pytest.raises(ValidationError):
        Settings(environment="production", jwt_secret="a" * 32, docs_enabled=False)


def test_route_config_loads_default_and_provides_service_mapping():
    settings = Settings(environment="test", allowed_hosts=["testserver"])

    assert settings.route_config is not None
    assert "auth" in settings.route_config.service_names()
    assert settings.service_env_var("auth") == "PESAGUARD_AUTH_SERVICE_URL"


def test_route_config_resolves_service_url_from_environment(tmp_path, monkeypatch):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  payments:\n    env_var: PESAGUARD_PAYMENTS_SERVICE_URL\n    health_path: /health\n    health_method: GET\n    methods: [GET, POST]\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PESAGUARD_PAYMENTS_SERVICE_URL", "https://payments.example.com")

    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path)

    assert settings.route_config is not None
    assert settings.service_env_var("payments") == "PESAGUARD_PAYMENTS_SERVICE_URL"
    assert settings.service_health_path("payments") == "/health"
    assert settings.service_health_method("payments") == "GET"
    assert settings.supported_methods_for("payments") == ("GET", "POST")
    assert settings.upstream_for("payments") == "https://payments.example.com"


def test_route_config_rejects_invalid_service_names(tmp_path):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  Invalid-Name: PESAGUARD_BAD_SERVICE_URL\n",
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        RouteConfig.load(config_path)


def test_route_config_rejects_invalid_env_var_names(tmp_path):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  payments: bad_env_var\n",
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        RouteConfig.load(config_path)
