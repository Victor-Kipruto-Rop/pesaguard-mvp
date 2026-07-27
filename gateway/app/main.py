"""Application factory for the PesaGuard API gateway."""
import logging
import sys

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config.settings import Settings, get_settings
from app.exceptions import register_exception_handlers
from app.lifecycle import lifespan
from app.middleware import AuthenticationMiddleware, RateLimitMiddleware, RequestContextMiddleware, SecurityMiddleware
from app.routes import health_router, proxy_router


def configure_logging(settings: Settings) -> None:
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=getattr(logging, settings.log_level.upper(), logging.INFO))
    structlog.configure(
        processors=[structlog.contextvars.merge_contextvars, structlog.processors.add_log_level,
                    structlog.processors.TimeStamper(fmt="iso", utc=True), structlog.processors.JSONRenderer()],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, settings.log_level.upper(), logging.INFO)),
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create an independently testable ASGI app."""
    settings = settings or get_settings()
    configure_logging(settings)
    app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan,
                  docs_url="/docs", redoc_url="/redoc", openapi_url="/openapi.json")
    app.state.settings = settings
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
    app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True,
                       allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                       allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID", "X-Correlation-ID"])
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(AuthenticationMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.include_router(health_router)
    app.include_router(proxy_router)
    register_exception_handlers(app)
    return app


app = create_app()
