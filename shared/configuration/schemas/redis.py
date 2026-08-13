from __future__ import annotations

from pydantic import BaseModel, Field, RedisDsn, field_validator


class RedisSettings(BaseModel):
    url: RedisDsn = Field(..., description="Redis connection URL")
    cache_ttl_seconds: int = Field(300, ge=1, description="Default Redis cache TTL")
    max_connections: int = Field(50, ge=1, le=500, description="Redis maximum connection pool size")
    timeout_seconds: int = Field(5, ge=1, le=60, description="Redis operation timeout")

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: RedisDsn) -> RedisDsn:
        return value
