import os
from pathlib import Path
import tempfile

import pytest
from fastapi import APIRouter
from pydantic import ValidationError

from app.config.routes import RouteConfig
from app.config.settings import Settings
from app.routes.proxy import register_proxy_routes


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


def test_route_config_selects_weighted_upstreams(tmp_path, monkeypatch):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  payments:\n    upstreams:\n      - env_var: PESAGUARD_PAYMENTS_SERVICE_URL_A\n        weight: 1\n      - env_var: PESAGUARD_PAYMENTS_SERVICE_URL_B\n        weight: 3\n    health_path: /health\n    health_method: GET\n    methods: [GET, POST]\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PESAGUARD_PAYMENTS_SERVICE_URL_A", "https://payments-a.example.com")
    monkeypatch.setenv("PESAGUARD_PAYMENTS_SERVICE_URL_B", "https://payments-b.example.com")

    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path)
    selected = {settings.route_config.select_upstream_for("payments") for _ in range(50)}

    assert "https://payments-a.example.com" in selected
    assert "https://payments-b.example.com" in selected


def test_route_config_applies_service_ordering_by_group_and_priority(tmp_path):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  low_priority:\n    env_var: PESAGUARD_LOW_SERVICE_URL\n    group: core\n    priority: 0\n  high_priority:\n    env_var: PESAGUARD_HIGH_SERVICE_URL\n    group: core\n    priority: 10\n  external:\n    env_var: PESAGUARD_EXTERNAL_SERVICE_URL\n    group: external\n    priority: 5\n",
        encoding="utf-8",
    )
    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path)

    assert settings.route_config.service_names() == ("high_priority", "low_priority", "external")


def test_route_config_uses_fallback_service_when_primary_missing(tmp_path, monkeypatch):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  primary:\n    env_var: PESAGUARD_PRIMARY_SERVICE_URL\n  fallback:\n    env_var: PESAGUARD_FALLBACK_SERVICE_URL\n    fallback: true\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PESAGUARD_FALLBACK_SERVICE_URL", "https://fallback.example.com")

    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path)
    assert settings.upstream_for("primary") == "https://fallback.example.com"


def test_route_config_supports_custom_gateway_paths(tmp_path):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  auth:\n    env_var: PESAGUARD_AUTH_SERVICE_URL\n    gateway_path: /identity/auth\n    path_prefix: /internal/{service}\n    health_path: /health\n    health_method: GET\n    methods: [GET, POST]\n",
        encoding="utf-8",
    )

    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path)

    assert settings.gateway_path_for("auth") == "/identity/auth"
    assert settings.path_prefix_for("auth") == "/internal/{service}"


def test_proxy_routes_register_from_configured_gateway_paths(tmp_path):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  auth:\n    env_var: PESAGUARD_AUTH_SERVICE_URL\n    gateway_path: /identity/auth\n    path_prefix: /internal/{service}\n    health_path: /health\n    health_method: GET\n    methods: [GET, POST]\n",
        encoding="utf-8",
    )

    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path)
    router = APIRouter(prefix="/api/v1")
    register_proxy_routes(router, settings)

    route_paths = {route.path for route in router.routes}
    assert "/api/v1/identity/auth" in route_paths
    assert "/api/v1/identity/auth/{path:path}" in route_paths


def test_route_config_supports_websocket_flag(tmp_path):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  chat:\n    env_var: PESAGUARD_CHAT_SERVICE_URL\n    gateway_path: /chat\n    websocket: true\n",
        encoding="utf-8",
    )

    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path)
    router = APIRouter(prefix="/api/v1")
    register_proxy_routes(router, settings)

    route_paths = {route.path for route in router.routes}
    assert "/api/v1/chat" in route_paths
    # websocket routes are registered with same base path
    assert "/api/v1/chat" in route_paths


def test_route_config_supports_websocket_flag(tmp_path):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  chat:\n    env_var: PESAGUARD_CHAT_SERVICE_URL\n    websocket: true\n    methods: [GET]\n",
        encoding="utf-8",
    )

    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path)

    assert settings.supports_websocket_for("chat") is True


def test_proxy_routes_register_websocket_routes_for_websocket_enabled_services(tmp_path):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  chat:\n    env_var: PESAGUARD_CHAT_SERVICE_URL\n    websocket: true\n    methods: [GET]\n",
        encoding="utf-8",
    )

    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path)
    router = APIRouter(prefix="/api/v1")
    register_proxy_routes(router, settings)

    route_paths = {route.path for route in router.routes}
    assert "/api/v1/chat" in route_paths
    assert "/api/v1/chat/{path:path}" in route_paths
    assert any(route.__class__.__name__ == "APIWebSocketRoute" and route.path == "/api/v1/chat" for route in router.routes)
    assert any(route.__class__.__name__ == "APIWebSocketRoute" and route.path == "/api/v1/chat/{path:path}" for route in router.routes)


def test_proxy_routes_do_not_register_websocket_routes_for_non_websocket_services(tmp_path):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  chat:\n    env_var: PESAGUARD_CHAT_SERVICE_URL\n    methods: [GET]\n",
        encoding="utf-8",
    )

    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path)
    router = APIRouter(prefix="/api/v1")
    register_proxy_routes(router, settings)

    assert not any(route.__class__.__name__ == "APIWebSocketRoute" for route in router.routes)
