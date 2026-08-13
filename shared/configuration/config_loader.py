from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional


class ValidationError(ValueError):
    """Raised when configuration validation fails."""


class ConfigLoader:
    """Loads JSON-based configuration with required-key validation."""

    def __init__(self, path: str, *, required_keys: Optional[List[str]] = None) -> None:
        self.path = path
        self.required_keys = required_keys or []

    def load(self) -> Dict[str, Any]:
        if not os.path.exists(self.path):
            raise FileNotFoundError(self.path)
        with open(self.path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValidationError("configuration root must be a JSON object")
        missing = [key for key in self.required_keys if key not in data]
        if missing:
            raise ValidationError(f"missing required configuration keys: {', '.join(missing)}")
        return data
