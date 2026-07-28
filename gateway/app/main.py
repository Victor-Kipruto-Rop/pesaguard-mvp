"""Application factory for the PesaGuard API gateway."""
import logging
import sys
import re

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config.settings import Settings, get_settings
from app.exceptions import register_exception_handlers
from app.lifecycle import lifespan
from app.logging import redact_sensitive_fields
from app.middleware import AuthenticationMiddleware, IdempotencyMiddleware, RateLimitMiddleware, RequestContextMiddleware, SecurityMiddleware
from app.routes import admin_router, health_router, proxy_router
from app.routes.proxy import register_proxy_routes
from app.telemetry import instrument_application


def operation_id(route) -> str:
    """Create stable, method-aware OpenAPI operation IDs for multi-method proxy routes."""
    method = "_".join(sorted(route.methods or {"GET"})).lower()
    normalized_path = re.sub(r"[^a-zA-Z0-9]+", "_", route.path).strip("_")
    return f"{route.name}_{method}_{normalized_path}"


def configure_logging(settings: Settings) -> None:
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=getattr(logging, settings.log_level.upper(), logging.INFO))
    structlog.configure(
        processors=[structlog.contextvars.merge_contextvars, structlog.processors.add_log_level,
                    structlog.processors.TimeStamper(fmt="iso", utc=True), redact_sensitive_fields, structlog.processors.JSONRenderer()],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, settings.log_level.upper(), logging.INFO)),
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create an independently testable ASGI app."""
    settings = settings or get_settings()
    configure_logging(settings)
    docs_url = "/docs" if settings.docs_enabled else None
    app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan,
                  docs_url=docs_url, redoc_url="/redoc" if settings.docs_enabled else None,
                  openapi_url="/openapi.json" if settings.docs_enabled else None, generate_unique_id_function=operation_id)
    app.state.settings = settings
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
    app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True,
                       allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                       allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID", "X-Correlation-ID"])
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(IdempotencyMiddleware)
    app.add_middleware(AuthenticationMiddleware)
    app.add_middleware(SecurityMiddleware)
    # Starlette executes the most recently added middleware first.
    app.add_middleware(RequestContextMiddleware)
    app.include_router(health_router)
    app.include_router(proxy_router)
    register_proxy_routes(proxy_router, settings)
    app.include_router(admin_router)
    register_exception_handlers(app)
    if settings.otel_endpoint:
        instrument_application(app)
    return app


app = create_app()
