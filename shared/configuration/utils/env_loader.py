from __future__ import annotations

import os
from typing import Dict, Optional

from pydantic import BaseModel

from shared.configuration.constants import SENSITIVE_FIELDS


def load_environment_variables(prefix: str = "PESAGUARD_") -> Dict[str, str]:
    return {key: value for key, value in os.environ.items() if key.startswith(prefix)}


def mask_sensitive_values(values: Dict[str, str], mask: str = "*****") -> Dict[str, str]:
    masked: Dict[str, str] = {}
    for key, value in values.items():
        normalized_key = key.lower()
        if any(field in normalized_key for field in SENSITIVE_FIELDS):
            masked[key] = mask
        else:
            masked[key] = value
    return masked


def flatten_settings(settings: BaseModel) -> Dict[str, str]:
    return {key: str(value) for key, value in settings.model_dump().items()}
