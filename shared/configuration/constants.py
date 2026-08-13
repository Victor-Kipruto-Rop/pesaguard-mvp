from __future__ import annotations

from enum import Enum


class EnvironmentName(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


ENVIRONMENT_VARIABLE = "PESAGUARD_ENVIRONMENT"
CONFIG_PATH_VARIABLE = "PESAGUARD_CONFIG_PATH"
CONFIG_VERSION_ENV = "PESAGUARD_CONFIG_VERSION"
DEFAULT_CONFIG_VERSION = "1.0"
SUPPORTED_ENVIRONMENTS = {
    EnvironmentName.DEVELOPMENT,
    EnvironmentName.TESTING,
    EnvironmentName.STAGING,
    EnvironmentName.PRODUCTION,
}
SENSITIVE_FIELDS = {
    "password",
    "secret",
    "token",
    "access_key",
    "secret_key",
    "jwt_secret",
    "encryption_key",
    "private_key",
    "api_key",
    "client_secret",
}
DEFAULT_CONFIG_FILE_NAME = "pesaguard.config.json"
DEFAULT_CONFIG_DIR = "/etc/pesaguard"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_REDIS_DB = 0
DEFAULT_DATABASE_PORT = 5432
DEFAULT_REDIS_PORT = 6379
DEFAULT_HTTP_TIMEOUT_SECONDS = 10
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_BACKOFF_SECONDS = 2
