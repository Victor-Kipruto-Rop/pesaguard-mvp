from __future__ import annotations

from typing import Any, Dict

from pydantic import Field, SecretStr, field_validator

from shared.configuration.base import ConfigBase
from shared.configuration.constants import DEFAULT_CONFIG_VERSION, EnvironmentName, SENSITIVE_FIELDS
from shared.configuration.schemas.api import APISettings
from shared.configuration.schemas.cache import CacheSettings
from shared.configuration.schemas.database import DatabaseSettings
from shared.configuration.schemas.email import EmailSettings
from shared.configuration.schemas.feature_flags import FeatureFlagsSettings
from shared.configuration.schemas.gateway import GatewaySettings
from shared.configuration.schemas.integrations import IntegrationSettings
from shared.configuration.schemas.logging import LoggingSettings
from shared.configuration.schemas.monitoring import MonitoringSettings
from shared.configuration.schemas.notifications import NotificationSettings
from shared.configuration.schemas.redis import RedisSettings
from shared.configuration.schemas.scheduler import SchedulerSettings
from shared.configuration.schemas.security import SecuritySettings
from shared.configuration.schemas.storage import StorageSettings
from shared.configuration.schemas.telemetry import TelemetrySettings


class AppConfig(ConfigBase):
    version: str = Field(DEFAULT_CONFIG_VERSION, description="Configuration schema version")
    environment: EnvironmentName = Field(..., description="Deployment environment")
    app_name: str = Field("pesaguard", min_length=1, description="Application logical name")
    app_version: str = Field("0.1.0", min_length=1, description="Application semantic version")
    description: str | None = Field(None, description="Application description")
    database: DatabaseSettings
    redis: RedisSettings
    gateway: GatewaySettings
    api: APISettings
    logging: LoggingSettings
    monitoring: MonitoringSettings
    telemetry: TelemetrySettings
    security: SecuritySettings
    cache: CacheSettings
    email: EmailSettings
    notifications: NotificationSettings
    feature_flags: FeatureFlagsSettings
    integrations: IntegrationSettings
    scheduler: SchedulerSettings
    storage: StorageSettings

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Configuration version must not be empty")
        return value

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: EnvironmentName) -> EnvironmentName:
        if value not in EnvironmentName:
            raise ValueError(f"Unsupported environment '{value}'")
        return value

    def export(self, mask_secrets: bool = True) -> Dict[str, Any]:
        raw = self.model_dump()
        if not mask_secrets:
            return raw
        return self._mask_dict(raw)

    @staticmethod
    def _mask_dict(data: dict[str, Any]) -> dict[str, Any]:
        masked: dict[str, Any] = {}
        for key, value in data.items():
            normalized_key = key.lower()
            if isinstance(value, SecretStr) or any(field in normalized_key for field in SENSITIVE_FIELDS):
                masked[key] = "*****"
            elif isinstance(value, dict):
                masked[key] = AppConfig._mask_dict(value)
            else:
                masked[key] = value
        return masked
