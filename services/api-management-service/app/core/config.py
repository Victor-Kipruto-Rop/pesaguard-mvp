from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_name: str = Field(default="PesaGuard API Gateway")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    trusted_hosts: list[str] = Field(default_factory=lambda: ["*"])
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    enable_metrics: bool = Field(default=True)
    enable_tracing: bool = Field(default=False)

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.getenv("APP_NAME", "PesaGuard API Gateway"),
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            trusted_hosts=os.getenv("TRUSTED_HOSTS", "*").split(",") if os.getenv("TRUSTED_HOSTS") else ["*"],
            cors_origins=os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"],
            enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
            enable_tracing=os.getenv("ENABLE_TRACING", "false").lower() == "true",
        )


settings = Settings.from_env()
