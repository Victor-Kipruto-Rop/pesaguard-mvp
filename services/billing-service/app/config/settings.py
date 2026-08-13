from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, Field

from app.config.shared_config_bridge import SharedConfigBridge


class Settings(BaseModel):
    app_name: str = Field(default="billing-service")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    database_url: str = Field(default="sqlite:///./billing-service.db")
    secret_key: str = Field(default="development-only")
    payment_provider_url: str = Field(default="http://payments.local")

    @classmethod
    def from_env(cls, *, store: Any | None = None, secret_provider: Any | None = None) -> "Settings":
        bridge = SharedConfigBridge(store=store, secret_provider=secret_provider)
        payload = bridge.load_payload()
        resolved_payload = bridge.resolve_payload(payload)

        return cls(
            app_name=resolved_payload.get("app_name") or os.getenv("APP_NAME", cls.model_fields["app_name"].default),
            environment=resolved_payload.get("environment") or os.getenv("ENVIRONMENT", cls.model_fields["environment"].default),
            debug=resolved_payload.get("debug") if isinstance(resolved_payload.get("debug"), bool) else os.getenv("DEBUG", "false").lower() == "true",
            database_url=resolved_payload.get("database_url") or os.getenv("DATABASE_URL", cls.model_fields["database_url"].default),
            secret_key=resolved_payload.get("secret_key") or os.getenv("SECRET_KEY", cls.model_fields["secret_key"].default),
            payment_provider_url=resolved_payload.get("payment_provider_url") or os.getenv("PAYMENT_PROVIDER_URL", cls.model_fields["payment_provider_url"].default),
        )
