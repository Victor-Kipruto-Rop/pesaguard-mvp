"""Small typed cache adapter that keeps key names and TTLs explicit."""
from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

JsonValue = dict[str, Any]


class RedisCache:
    """Application-scoped cache adapter backed by the managed Redis client."""

    def __init__(self, redis: Any, namespace: str = "gateway") -> None:
        self._redis = redis
        self._namespace = namespace

    def key(self, name: str) -> str:
        return f"{self._namespace}:{name}"

    async def get(self, name: str) -> str | None:
        """Return the string value for the given key or None if it does not exist."""
        return await self._redis.get(self.key(name))

    async def get_bytes(self, name: str) -> bytes | None:
        """Return raw bytes for the given key if the Redis client is not decoding responses."""
        return await self._redis.get(self.key(name))

    async def set(self, name: str, value: str | bytes, ttl_seconds: int | None = None) -> None:
        """Store a raw string or bytes value in Redis with an optional expiration."""
        if ttl_seconds is None:
            await self._redis.set(self.key(name), value)
            return
        await self._redis.set(self.key(name), value, ex=ttl_seconds)

    async def get_json(self, name: str) -> JsonValue | None:
        """Load a JSON object from Redis and return it as a dict."""
        value = await self.get(name)
        if value is None:
            return None
        return json.loads(value)

    async def set_json(self, name: str, value: JsonValue, ttl_seconds: int | None = None) -> None:
        """Serialize and store a JSON object in Redis with optional TTL."""
        await self.set(name, json.dumps(value, separators=(",", ":"), ensure_ascii=False), ttl_seconds)

    async def delete(self, name: str) -> None:
        """Delete a key from Redis."""
        await self._redis.delete(self.key(name))

    async def exists(self, name: str) -> bool:
        """Return True when a key exists in Redis."""
        return bool(await self._redis.exists(self.key(name)))

    async def expire(self, name: str, ttl_seconds: int) -> bool:
        """Update the TTL for a key."""
        return bool(await self._redis.expire(self.key(name), ttl_seconds))

    async def ttl(self, name: str) -> int:
        """Return the remaining TTL for a key in seconds."""
        return await self._redis.ttl(self.key(name))

    async def set_if_not_exists(self, name: str, value: str | bytes, ttl_seconds: int) -> bool:
        """Set a value only if the key does not already exist."""
        return bool(await self._redis.set(self.key(name), value, nx=True, ex=ttl_seconds))

    async def get_or_set_json(self, name: str, value: JsonValue | Callable[[], JsonValue], ttl_seconds: int) -> JsonValue:
        """Return existing JSON from cache or compute, store, and return a new value."""
        existing = await self.get_json(name)
        if existing is not None:
            return existing
        payload = value() if callable(value) else value
        await self.set_json(name, payload, ttl_seconds)
        return payload

    async def increment(self, name: str, amount: int = 1) -> int:
        """Atomically increment a numeric key."""
        return await self._redis.incr(self.key(name), amount)

    async def decrement(self, name: str, amount: int = 1) -> int:
        """Atomically decrement a numeric key."""
        return await self._redis.decr(self.key(name), amount)

    async def eval(self, script: str, num_keys: int, *keys_and_args: Any) -> Any:
        """Execute a Lua script against Redis."""
        return await self._redis.eval(script, num_keys, *keys_and_args)
