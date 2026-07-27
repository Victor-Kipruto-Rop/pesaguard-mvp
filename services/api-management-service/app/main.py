from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_client import CollectorRegistry, Counter, Gauge, generate_latest

from app.api.router import router as api_router
from app.core.config import settings
from app.core.exceptions import APIError, api_exception_handler, validation_exception_handler
from app.middleware.request_context import RequestContextMiddleware
from app.middleware.security import SecurityHeadersMiddleware

registry = CollectorRegistry(auto_describe=True)
request_counter = Counter("gateway_requests_total", "Total gateway requests", registry=registry)
request_latency = Gauge("gateway_request_latency_seconds", "Gateway latency", registry=registry)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        debug=settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    app.add_exception_handler(APIError, api_exception_handler)
    app.add_exception_handler(Exception, lambda request, exc: api_exception_handler(request, APIError(str(exc), 500)))
    app.add_exception_handler(Exception, validation_exception_handler)

    app.include_router(api_router)

    @app.middleware("http")
    async def metrics_middleware(request, call_next):
        request_counter.inc()
        response = await call_next(request)
        request_latency.set(0.0)
        return response

    @app.get("/metrics")
    def metrics() -> str:
        return generate_latest(registry).decode("utf-8")

    return app


app = create_app()
