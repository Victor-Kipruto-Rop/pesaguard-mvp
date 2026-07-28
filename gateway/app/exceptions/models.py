from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GatewayErrorCode(StrEnum):
    UNAUTHENTICATED = "UNAUTHENTICATED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    HTTP_ERROR = "HTTP_ERROR"
    SERVICE_NOT_FOUND = "SERVICE_NOT_FOUND"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"
    UPSTREAM_TIMEOUT = "UPSTREAM_TIMEOUT"
    UPSTREAM_CIRCUIT_OPEN = "UPSTREAM_CIRCUIT_OPEN"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    RATE_LIMITED = "RATE_LIMITED"
    RATE_LIMIT_UNAVAILABLE = "RATE_LIMIT_UNAVAILABLE"


class ProblemDetails(BaseModel):
    type: str = Field(default="about:blank")
    title: str
    status: int
    detail: str
    code: str | None = None
    instance: str | None = None
    request_id: str | None = None
    errors: Any | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")

    @classmethod
    def from_exception(
        cls,
        status: int,
        code: str | None,
        title: str,
        detail: str,
        request_id: str | None = None,
        instance: str | None = None,
        errors: Any | None = None,
        type_: str | None = None,
        **extensions: Any,
    ) -> "ProblemDetails":
        normalized_title = title.strip() or "Error"
        payload = {
            "type": type_ or f"about:blank#{normalized_title.lower().replace(' ', '_')}",
            "title": normalized_title,
            "status": status,
            "detail": detail,
            "request_id": request_id,
            "instance": instance,
            "errors": errors,
            "code": code,
            "extensions": extensions,
        }
        return cls(**{key: value for key, value in payload.items() if value is not None})


class GatewayErrorResponse(BaseModel):
    error: ProblemDetails
