"""Managed external resources with deterministic shutdown."""
from contextlib import asynccontextmanager

import httpx
import structlog
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config.settings import get_settings
from app.telemetry import configure_tracing


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = app.state.settings if hasattr(app.state, "settings") else get_settings()
    app.state.logger = structlog.get_logger("pesaguard.gateway")
    app.state.http = httpx.AsyncClient(timeout=settings.upstream_timeout_seconds, follow_redirects=False)
    app.state.redis = None
    app.state.db_engine: AsyncEngine | None = None
    if settings.redis_url:
        from redis.asyncio import Redis
        app.state.redis = Redis.from_url(settings.redis_url, decode_responses=True)
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
