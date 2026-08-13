from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl, constr


class IntegrationSettings(BaseModel):
    payment_provider_url: HttpUrl = Field(..., description="Primary payment provider endpoint")
    notification_provider_url: HttpUrl = Field(..., description="Primary notification provider endpoint")
    auth_provider_url: HttpUrl = Field(..., description="Authentication provider endpoint")
    retry_attempts: int = Field(3, ge=0, le=10, description="Integration retry attempts")
    retry_backoff_seconds: int = Field(5, ge=0, le=60, description="Integration retry backoff interval")
    default_timeout_seconds: int = Field(15, ge=1, description="Default integration call timeout seconds")
