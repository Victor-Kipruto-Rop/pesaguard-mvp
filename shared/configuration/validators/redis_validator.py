from __future__ import annotations

from pydantic import BaseModel, RedisDsn, field_validator

from shared.configuration.schemas.redis import RedisSettings


class RedisValidator(BaseModel):
    redis: RedisSettings

    @field_validator("redis")
    @classmethod
    def validate_redis_scheme(cls, value: RedisSettings) -> RedisSettings:
        if not value.url.startswith("redis://") and not value.url.startswith("rediss://"):
            raise ValueError("Redis URL must use redis:// or rediss:// scheme")
        return value
