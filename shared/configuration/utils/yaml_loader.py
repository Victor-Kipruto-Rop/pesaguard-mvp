from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Dict

from shared.configuration.exceptions.config_exception import ConfigurationError


def load_yaml_file(path: str) -> Dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigurationError(f"YAML file not found: {path}")
    try:
        with config_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"Invalid YAML file: {path}") from exc
    if not isinstance(data, dict):
        raise ConfigurationError("YAML configuration root must be a mapping")
    return data
