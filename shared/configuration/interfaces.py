from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from shared.configuration.config import AppConfig


class ConfigurationProvider(ABC):
    """Abstract contract for configuration sources that can materialize AppConfig."""

    @abstractmethod
    def get_config(self) -> AppConfig:
        """Return an application configuration instance."""


class ConfigurationReloadHook(ABC):
    """Hook executed when configuration is reloaded."""

    @abstractmethod
    def on_reload(self, config: AppConfig) -> None:
        """Receive a newly loaded configuration instance."""


class SecretProvider(ABC):
    """Abstract interface for dynamic secret retrieval."""

    @abstractmethod
    def get_secret(self, key: str) -> str:
        """Resolve a secret value by key."""


class ConfigurationStore(ABC):
    """Generic configuration store abstraction for future remote configuration integrations."""

    @abstractmethod
    def load(self) -> dict[str, Any]:
        """Load raw configuration data from the backing store."""

    @abstractmethod
    def save(self, data: dict[str, Any]) -> None:
        """Persist raw configuration data to the backing store."""
