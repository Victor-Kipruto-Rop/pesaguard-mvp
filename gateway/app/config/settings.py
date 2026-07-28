"""Typed, fail-fast configuration for the gateway."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.routes import RouteConfig


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="PESAGUARD_", extra="ignore")

    environment: str = "development"
    app_name: str = "PesaGuard API Gateway"
    version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    log_level: str = "INFO"
    docs_enabled: bool = True
    allowed_origins: list[str] = ["http://localhost:3000"]
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "testserver"]
    trusted_proxy_ips: list[str] = []
    allowed_ips: list[str] = []
    denied_ips: list[str] = []
    jwt_secret: SecretStr = SecretStr("development-only-change-me-please-32")
    jwt_algorithm: str = "HS256"
    jwt_jwks_url: AnyHttpUrl | None = None
    jwt_jwks_cache_seconds: int = Field(default=300, ge=30, le=86400)
    jwt_audience: str = "pesaguard-api"
    jwt_issuer: str = "pesaguard"
    api_key_hashes: list[str] = []
    api_key_scopes: dict[str, list[str]] = {}
    rate_limit_requests: int = Field(default=120, ge=1)
    rate_limit_window_seconds: int = Field(default=60, ge=1)
    rate_limit_burst: int = Field(default=0, ge=0, le=10_000)
    rate_limit_fail_open: bool = False
    request_max_bytes: int = Field(default=1_048_576, ge=1)
    allowed_content_types: list[str] = ["application/json", "application/x-www-form-urlencoded", "multipart/form-data"]
    idempotency_ttl_seconds: int = Field(default=86_400, ge=60, le=604_800)
    idempotency_lock_seconds: int = Field(default=120, ge=10, le=600)
    redis_url: str | None = None
    database_url: str | None = None
    otel_endpoint: str | None = None
    auth_service_url: AnyHttpUrl | None = None
    organizations_service_url: AnyHttpUrl | None = None
    merchants_service_url: AnyHttpUrl | None = None
    payments_service_url: AnyHttpUrl | None = None
    reconciliation_service_url: AnyHttpUrl | None = None
    notifications_service_url: AnyHttpUrl | None = None
    transactions_service_url: AnyHttpUrl | None = None
    reports_service_url: AnyHttpUrl | None = None
    audit_service_url: AnyHttpUrl | None = None
    upstream_timeout_seconds: float = Field(default=10, gt=0, le=120)
    downstream_mtls_required: bool = False
    downstream_ca_bundle: Path | None = None
    downstream_client_certificate: Path | None = None
    downstream_client_key: Path | None = None
    upstream_max_retries: int = Field(default=2, ge=0, le=5)
    upstream_failure_threshold: int = Field(default=5, ge=1, le=100)
    upstream_circuit_reset_seconds: int = Field(default=30, ge=1, le=3600)
    service_health_cache_seconds: int = Field(default=15, ge=0, le=300)
    route_config_path: Path | None = None
    route_config: RouteConfig | None = None

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        allowed = {"development", "test", "staging", "production"}
        if value not in allowed:
            raise ValueError(f"environment must be one of {sorted(allowed)}")
        return value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        value = value.upper()
        if value not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("log_level must be a standard Python log level")
        return value

    @field_validator("api_key_hashes")
    @classmethod
    def validate_api_key_hashes(cls, values: list[str]) -> list[str]:
        if any(len(value) != 64 or any(char not in "0123456789abcdef" for char in value.lower()) for value in values):
            raise ValueError("api_key_hashes must contain SHA-256 hexadecimal digests")
        return values

    @field_validator("api_key_scopes")
    @classmethod
    def validate_api_key_scopes(cls, values: dict[str, list[str]]) -> dict[str, list[str]]:
        if any(len(key) != 64 or not scopes for key, scopes in values.items()):
            raise ValueError("api_key_scopes must map a SHA-256 digest to at least one scope")
        return values

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.environment == "production":
            if self.jwt_algorithm == "HS256" and len(self.jwt_secret.get_secret_value()) < 32:
                raise ValueError("PESAGUARD_JWT_SECRET must be at least 32 characters in production")
            if self.jwt_algorithm not in {"RS256", "ES256"} or not self.jwt_jwks_url:
                raise ValueError("production requires RS256 or ES256 JWT verification with PESAGUARD_JWT_JWKS_URL")
            if "*" in self.allowed_origins or "*" in self.allowed_hosts:
                raise ValueError("wildcard origins and hosts are not allowed in production")
            if not self.redis_url:
                raise ValueError("PESAGUARD_REDIS_URL is required in production for distributed rate limiting")
            if self.docs_enabled:
                raise ValueError("interactive API documentation must be explicitly disabled in production")
            if set(self.api_key_scopes) - set(self.api_key_hashes):
                raise ValueError("every API key scope mapping must reference a configured API key hash")
            if self.downstream_mtls_required and not all((self.downstream_ca_bundle, self.downstream_client_certificate, self.downstream_client_key)):
                raise ValueError("mTLS requires a CA bundle, client certificate, and client key")
        return self

    @model_validator(mode="after")
    def load_route_config(self) -> "Settings":
        if self.route_config is None:
            config_path = self.route_config_path or Path(__file__).parent / "routes.yaml"
            self.route_config = RouteConfig.load(config_path)
        return self

    def service_env_var(self, service: str) -> str | None:
        if self.route_config and service in self.route_config.services:
            return self.route_config.env_var_for(service)
        return None

    def service_health_path(self, service: str) -> str | None:
        if self.route_config and service in self.route_config.services:
            return self.route_config.health_path_for(service)
        return None

    def service_health_method(self, service: str) -> str | None:
        if self.route_config and service in self.route_config.services:
            return self.route_config.health_method_for(service)
        return None

    def supported_methods_for(self, service: str) -> tuple[str, ...] | None:
        if self.route_config and service in self.route_config.services:
            return self.route_config.supported_methods_for(service)
        return None

    def path_prefix_for(self, service: str) -> str | None:
        if self.route_config and service in self.route_config.services:
            return self.route_config.path_prefix_for(service)
        return None

    def upstream_for(self, service: str) -> str | None:
        env_var = self.service_env_var(service)
        if env_var:
            value = os.environ.get(env_var)
            if value:
                return value.rstrip("/")
        value = getattr(self, f"{service}_service_url", None)
        return str(value).rstrip("/") if value else None

    def route_services(self) -> tuple[str, ...]:
        return tuple(self.route_config.service_names()) if self.route_config else ()


@lru_cache
def get_settings() -> Settings:
    return Settings()
