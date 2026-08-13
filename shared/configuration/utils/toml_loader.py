from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Dict

from shared.configuration.exceptions.config_exception import ConfigurationError


def load_toml_file(path: str) -> Dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigurationError(f"TOML file not found: {path}")
    try:
        with config_path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigurationError(f"Invalid TOML file: {path}") from exc
    if not isinstance(data, dict):
        raise ConfigurationError("TOML configuration root must be a table")
    return data
