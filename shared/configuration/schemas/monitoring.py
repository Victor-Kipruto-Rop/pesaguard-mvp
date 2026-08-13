from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl, conint


class MonitoringSettings(BaseModel):
    prometheus_endpoint: HttpUrl = Field(..., description="Prometheus push gateway or scrape endpoint")
    enabled: bool = Field(True, description="Enable application monitoring")
    scrape_interval_seconds: int = Field(15, ge=5, description="Monitoring scrape interval")
    metrics_prefix: str = Field("pesaguard", description="Prometheus metrics prefix")

    @classmethod
    def model_validate(cls, value: dict) -> "MonitoringSettings":
        return super().model_validate(value)
