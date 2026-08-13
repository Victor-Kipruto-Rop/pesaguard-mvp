from __future__ import annotations

from typing import Any, Dict, List

from pydantic import ValidationError


class SettingsValidationError(RuntimeError):
    """Raised when a settings model fails validation."""

    def __init__(self, errors: List[Dict[str, Any]]) -> None:
        self.errors = errors
        message = "Configuration validation failed"
        super().__init__(message)

    @classmethod
    def from_pydantic(cls, error: ValidationError) -> "SettingsValidationError":
        return cls(errors=error.errors())
