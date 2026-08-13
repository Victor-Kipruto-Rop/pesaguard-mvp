from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl, conint


class APISettings(BaseModel):
    title: str = Field(..., description="API service title")
    version: str = Field(..., description="API version")
    openapi_url: HttpUrl = Field(..., description="OpenAPI documentation url")
    request_limit_per_minute: int = Field(1200, ge=1, description="Default API rate limit")
    page_size_default: int = Field(50, ge=1, le=1000, description="Default page size for paginated responses")
    page_size_max: int = Field(250, ge=1, le=2000, description="Maximum page size for paginated responses")
