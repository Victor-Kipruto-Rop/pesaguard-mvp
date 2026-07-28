"""Consistent RFC-inspired API errors without leaking implementation details."""
from __future__ import annotations

from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions.models import GatewayErrorCode, GatewayErrorResponse, ProblemDetails


class GatewayError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Any = None,
        type_: str | None = None,
        instance: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = GatewayErrorCode(code).value if code in GatewayErrorCode.__members__ else code
        self.message = message
        self.details = details
        self.type = type_
        self.instance = instance


def build_problem_details(
    request: Request,
    status_code: int,
    code: str,
    detail: str,
    errors: Any | None = None,
    type_: str | None = None,
    instance: str | None = None,
    **extensions: Any,
) -> ProblemDetails:
    title = HTTPStatus(status_code).phrase if status_code in HTTPStatus._value2member_map_ else code.replace("_", " ").title()
    return ProblemDetails.from_exception(
        status=status_code,
        code=code,
        title=title,
        detail=detail,
        request_id=getattr(request.state, "request_id", None),
        instance=instance,
        errors=errors,
        type_=type_,
        **extensions,
    )


def error_body(request: Request, code: str, message: str, details: Any = None) -> dict[str, Any]:
    return GatewayErrorResponse(error=build_problem_details(request, HTTPStatus.INTERNAL_SERVER_ERROR, code, message, details)).model_dump()


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(GatewayError)
    async def gateway_error(request: Request, exc: GatewayError) -> JSONResponse:
        problem = build_problem_details(
            request,
            exc.status_code,
            exc.code,
            exc.message,
            errors=exc.details,
            type_=exc.type,
            instance=exc.instance,
        )
        return JSONResponse(status_code=exc.status_code, content=GatewayErrorResponse(error=problem).model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        problem = build_problem_details(
            request,
            422,
            GatewayErrorCode.VALIDATION_ERROR.value,
            "Request validation failed",
            errors=exc.errors(),
            type_="about:blank#unprocessable_entity",
            path=getattr(request, "url", None).path if getattr(request, "url", None) else None,
        )
        return JSONResponse(status_code=422, content=GatewayErrorResponse(error=problem).model_dump())

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 404:
            code = GatewayErrorCode.NOT_FOUND.value
        elif exc.status_code == 405:
            code = GatewayErrorCode.METHOD_NOT_ALLOWED.value
        else:
            code = GatewayErrorCode.HTTP_ERROR.value
        problem = build_problem_details(request, exc.status_code, code, str(exc.detail), type_="about:blank#http_error")
        return JSONResponse(status_code=exc.status_code, content=GatewayErrorResponse(error=problem).model_dump())

    @app.exception_handler(Exception)
    async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        logger = getattr(request.app.state, "logger", None)
        if logger is not None:
            logger.exception("unhandled_exception", exc_info=exc)
        problem = build_problem_details(
            request,
            500,
            GatewayErrorCode.INTERNAL_ERROR.value,
            "An unexpected error occurred",
            type_="about:blank#internal_error",
            errors={"exception": exc.__class__.__name__},
        )
        return JSONResponse(status_code=500, content=GatewayErrorResponse(error=problem).model_dump())
