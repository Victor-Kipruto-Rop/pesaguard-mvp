from __future__ import annotations

from pydantic import BaseModel, Field

from shared.configuration.constants import EnvironmentName
from shared.configuration.schemas import api as api_schema
from shared.configuration.schemas import cache as cache_schema
from shared.configuration.schemas import database as database_schema
from shared.configuration.schemas import email as email_schema
from shared.configuration.schemas import feature_flags as feature_flags_schema
from shared.configuration.schemas import gateway as gateway_schema
from shared.configuration.schemas import integrations as integrations_schema
from shared.configuration.schemas import logging as logging_schema
from shared.configuration.schemas import monitoring as monitoring_schema
from shared.configuration.schemas import redis as redis_schema
from shared.configuration.schemas import scheduler as scheduler_schema
from shared.configuration.schemas import security as security_schema
from shared.configuration.schemas import storage as storage_schema
from shared.configuration.schemas import telemetry as telemetry_schema
from shared.configuration.schemas import notifications as notifications_schema


class TestingProfile(BaseModel):
    environment_name: EnvironmentName = Field(EnvironmentName.TESTING, description="Environment name")
    database: database_schema.DatabaseSettings = Field(
        default_factory=lambda: database_schema.DatabaseSettings(
            url="postgresql://postgres:postgres@localhost:5432/pesaguard_test"
        )
    )
    redis: redis_schema.RedisSettings = Field(
        default_factory=lambda: redis_schema.RedisSettings(url="redis://localhost:6379/1")
    )
    gateway: gateway_schema.GatewaySettings = Field(default_factory=gateway_schema.GatewaySettings)
    api: api_schema.APISettings = Field(
        default_factory=lambda: api_schema.APISettings(
            title="PesaGuard API Test",
            version="test",
            openapi_url="http://localhost:8001/openapi.json"
        )
    )
    logging: logging_schema.LoggingSettings = Field(
        default_factory=lambda: logging_schema.LoggingSettings(level="DEBUG")
    )
    monitoring: monitoring_schema.MonitoringSettings = Field(
        default_factory=lambda: monitoring_schema.MonitoringSettings(prometheus_endpoint="http://localhost:9091")
    )
    telemetry: telemetry_schema.TelemetrySettings = Field(
        default_factory=lambda: telemetry_schema.TelemetrySettings(otlp_endpoint="http://localhost:4319", service_name="pesaguard-test")
    )
    security: security_schema.SecuritySettings = Field(
        default_factory=lambda: security_schema.SecuritySettings(
            jwt_secret="testing-jwt-secret-1234567890123456",
            encryption_key="testing-encryption-key-1234567890",
            allowed_hosts=["localhost"],
        )
    )
    cache: cache_schema.CacheSettings = Field(default_factory=cache_schema.CacheSettings)
    email: email_schema.EmailSettings = Field(
        default_factory=lambda: email_schema.EmailSettings(
            smtp_host="localhost",
            smtp_port=1025,
            username="test",
            password="testpass",
            default_from_address="no-reply@pesaguard.test",
            use_tls=False,
        )
    )
    notifications: notifications_schema.NotificationSettings = Field(
        default_factory=lambda: notifications_schema.NotificationSettings(
            email_enabled=False,
            sms_enabled=False,
            email_from_address="no-reply@pesaguard.test",
        )
    )
    feature_flags: feature_flags_schema.FeatureFlagsSettings = Field(default_factory=feature_flags_schema.FeatureFlagsSettings)
    integrations: integrations_schema.IntegrationSettings = Field(
        default_factory=lambda: integrations_schema.IntegrationSettings(
            payment_provider_url="http://localhost:9100",
            notification_provider_url="http://localhost:9101",
            auth_provider_url="http://localhost:9102"
        )
    )
    scheduler: scheduler_schema.SchedulerSettings = Field(default_factory=scheduler_schema.SchedulerSettings)
    storage: storage_schema.StorageSettings = Field(default_factory=storage_schema.StorageSettings)
