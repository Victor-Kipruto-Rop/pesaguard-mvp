from __future__ import annotations

from pydantic import BaseModel, Field, PostgresDsn, field_validator


class DatabaseSettings(BaseModel):
    url: PostgresDsn = Field(..., description="PostgreSQL connection URL")
    max_connections: int = Field(20, ge=1, le=200, description="Maximum DB connection pool size")
    connect_timeout: int = Field(10, ge=1, le=60, description="PostgreSQL connection timeout in seconds")

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: PostgresDsn) -> PostgresDsn:
        return value
