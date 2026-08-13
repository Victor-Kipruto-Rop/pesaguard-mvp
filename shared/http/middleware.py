from __future__ import annotations

from typing import Any, Callable, Dict


class HTTPException(Exception):
    def __init__(self, status_code: int, message: str, *, details: Dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.details = details or {}


class ExceptionHandlingMiddleware:
    """A small middleware wrapper that translates exceptions into HTTP-style error objects."""

    def __init__(self, handler: Callable[[Dict[str, Any]], Any]) -> None:
        self.handler = handler

    def __call__(self, request: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = self.handler(request)
            return {"ok": True, "data": result}
        except HTTPException as exc:
            return {"ok": False, "error": {"status_code": exc.status_code, "message": exc.message, "details": exc.details}}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": {"status_code": 500, "message": str(exc)}}
