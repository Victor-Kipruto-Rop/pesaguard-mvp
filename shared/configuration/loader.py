from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import ValidationError

from shared.configuration.base import ConfigBase
from shared.configuration.constants import (
    CONFIG_PATH_VARIABLE,
    CONFIG_VERSION_ENV,
    DEFAULT_CONFIG_DIR,
    DEFAULT_CONFIG_FILE_NAME,
    DEFAULT_CONFIG_VERSION,
    ENVIRONMENT_VARIABLE,
)
from shared.configuration.exceptions.config_exception import ConfigurationError
from shared.configuration.exceptions.validation_exception import SettingsValidationError
from shared.configuration.profile_runtime import RuntimeProfileResolver
from shared.configuration.utils.json_loader import load_json_file
from shared.configuration.utils.toml_loader import load_toml_file
from shared.configuration.utils.yaml_loader import load_yaml_file


class ConfigurationLoader:
    """Loads configuration from JSON, environment, or explicit dictionaries."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config_path = config_path or os.environ.get(CONFIG_PATH_VARIABLE)

    def get_config_path(self) -> Path:
        config_path = self.config_path or Path(DEFAULT_CONFIG_DIR) / DEFAULT_CONFIG_FILE_NAME
        if isinstance(config_path, str):
            config_path = Path(config_path)
        return config_path

    def load_file(self) -> Dict[str, Any]:
        config_path = self.get_config_path()
        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        suffix = config_path.suffix.lower()
        if suffix == ".json":
            return load_json_file(str(config_path))
        if suffix in {".yaml", ".yml"}:
            return load_yaml_file(str(config_path))
        if suffix == ".toml":
            return load_toml_file(str(config_path))
        raise ConfigurationError(f"Unsupported configuration file type: {config_path}")

    RESERVED_ENVIRONMENT_KEYS = {
        CONFIG_PATH_VARIABLE,
        ENVIRONMENT_VARIABLE,
        CONFIG_VERSION_ENV,
    }

    def load_environment(self, prefix: str = "PESAGUARD_") -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        environment_key = ENVIRONMENT_VARIABLE.split("_", 1)[-1].lower()
        for key, raw_value in os.environ.items():
            if not key.startswith(prefix):
                continue
            if key in self.RESERVED_ENVIRONMENT_KEYS:
                continue
            stripped_key = key[len(prefix) :]
            path = stripped_key.split("__")
            if not path or not path[0]:
                continue
            normalized_path = [segment.lower() for segment in path]
            value = self._parse_env_value(raw_value)
            if normalized_path[0] == environment_key:
                if len(normalized_path) == 1:
                    result["environment"] = value
                    continue
                if len(normalized_path) == 2 and normalized_path[1] == "name":
                    result["environment"] = value
                    continue
                raise ConfigurationError(f"Unsupported nested override for environment: {stripped_key}")
            self._insert_override(result, normalized_path, value)
        return result

    @staticmethod
    def _parse_env_value(value: str) -> Any:
        normalized = value.strip()
        lowered = normalized.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        if lowered == "null":
            return None
        if re.fullmatch(r"-?\d+", normalized):
            return int(normalized)
        if re.fullmatch(r"-?\d+\.\d+", normalized):
            return float(normalized)
        return value

    def _insert_override(self, target: Dict[str, Any], path: list[str], value: Any) -> None:
        key = path[0]
        if len(path) == 1:
            target[key] = value
            return
        if key not in target or not isinstance(target[key], dict):
            target[key] = {}
        self._insert_override(target[key], path[1:], value)

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        merged: Dict[str, Any] = dict(base)
        for key, override_value in override.items():
            base_value = merged.get(key)
            if isinstance(base_value, dict) and isinstance(override_value, dict):
                merged[key] = ConfigurationLoader._deep_merge(base_value, override_value)
            else:
                merged[key] = override_value
        return merged

    def create_settings(self, settings_class: type[ConfigBase], override: Optional[Dict[str, Any]] = None) -> ConfigBase:
        config = override or self.load_file()
        try:
            return settings_class.model_validate(config)
        except ValidationError as exc:
            raise SettingsValidationError.from_pydantic(exc) from exc

    def _resolve_profiles(self, config: Dict[str, Any]) -> Dict[str, Any]:
        profiles = config.get("profiles")
        if not isinstance(profiles, dict):
            return config

        active_profile = config.get("active_profile")
        if not isinstance(active_profile, str):
            active_profile = detect_environment().name.value

        resolved_profile = RuntimeProfileResolver(profiles).resolve(active_profile)
        base_config = {k: v for k, v in config.items() if k not in {"profiles", "active_profile"}}
        return self._deep_merge(base_config, resolved_profile)

    def load_with_environment_overrides(self, settings_class: type[ConfigBase]) -> ConfigBase:
        file_config = self.load_file()
        file_config = self._resolve_profiles(file_config)
        env_override = self.load_environment()
        merged = self._deep_merge(file_config, env_override)
        try:
            return settings_class.model_validate(merged)
        except ValidationError as exc:
            raise SettingsValidationError.from_pydantic(exc) from exc


class ConfigurationVersion:
    """Simple version guard for configuration artifacts."""

    @staticmethod
    def validate_version(config: Dict[str, Any]) -> None:
        version = config.get("version") or os.environ.get("PESAGUARD_CONFIG_VERSION") or DEFAULT_CONFIG_VERSION
        if not isinstance(version, str) or not version.strip():
            raise ConfigurationError("Configuration version is required")
