from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl, conint


class TelemetrySettings(BaseModel):
    otlp_endpoint: HttpUrl = Field(..., description="OTLP collector endpoint")
    service_name: str = Field(..., min_length=1, description="Telemetry service name")
    traces_sample_rate: float = Field(0.2, ge=0.0, le=1.0, description="Tracing sample rate")
    metrics_enabled: bool = Field(True, description="Enable metrics export")
    traces_enabled: bool = Field(True, description="Enable tracing export")
