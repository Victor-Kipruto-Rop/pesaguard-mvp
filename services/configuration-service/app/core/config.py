from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, Field


class ServiceConfig(BaseModel):
    service_name: str = Field(default="configuration-service")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    redis_url: str = Field(default="redis://localhost:6379/0")
    database_url: str = Field(default="postgresql://postgres:postgres@localhost:5432/pesaguard")
    secret_key: str = Field(default="change-me")


class Settings(BaseModel):
    profiles: dict[str, ServiceConfig] = Field(default_factory=lambda: {
        "development": ServiceConfig(environment="development"),
        "testing": ServiceConfig(environment="testing"),
        "staging": ServiceConfig(environment="staging"),
        "production": ServiceConfig(environment="production"),
    })

    @classmethod
    def from_env(cls) -> "Settings":
        current_env = os.getenv("ENVIRONMENT", "development")
        profile = cls().profiles.get(current_env, cls().profiles["development"])
        return cls(profiles={**cls().profiles, current_env: ServiceConfig(
            service_name=profile.service_name,
            environment=current_env,
            debug=os.getenv("DEBUG", "false").lower() == "true",
            redis_url=os.getenv("REDIS_URL", profile.redis_url),
            database_url=os.getenv("DATABASE_URL", profile.database_url),
            secret_key=os.getenv("SECRET_KEY", profile.secret_key),
        )})


settings = Settings.from_env()
