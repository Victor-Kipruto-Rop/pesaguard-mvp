"""Typed, fail-fast configuration for the gateway."""
from functools import lru_cache
from typing import Annotated

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="PESAGUARD_", extra="ignore")

    environment: str = "development"
    app_name: str = "PesaGuard API Gateway"
    version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    log_level: str = "INFO"
    allowed_origins: list[str] = ["http://localhost:3000"]
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "testserver"]
    trusted_proxy_ips: list[str] = []
    allowed_ips: list[str] = []
    denied_ips: list[str] = []
    jwt_secret: SecretStr = SecretStr("development-only-change-me-please-32")
    jwt_algorithm: str = "HS256"
    jwt_audience: str = "pesaguard-api"
    jwt_issuer: str = "pesaguard"
    api_key_hashes: list[str] = []
    rate_limit_requests: int = Field(default=120, ge=1)
    rate_limit_window_seconds: int = Field(default=60, ge=1)
    request_max_bytes: int = Field(default=1_048_576, ge=1)
    redis_url: str | None = None
    database_url: str | None = None
    otel_endpoint: str | None = None
    auth_service_url: AnyHttpUrl | None = None
    organizations_service_url: AnyHttpUrl | None = None
    merchants_service_url: AnyHttpUrl | None = None
    payments_service_url: AnyHttpUrl | None = None
    reconciliation_service_url: AnyHttpUrl | None = None
    notifications_service_url: AnyHttpUrl | None = None
    upstream_timeout_seconds: float = Field(default=10, gt=0, le=120)

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        allowed = {"development", "test", "staging", "production"}
        if value not in allowed:
            raise ValueError(f"environment must be one of {sorted(allowed)}")
        return value

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.environment == "production":
            if len(self.jwt_secret.get_secret_value()) < 32:
                raise ValueError("PESAGUARD_JWT_SECRET must be at least 32 characters in production")
            if "*" in self.allowed_origins or "*" in self.allowed_hosts:
                raise ValueError("wildcard origins and hosts are not allowed in production")
        return self

    def upstream_for(self, service: str) -> str | None:
        value = getattr(self, f"{service}_service_url", None)
        return str(value).rstrip("/") if value else None


@lru_cache
def get_settings() -> Settings:
    return Settings()
