from __future__ import annotations

from typing import Any, Dict, Optional


class BaseApplicationError(Exception):
    """Base exception for application-level failures with structured metadata."""

    def __init__(self, message: str, *, error_code: Optional[str] = None, status_code: int = 500, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "INTERNAL_ERROR"
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message,
            "error_code": self.error_code,
            "status_code": self.status_code,
            "details": self.details,
        }
