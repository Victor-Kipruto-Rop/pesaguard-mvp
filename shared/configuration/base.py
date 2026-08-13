from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Self

from pydantic import BaseModel
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

from shared.configuration.constants import CONFIG_PATH_VARIABLE, DEFAULT_CONFIG_DIR, DEFAULT_CONFIG_FILE_NAME
from shared.configuration.exceptions.config_exception import ConfigurationError


class ConfigBase(ABC, BaseSettings):
    """Base class for all configuration models."""

    model_config = ConfigDict(
        env_prefix="PESAGUARD_",
        extra="forbid",
        validate_assignment=True,
        frozen=True,
        case_sensitive=False,
    )

    @classmethod
    def load_json_file(cls, path: Optional[str] = None) -> Dict[str, Any]:
        config_path = path or os.environ.get(CONFIG_PATH_VARIABLE)
        if config_path:
            config_path = Path(config_path)
        else:
            config_path = Path(DEFAULT_CONFIG_DIR) / DEFAULT_CONFIG_FILE_NAME
        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        try:
            return json.loads(config_path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise ConfigurationError(f"Invalid JSON configuration file {config_path}") from exc

    @classmethod
    def create_from_source(cls, config: Optional[Dict[str, Any]] = None, path: Optional[str] = None) -> Self:
        raw = config or cls.load_json_file(path)
        return cls.model_validate(raw)

    @abstractmethod
    def export(self) -> Dict[str, Any]:
        raise NotImplementedError
