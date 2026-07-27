from fastapi import FastAPI

from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="PesaGuard Configuration Service", version="1.0.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/config")
    def config() -> dict[str, object]:
        current = settings.profiles.get(settings.profiles.keys().__iter__().__next__(), settings.profiles["development"])
        return {"profiles": {key: value.model_dump() for key, value in settings.profiles.items()}, "active": current.model_dump()}

    return app


app = create_app()
