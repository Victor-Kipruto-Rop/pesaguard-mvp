from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl, conint


class GatewaySettings(BaseModel):
    host: str = Field("0.0.0.0", description="Gateway bind host")
    port: conint(ge=1, le=65535) = Field(8080, description="Gateway bind port")
    request_timeout_seconds: int = Field(30, ge=1, le=300, description="HTTP request timeout seconds")
    max_concurrent_requests: int = Field(500, ge=1, description="Maximum concurrent requests")
    allowed_origins: list[HttpUrl] = Field(default_factory=list, description="CORS allowed origins")
