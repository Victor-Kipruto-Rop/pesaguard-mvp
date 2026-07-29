import pytest

from app.config.settings import Settings
from app.constants import DEFAULT_API_PREFIX
from app.services import GatewayServiceManager, RouteManager
from app.utils import is_health_probe, normalize_headers, strip_sensitive_headers


def test_route_manager_resolves_gateway_route_from_settings(tmp_path, monkeypatch):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  payments:\n    env_var: PESAGUARD_PAYMENTS_SERVICE_URL\n    gateway_path: /payments\n"
    )
    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path)
    route_manager = RouteManager(settings)

    assert route_manager.service_exists("payments")
    assert route_manager.gateway_route("payments") == "/payments"
    assert route_manager.resolve_service_url("payments") is None
    assert route_manager.service_names() == ("payments",)


def test_route_manager_build_upstream_url_with_default_prefix(monkeypatch, tmp_path):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  payments:\n    env_var: PESAGUARD_PAYMENTS_SERVICE_URL\n    path_prefix: /internal/{service}\n"
    )
    monkeypatch.setenv("PESAGUARD_PAYMENTS_SERVICE_URL", "https://payments.local")
    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path)
    route_manager = RouteManager(settings)

    assert route_manager.build_upstream_url("payments", "charge") == "https://payments.local/internal/payments/charge"


def test_header_helpers_normalize_and_strip():
    headers = {"Authorization": "Bearer tok", "X-Custom": "value", "": "ignored"}
    normalized = normalize_headers(headers)
    assert normalized == {"authorization": "Bearer tok", "x-custom": "value"}
    stripped = strip_sensitive_headers(normalized, ["authorization"])
    assert stripped == {"x-custom": "value"}


def test_gateway_service_manager_builds_runtime_snapshot(tmp_path, monkeypatch):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  payments:\n    env_var: PESAGUARD_PAYMENTS_SERVICE_URL\n    gateway_path: /payments\n    methods: [GET, POST]\n"
    )
    monkeypatch.setenv("PESAGUARD_PAYMENTS_SERVICE_URL", "https://payments.internal")
    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path, redis_url="redis://localhost:6379/0")
    manager = GatewayServiceManager(settings)

    snapshot = manager.runtime_snapshot()

    assert snapshot["service"] == "gateway"
    assert snapshot["route_count"] == 1
    assert snapshot["configured_upstreams"] == ["payments"]
    assert snapshot["services"][0]["name"] == "payments"
    assert snapshot["services"][0]["configured"] is True


def test_health_probe_detector():
    assert is_health_probe("/metrics", {"/health", "/metrics"})
    assert not is_health_probe("/api/v1/payments", {"/health", "/metrics"})
