import json
from unittest.mock import AsyncMock

import pytest

from app.cache.redis_cache import RedisCache


@pytest.fixture
def redis_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def cache(redis_client: AsyncMock) -> RedisCache:
    return RedisCache(redis_client, namespace="test")


@pytest.mark.asyncio
async def test_get_set_delete_round_trip(cache: RedisCache, redis_client: AsyncMock):
    redis_client.get.return_value = "value"

    result = await cache.get("key")

    assert result == "value"
    redis_client.get.assert_awaited_once_with("test:key")

    await cache.set("key", "value", ttl_seconds=10)
    redis_client.set.assert_awaited_once_with("test:key", "value", ex=10)

    await cache.delete("key")
    redis_client.delete.assert_awaited_once_with("test:key")


@pytest.mark.asyncio
async def test_json_helpers_serialize_and_deserialize(cache: RedisCache, redis_client: AsyncMock):
    payload = {"user_id": 123, "scopes": ["read", "write"]}
    redis_client.get.return_value = json.dumps(payload)

    result = await cache.get_json("session")

    assert result == payload
    await cache.set_json("session", payload, ttl_seconds=30)
    redis_client.set.assert_awaited_once_with("test:session", json.dumps(payload, separators=(",", ":"), ensure_ascii=False), ex=30)


@pytest.mark.asyncio
async def test_exists_expire_and_ttl(cache: RedisCache, redis_client: AsyncMock):
    redis_client.exists.return_value = 1
    redis_client.expire.return_value = 1
    redis_client.ttl.return_value = 90

    assert await cache.exists("token") is True
    redis_client.exists.assert_awaited_once_with("test:token")

    assert await cache.expire("token", 120) is True
    redis_client.expire.assert_awaited_once_with("test:token", 120)

    assert await cache.ttl("token") == 90
    redis_client.ttl.assert_awaited_once_with("test:token")


@pytest.mark.asyncio
async def test_set_if_not_exists_and_get_or_set_json(cache: RedisCache, redis_client: AsyncMock):
    redis_client.set.return_value = True
    redis_client.get.return_value = None

    assert await cache.set_if_not_exists("lock", "1", ttl_seconds=5) is True
    redis_client.set.assert_awaited_once_with("test:lock", "1", nx=True, ex=5)

    payload = {"result": "cached"}
    result = await cache.get_or_set_json("cache-key", payload, ttl_seconds=60)

    assert result == payload
    redis_client.set.assert_awaited_with("test:cache-key", json.dumps(payload, separators=(",", ":"), ensure_ascii=False), ex=60)


@pytest.mark.asyncio
async def test_increment_and_decrement(cache: RedisCache, redis_client: AsyncMock):
    redis_client.incr.return_value = 5
    redis_client.decr.return_value = 3

    assert await cache.increment("counter") == 5
    redis_client.incr.assert_awaited_once_with("test:counter", 1)

    assert await cache.decrement("counter", amount=2) == 3
    redis_client.decr.assert_awaited_once_with("test:counter", 2)
