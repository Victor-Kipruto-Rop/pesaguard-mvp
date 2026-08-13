from __future__ import annotations

from pydantic import BaseModel, Field, conint


class SchedulerSettings(BaseModel):
    enabled: bool = Field(True, description="Enable scheduled background jobs")
    max_workers: int = Field(10, ge=1, le=100, description="Maximum number of scheduler workers")
    default_interval_seconds: int = Field(60, ge=10, description="Default schedule interval seconds")
    retry_attempts: int = Field(3, ge=0, description="Default retry attempts for jobs")
    retry_backoff_seconds: int = Field(5, ge=0, description="Default retry backoff interval")
