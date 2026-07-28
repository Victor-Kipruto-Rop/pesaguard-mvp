"""Typed response envelopes and helpers for gateway routes and middleware."""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ResponseMetadata(BaseModel):
    """Standard metadata attached to successful gateway responses."""

    model_config = ConfigDict(extra="forbid")

    request_id: str | None = Field(default=None, min_length=1)
    correlation_id: str | None = Field(default=None, min_length=1)
    trace_id: str | None = Field(default=None, min_length=1)
    method: str | None = Field(default=None, min_length=1)
    path: str | None = Field(default=None, min_length=1)


class ErrorDetail(BaseModel):
    """Error detail payload for structured gateway failures."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    request_id: str | None = Field(default=None, min_length=1)
    details: dict[str, Any] | None = None


class GatewayResponse(BaseModel, Generic[T]):
    """Envelope used for successful gateway responses."""

    model_config = ConfigDict(extra="forbid")

    success: bool = True
    data: T
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)


class GatewayErrorResponse(BaseModel):
    """Envelope used for failed gateway responses."""

    model_config = ConfigDict(extra="forbid")

    success: bool = False
    error: ErrorDetail


def success_response(data: T, *, request_id: str | None = None, correlation_id: str | None = None, trace_id: str | None = None) -> GatewayResponse[T]:
    return GatewayResponse(
        data=data,
        metadata=ResponseMetadata(request_id=request_id, correlation_id=correlation_id, trace_id=trace_id),
    )


def error_response(code: str, message: str, *, request_id: str | None = None, details: dict[str, Any] | None = None) -> GatewayErrorResponse:
    return GatewayErrorResponse(error=ErrorDetail(code=code, message=message, request_id=request_id, details=details))


__all__ = ["ErrorDetail", "GatewayErrorResponse", "GatewayResponse", "ResponseMetadata", "error_response", "success_response"]
