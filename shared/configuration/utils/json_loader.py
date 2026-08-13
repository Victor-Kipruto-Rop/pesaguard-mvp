from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from shared.configuration.exceptions.config_exception import ConfigurationError


def load_json_file(path: str) -> Dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigurationError(f"JSON file not found: {path}")
    try:
        with config_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except ValueError as exc:
        raise ConfigurationError(f"Invalid JSON file: {path}") from exc
    if not isinstance(data, dict):
        raise ConfigurationError("JSON configuration root must be an object")
    return data
