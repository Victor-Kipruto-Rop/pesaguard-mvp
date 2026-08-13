from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from shared.configuration.config import AppConfig
from shared.configuration.constants import EnvironmentName, SENSITIVE_FIELDS
from shared.configuration.environment import detect_environment, EnvironmentProfile
from shared.configuration.exceptions.config_exception import ConfigurationError
from shared.configuration.exceptions.validation_exception import SettingsValidationError
from shared.configuration.factory import ConfigurationFactory, ConfigurationRegistry
from shared.configuration.loader import ConfigurationLoader
from shared.configuration.utils.env_loader import load_environment_variables, mask_sensitive_values


def test_detect_environment_default(monkeypatch):
    monkeypatch.delenv("PESAGUARD_ENVIRONMENT", raising=False)
    profile = detect_environment()
    assert isinstance(profile, EnvironmentProfile)
    assert profile.name == EnvironmentName.DEVELOPMENT


def test_detect_environment_invalid(monkeypatch):
    monkeypatch.setenv("PESAGUARD_ENVIRONMENT", "invalid")
    with pytest.raises(ConfigurationError):
        detect_environment()


def test_load_json_file(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "version": "1.0",
        "environment": "development",
        "app_name": "pesaguard",
        "app_version": "0.1.0",
        "database": {"url": "postgresql://postgres:postgres@localhost:5432/pesaguard"},
        "redis": {"url": "redis://localhost:6379/0"},
        "gateway": {"host": "0.0.0.0", "port": 8080},
        "api": {"title": "PesaGuard API", "version": "v1", "openapi_url": "http://localhost:8000/openapi.json", "request_limit_per_minute": 1200, "page_size_default": 50, "page_size_max": 250},
        "logging": {"level": "INFO", "structured": True, "file_path": "/tmp/app.log", "max_file_size_mb": 50, "backup_count": 5},
        "monitoring": {"prometheus_endpoint": "http://localhost:9090", "enabled": True, "scrape_interval_seconds": 15, "metrics_prefix": "pesaguard"},
        "telemetry": {"otlp_endpoint": "http://localhost:4318", "service_name": "pesaguard", "traces_sample_rate": 0.2, "metrics_enabled": True, "traces_enabled": True},
        "security": {"jwt_secret": "a" * 32, "encryption_key": "b" * 32, "allowed_hosts": ["localhost"], "password_salt_rounds": 12},
        "cache": {"default_ttl_seconds": 300, "max_items": 10000, "eviction_policy": "LRU", "stale_after_seconds": 60},
        "email": {"smtp_host": "localhost", "smtp_port": 1025, "username": "test", "password": "testpass", "default_from_address": "no-reply@pesaguard.local", "use_tls": False},
        "notifications": {"email_enabled": True, "sms_enabled": False, "email_from_address": "no-reply@pesaguard.local"},
        "feature_flags": {"enable_experimental_payments": False, "enable_service_mesh": True, "enable_rate_limiting": True, "enable_caching": True, "flag_overrides": {}},
        "integrations": {"payment_provider_url": "http://localhost:9000", "notification_provider_url": "http://localhost:9001", "auth_provider_url": "http://localhost:9002", "retry_attempts": 3, "retry_backoff_seconds": 5, "default_timeout_seconds": 15},
        "scheduler": {"enabled": True, "max_workers": 10, "default_interval_seconds": 60, "retry_attempts": 3, "retry_backoff_seconds": 5},
        "storage": {"provider": "local", "base_path": "/tmp/storage", "endpoint": None, "max_file_size_mb": 100},
    }))
    loader = ConfigurationLoader(str(config_path))
    config = loader.load_file()
    assert config["environment"] == "development"


def test_create_settings_from_file(tmp_path):
    config_data = {
        "version": "1.0",
        "environment": "testing",
        "app_name": "pesaguard",
        "app_version": "0.1.0",
        "database": {"url": "postgresql://postgres:postgres@localhost:5432/pesaguard"},
        "redis": {"url": "redis://localhost:6379/0"},
        "gateway": {"host": "0.0.0.0", "port": 8080},
        "api": {"title": "PesaGuard API", "version": "v1", "openapi_url": "http://localhost:8000/openapi.json", "request_limit_per_minute": 1200, "page_size_default": 50, "page_size_max": 250},
        "logging": {"level": "INFO", "structured": True, "file_path": "/tmp/app.log", "max_file_size_mb": 50, "backup_count": 5},
        "monitoring": {"prometheus_endpoint": "http://localhost:9090", "enabled": True, "scrape_interval_seconds": 15, "metrics_prefix": "pesaguard"},
        "telemetry": {"otlp_endpoint": "http://localhost:4318", "service_name": "pesaguard", "traces_sample_rate": 0.2, "metrics_enabled": True, "traces_enabled": True},
        "security": {"jwt_secret": "a" * 32, "encryption_key": "b" * 32, "allowed_hosts": ["localhost"], "password_salt_rounds": 12},
        "cache": {"default_ttl_seconds": 300, "max_items": 10000, "eviction_policy": "LRU", "stale_after_seconds": 60},
        "email": {"smtp_host": "localhost", "smtp_port": 1025, "username": "test", "password": "testpass", "default_from_address": "no-reply@pesaguard.local", "use_tls": False},
        "notifications": {"email_enabled": True, "sms_enabled": False, "email_from_address": "no-reply@pesaguard.local"},
        "feature_flags": {"enable_experimental_payments": False, "enable_service_mesh": True, "enable_rate_limiting": True, "enable_caching": True, "flag_overrides": {}},
        "integrations": {"payment_provider_url": "http://localhost:9000", "notification_provider_url": "http://localhost:9001", "auth_provider_url": "http://localhost:9002", "retry_attempts": 3, "retry_backoff_seconds": 5, "default_timeout_seconds": 15},
        "scheduler": {"enabled": True, "max_workers": 10, "default_interval_seconds": 60, "retry_attempts": 3, "retry_backoff_seconds": 5},
        "storage": {"provider": "local", "base_path": "/tmp/storage", "endpoint": None, "max_file_size_mb": 100},
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config_data))
    loader = ConfigurationLoader(str(config_path))
    settings = loader.create_settings(AppConfig)
    assert settings.environment == EnvironmentName.TESTING
    assert settings.app_name == "pesaguard"


def test_configuration_overrides(monkeypatch, tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "version": "1.0",
        "environment": "development",
        "app_name": "pesaguard",
        "app_version": "0.1.0",
        "database": {"url": "postgresql://postgres:postgres@localhost:5432/pesaguard"},
        "redis": {"url": "redis://localhost:6379/0"},
        "gateway": {"host": "0.0.0.0", "port": 8080},
        "api": {"title": "PesaGuard API", "version": "v1", "openapi_url": "http://localhost:8000/openapi.json", "request_limit_per_minute": 1200, "page_size_default": 50, "page_size_max": 250},
        "logging": {"level": "INFO", "structured": True, "file_path": "/tmp/app.log", "max_file_size_mb": 50, "backup_count": 5},
        "monitoring": {"prometheus_endpoint": "http://localhost:9090", "enabled": True, "scrape_interval_seconds": 15, "metrics_prefix": "pesaguard"},
        "telemetry": {"otlp_endpoint": "http://localhost:4318", "service_name": "pesaguard", "traces_sample_rate": 0.2, "metrics_enabled": True, "traces_enabled": True},
        "security": {"jwt_secret": "a" * 32, "encryption_key": "b" * 32, "allowed_hosts": ["localhost"], "password_salt_rounds": 12},
        "cache": {"default_ttl_seconds": 300, "max_items": 10000, "eviction_policy": "LRU", "stale_after_seconds": 60},
        "email": {"smtp_host": "localhost", "smtp_port": 1025, "username": "test", "password": "testpass", "default_from_address": "no-reply@pesaguard.local", "use_tls": False},
        "notifications": {"email_enabled": True, "sms_enabled": False, "email_from_address": "no-reply@pesaguard.local"},
        "feature_flags": {"enable_experimental_payments": False, "enable_service_mesh": True, "enable_rate_limiting": True, "enable_caching": True, "flag_overrides": {}},
        "integrations": {"payment_provider_url": "http://localhost:9000", "notification_provider_url": "http://localhost:9001", "auth_provider_url": "http://localhost:9002", "retry_attempts": 3, "retry_backoff_seconds": 5, "default_timeout_seconds": 15},
        "scheduler": {"enabled": True, "max_workers": 10, "default_interval_seconds": 60, "retry_attempts": 3, "retry_backoff_seconds": 5},
        "storage": {"provider": "local", "base_path": "/tmp/storage", "endpoint": None, "max_file_size_mb": 100},
    }))
    monkeypatch.setenv("PESAGUARD_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("PESAGUARD_ENVIRONMENT", "testing")
    monkeypatch.setenv("PESAGUARD_ENVIRONMENT__name", "production")
    monkeypatch.setenv("PESAGUARD_API__TITLE", "PesaGuard Override")
    factory = ConfigurationFactory()
    configuration = factory.get_config()
    assert configuration.api.title == "PesaGuard Override"


def test_configuration_registry():
    ConfigurationRegistry.clear()
    config = AppConfig.model_validate({
        "version": "1.0",
        "environment": "development",
        "app_name": "pesaguard",
        "app_version": "0.1.0",
        "database": {"url": "postgresql://postgres:postgres@localhost:5432/pesaguard"},
        "redis": {"url": "redis://localhost:6379/0"},
        "gateway": {"host": "0.0.0.0", "port": 8080},
        "api": {"title": "PesaGuard API", "version": "v1", "openapi_url": "http://localhost:8000/openapi.json", "request_limit_per_minute": 1200, "page_size_default": 50, "page_size_max": 250},
        "logging": {"level": "INFO", "structured": True, "file_path": "/tmp/app.log", "max_file_size_mb": 50, "backup_count": 5},
        "monitoring": {"prometheus_endpoint": "http://localhost:9090", "enabled": True, "scrape_interval_seconds": 15, "metrics_prefix": "pesaguard"},
        "telemetry": {"otlp_endpoint": "http://localhost:4318", "service_name": "pesaguard", "traces_sample_rate": 0.2, "metrics_enabled": True, "traces_enabled": True},
        "security": {"jwt_secret": "a" * 32, "encryption_key": "b" * 32, "allowed_hosts": ["localhost"], "password_salt_rounds": 12},
        "cache": {"default_ttl_seconds": 300, "max_items": 10000, "eviction_policy": "LRU", "stale_after_seconds": 60},
        "email": {"smtp_host": "localhost", "smtp_port": 1025, "username": "test", "password": "testpass", "default_from_address": "no-reply@pesaguard.local", "use_tls": False},
        "notifications": {"email_enabled": True, "sms_enabled": False, "email_from_address": "no-reply@pesaguard.local"},
        "feature_flags": {"enable_experimental_payments": False, "enable_service_mesh": True, "enable_rate_limiting": True, "enable_caching": True, "flag_overrides": {}},
        "integrations": {"payment_provider_url": "http://localhost:9000", "notification_provider_url": "http://localhost:9001", "auth_provider_url": "http://localhost:9002", "retry_attempts": 3, "retry_backoff_seconds": 5, "default_timeout_seconds": 15},
        "scheduler": {"enabled": True, "max_workers": 10, "default_interval_seconds": 60, "retry_attempts": 3, "retry_backoff_seconds": 5},
        "storage": {"provider": "local", "base_path": "/tmp/storage", "endpoint": None, "max_file_size_mb": 100},
    })
    ConfigurationRegistry.register("default", config)
    assert ConfigurationRegistry.get("default").app_name == "pesaguard"


def test_mask_sensitive_values():
    values = {"PESAGUARD_JWT_SECRET": "secret", "PESAGUARD_APP_NAME": "pesaguard"}
    masked = mask_sensitive_values(values)
    assert masked["PESAGUARD_JWT_SECRET"] == "*****"
    assert masked["PESAGUARD_APP_NAME"] == "pesaguard"
