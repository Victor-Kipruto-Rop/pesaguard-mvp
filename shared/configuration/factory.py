from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from shared.configuration.constants import CONFIG_PATH_VARIABLE, EnvironmentName
from shared.configuration.config import AppConfig
from shared.configuration.environment import detect_environment
from shared.configuration.exceptions.config_exception import ConfigurationError
from shared.configuration.loader import ConfigurationLoader


class ConfigurationRegistry:
    """Singleton registry for loaded configuration instances."""

    _instances: dict[str, AppConfig] = {}

    @classmethod
    def register(cls, name: str, config: AppConfig) -> None:
        cls._instances[name] = config

    @classmethod
    def get(cls, name: str = "default") -> AppConfig:
        if name not in cls._instances:
            raise ConfigurationError(f"Configuration '{name}' is not registered")
        return cls._instances[name]

    @classmethod
    def clear(cls) -> None:
        cls._instances.clear()


class ConfigurationFactory:
    """Factory that produces application configuration instances."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config_path = config_path or os.environ.get(CONFIG_PATH_VARIABLE)
        self.loader = ConfigurationLoader(self.config_path)

    @lru_cache(maxsize=1)
    def get_config(self) -> AppConfig:
        environment_name = detect_environment().name
        if environment_name not in EnvironmentName:
            raise ConfigurationError(f"Unsupported environment: {environment_name}")
        config = self.loader.load_with_environment_overrides(AppConfig)
        ConfigurationRegistry.register("default", config)
        return config

    def reload(self) -> AppConfig:
        self.loader = ConfigurationLoader(self.config_path)
        self.get_config.cache_clear()
        ConfigurationRegistry.clear()
        return self.get_config()


def get_configuration(factory: Optional[ConfigurationFactory] = None) -> AppConfig:
    return (factory or ConfigurationFactory()).get_config()
