from __future__ import annotations

import os
from typing import Any

from shared.configuration.config import AppConfig
from shared.configuration.factory import ConfigurationFactory, ConfigurationRegistry
from shared.configuration.interfaces import ConfigurationReloadHook, ConfigurationProvider
from shared.configuration.loader import ConfigurationLoader


class ConfigurationAuditEntry(dict):
    """Simple audit entry for config reload operations."""

    pass


class ConfigurationManager(ConfigurationProvider):
    """High-level orchestrator for loading, caching, reloading, and exporting configuration."""

    def __init__(self, config_path: str | None = None, *, reload_hooks: list[ConfigurationReloadHook] | None = None) -> None:
        self.config_path = config_path or os.environ.get("PESAGUARD_CONFIG_PATH")
        self.factory = ConfigurationFactory(self.config_path)
        self.reload_hooks = list(reload_hooks or [])
        self._audit_log: list[ConfigurationAuditEntry] = []

    def get_config(self) -> AppConfig:
        config = self.factory.get_config()
        return config

    def reload(self) -> AppConfig:
        config = self.factory.reload()
        for hook in self.reload_hooks:
            hook.on_reload(config)
        self._audit_log.append(ConfigurationAuditEntry({"event": "reload", "app_name": config.app_name, "environment": config.environment.value}))
        return config

    def snapshot(self) -> dict[str, Any]:
        return self.get_config().export(mask_secrets=True)

    def get_audit_log(self) -> list[dict[str, Any]]:
        return list(self._audit_log)

    def export(self, mask_secrets: bool = True) -> dict[str, Any]:
        return self.get_config().export(mask_secrets=mask_secrets)

    def get_loader(self) -> ConfigurationLoader:
        return self.factory.loader

    def clear_cache(self) -> None:
        ConfigurationRegistry.clear()
        self.factory.get_config.cache_clear()
