from __future__ import annotations

from pydantic import BaseModel, Field, conint


class CacheSettings(BaseModel):
    default_ttl_seconds: int = Field(300, ge=1, description="Default cache TTL in seconds")
    max_items: int = Field(10000, ge=1, description="Maximum cache entries")
    eviction_policy: str = Field("LRU", description="Cache eviction policy")
    stale_after_seconds: int = Field(60, ge=0, description="Time after which cache entries are considered stale")
