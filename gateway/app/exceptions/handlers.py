"""Consistent RFC-inspired API errors without leaking implementation details."""
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class GatewayError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: Any = None) -> None:
        self.status_code, self.code, self.message, self.details = status_code, code, message, details


def error_body(request: Request, code: str, message: str, details: Any = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message, "request_id": getattr(request.state, "request_id", None)}
    if details is not None:
        error["details"] = details
    return {"error": error}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(GatewayError)
    async def gateway_error(request: Request, exc: GatewayError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=error_body(request, exc.code, exc.message, exc.details))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content=error_body(request, "VALIDATION_ERROR", "Request validation failed", exc.errors()))

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 404:
            code = "NOT_FOUND"
        elif exc.status_code == 405:
            code = "METHOD_NOT_ALLOWED"
        else:
            code = "HTTP_ERROR"
        return JSONResponse(status_code=exc.status_code, content=error_body(request, code, str(exc.detail)))

    @app.exception_handler(Exception)
    async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        request.app.state.logger.exception("unhandled_exception", exc_info=exc)
        return JSONResponse(status_code=500, content=error_body(request, "INTERNAL_ERROR", "An unexpected error occurred"))
