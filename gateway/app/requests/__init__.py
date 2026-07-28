"""Typed request envelopes and metadata helpers for gateway-side request handling."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class RequestMetadata(BaseModel):
    """Normalized metadata captured for each inbound gateway request."""

    model_config = ConfigDict(extra="forbid")

    request_id: str | None = Field(default=None, min_length=1)
    correlation_id: str | None = Field(default=None, min_length=1)
    trace_id: str | None = Field(default=None, min_length=1)
    client_ip: str | None = Field(default=None, min_length=1)
    method: str | None = Field(default=None, min_length=1)
    path: str | None = Field(default=None, min_length=1)
    user_agent: str | None = Field(default=None, min_length=1)

    @field_validator("request_id", "correlation_id", "trace_id", "client_ip", "method", "path", "user_agent", mode="before")
    @classmethod
    def _strip_and_normalize(cls, value: Any, info: ValidationInfo) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            if info.field_name == "method":
                return normalized.upper()
            return normalized
        return value


class GatewayRequest(BaseModel):
    """A typed envelope for request payloads and their gateway metadata."""

    model_config = ConfigDict(extra="forbid")

    data: dict[str, Any] = Field(default_factory=dict)
    metadata: RequestMetadata = Field(default_factory=RequestMetadata)
    source: str | None = Field(default=None, min_length=1)

    @classmethod
    def from_request(cls, request: Any, *, data: dict[str, Any] | None = None, source: str | None = None) -> "GatewayRequest":
        headers = getattr(request, "headers", {}) or {}
        state = getattr(request, "state", None)
        url = getattr(request, "url", None)
        metadata = RequestMetadata(
            request_id=getattr(state, "request_id", None),
            correlation_id=getattr(state, "correlation_id", None),
            trace_id=getattr(state, "trace_id", None),
            client_ip=getattr(state, "client_ip", None),
            method=getattr(request, "method", None),
            path=getattr(url, "path", None),
            user_agent=headers.get("user-agent") or headers.get("User-Agent"),
        )
        return cls(data=data or {}, metadata=metadata, source=source)


__all__ = ["GatewayRequest", "RequestMetadata"]
