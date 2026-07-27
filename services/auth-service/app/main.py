from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.organizations import router as organization_router
from app.config.settings import Settings, set_settings
from app.database.session import init_db
from app.middleware.security import SecurityHeadersMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    set_settings(settings)
    init_db(settings)

    app = FastAPI(title=settings.app_name, version="1.0.0", debug=settings.debug)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
    app.add_middleware(SecurityHeadersMiddleware)
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(organization_router, prefix="/api/v1")
    app.include_router(metrics_router, prefix="/api/v1")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
