"""Reusable FastAPI dependencies for gateway routes and middleware."""
from __future__ import annotations

from typing import Any

from fastapi import Request

from app.config.settings import Settings
from app.core.security import Principal
from app.exceptions.handlers import GatewayError
from app.responses import ResponseMetadata


def current_principal(request: Request) -> Principal:
    principal = getattr(request.state, "principal", None)
    if not principal:
        raise GatewayError(401, "UNAUTHENTICATED", "Authentication is required")
    return principal


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_request_context(request: Request) -> ResponseMetadata:
    return ResponseMetadata(
        request_id=getattr(request.state, "request_id", None),
        correlation_id=getattr(request.state, "correlation_id", None),
        trace_id=getattr(request.state, "trace_id", None),
        method=getattr(request, "method", None),
        path=getattr(getattr(request, "url", None), "path", None),
    )


def get_client_ip(request: Request) -> str | None:
    return getattr(request.state, "client_ip", None)


__all__ = ["current_principal", "get_client_ip", "get_request_context", "get_settings"]
