"""Managed external resources with deterministic shutdown."""
from contextlib import asynccontextmanager

import httpx
import structlog
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.cache import RedisCache
from app.clients import ServiceClient
from app.config.settings import get_settings
from app.core.resilience import CircuitBreaker
from app.telemetry import configure_tracing


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = app.state.settings if hasattr(app.state, "settings") else get_settings()
    app.state.logger = structlog.get_logger("pesaguard.gateway")
    client_options: dict[str, object] = {"timeout": settings.upstream_timeout_seconds, "follow_redirects": False}
    if settings.downstream_ca_bundle:
        client_options["verify"] = str(settings.downstream_ca_bundle)
    if settings.downstream_client_certificate and settings.downstream_client_key:
        client_options["cert"] = (str(settings.downstream_client_certificate), str(settings.downstream_client_key))
    app.state.http = httpx.AsyncClient(**client_options)
    app.state.service_client = ServiceClient(app.state.http, base_url="")
    app.state.redis = None
    app.state.redis_cache: RedisCache | None = None
    app.state.jwks_cache = {"keys": {}, "expires_at": 0.0}
    app.state.db_engine: AsyncEngine | None = None
    app.state.circuit_breaker = CircuitBreaker(settings.upstream_failure_threshold, settings.upstream_circuit_reset_seconds)
    if settings.redis_url:
        from redis.asyncio import Redis
        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        app.state.redis = redis_client
        app.state.redis_cache = RedisCache(redis_client)
    if settings.database_url:
        app.state.db_engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    configure_tracing(settings)
    try:
        yield
    finally:
        await app.state.http.aclose()
        if app.state.redis:
            await app.state.redis.aclose()
        if app.state.db_engine:
            await app.state.db_engine.dispose()
