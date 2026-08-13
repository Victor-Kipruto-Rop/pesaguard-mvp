from __future__ import annotations

from shared.configuration.manager import ConfigurationManager


class MissingSecretError(RuntimeError):
    pass


def test_manager_rejects_missing_required_secret(tmp_path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        '{"version":"1.0","environment":"development","app_name":"billing","app_version":"0.1.0",'
        '"database":{"url":"postgresql://postgres:postgres@localhost:5432/billing"},'
        '"redis":{"url":"redis://localhost:6379/0"},'
        '"gateway":{"host":"0.0.0.0","port":8080},'
        '"api":{"title":"Billing API","version":"v1","openapi_url":"http://localhost:8000/openapi.json",'
        '"request_limit_per_minute":1200,"page_size_default":50,"page_size_max":250},'
        '"logging":{"level":"INFO","structured":true,"file_path":"/tmp/billing.log","max_file_size_mb":50,"backup_count":5},'
        '"monitoring":{"prometheus_endpoint":"http://localhost:9090","enabled":true,"scrape_interval_seconds":15,"metrics_prefix":"billing"},'
        '"telemetry":{"otlp_endpoint":"http://localhost:4318","service_name":"billing","traces_sample_rate":0.2,"metrics_enabled":true,"traces_enabled":true},'
        '"security":{"jwt_secret":"","encryption_key":"0123456789abcdefghijklmnopqrstuvwxzy","allowed_hosts":["localhost"],"password_salt_rounds":12},'
        '"cache":{"default_ttl_seconds":300,"max_items":10000,"eviction_policy":"LRU","stale_after_seconds":60},'
        '"email":{"smtp_host":"localhost","smtp_port":1025,"username":"test","password":"testpass","default_from_address":"no-reply@billing.local","use_tls":false},'
        '"notifications":{"email_enabled":true,"sms_enabled":false,"email_from_address":"no-reply@billing.local"},'
        '"feature_flags":{"enable_experimental_payments":false,"enable_service_mesh":true,"enable_rate_limiting":true,"enable_caching":true,"flag_overrides":{}},'
        '"integrations":{"payment_provider_url":"http://localhost:9000","notification_provider_url":"http://localhost:9001","auth_provider_url":"http://localhost:9002","retry_attempts":3,"retry_backoff_seconds":5,"default_timeout_seconds":15},'
        '"scheduler":{"enabled":true,"max_workers":10,"default_interval_seconds":60,"retry_attempts":3,"retry_backoff_seconds":5},'
        '"storage":{"provider":"local","base_path":"/tmp/storage","endpoint":null,"max_file_size_mb":100}}'
    )

    manager = ConfigurationManager(str(config_path))
    try:
        manager.reload()
    except Exception as exc:
        assert "secret" in str(exc).lower() or "validation" in str(exc).lower()
    else:
        raise MissingSecretError("Expected validation to fail for empty secrets")
