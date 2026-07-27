from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock

import pytest

from app.config.settings import Settings
from app.middleware.rate_limiter import RateLimitMiddleware, SLIDING_WINDOW_SCRIPT


def test_local_token_bucket_refuses_requests_after_burst():
    limiter = RateLimitMiddleware(lambda scope, receive, send: None)
    outcomes = [limiter._consume_local("client", limit=2, window_seconds=60)[0] for _ in range(3)]
    assert outcomes == [True, True, False]


@pytest.mark.asyncio
async def test_rate_limiter_uses_redis_cache_eval_when_available():
    redis_cache = AsyncMock()
    redis_cache.eval.return_value = [1, 4]
    settings = Settings(environment="test", rate_limit_fail_open=True)
    state = SimpleNamespace(settings=settings, redis=None, redis_cache=redis_cache, logger=SimpleNamespace(warning=print))
    request = SimpleNamespace(app=SimpleNamespace(state=state), url=SimpleNamespace(path="/api/v1/test"))

    limiter = RateLimitMiddleware(lambda scope, receive, send: None)
    allowed, remaining, backend = await limiter._consume(request, "ratelimit:client")

    assert allowed is True
    assert remaining == 4
    assert backend == "redis"
    redis_cache.eval.assert_awaited_once_with(SLIDING_WINDOW_SCRIPT, 1, "ratelimit:client", 1000, ANY, 60000, ANY)


@pytest.mark.asyncio
async def test_rate_limiter_falls_back_to_local_when_redis_cache_unavailable():
    redis_cache = AsyncMock()
    redis_cache.eval.side_effect = Exception("redis unavailable")
    settings = Settings(environment="test", rate_limit_fail_open=True)
    state = SimpleNamespace(settings=settings, redis=None, redis_cache=redis_cache, logger=SimpleNamespace(warning=print))
    request = SimpleNamespace(app=SimpleNamespace(state=state), url=SimpleNamespace(path="/api/v1/test"))

    limiter = RateLimitMiddleware(lambda scope, receive, send: None)
    allowed, remaining, backend = await limiter._consume(request, "ratelimit:client")

    assert allowed is True
    assert backend == "local"
