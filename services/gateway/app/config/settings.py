from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, Field

from app.config.shared_config_bridge import SharedConfigBridge


class Settings(BaseModel):
    app_name: str = Field(default="gateway-service")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    auth_service_url: str = Field(default="http://auth.local")

    @classmethod
    def from_env(cls, *, store: Any | None = None, secret_provider: Any | None = None) -> "Settings":
        bridge = SharedConfigBridge(store=store, secret_provider=secret_provider)
        payload = bridge.load_payload()
        resolved_payload = bridge.resolve_payload(payload)

        return cls(
            app_name=resolved_payload.get("app_name") or os.getenv("APP_NAME", cls.model_fields["app_name"].default),
            environment=resolved_payload.get("environment") or os.getenv("ENVIRONMENT", cls.model_fields["environment"].default),
            debug=resolved_payload.get("debug") if isinstance(resolved_payload.get("debug"), bool) else os.getenv("DEBUG", "false").lower() == "true",
            api_host=resolved_payload.get("api_host") or os.getenv("API_HOST", cls.model_fields["api_host"].default),
            api_port=int(resolved_payload.get("api_port") or os.getenv("API_PORT", cls.model_fields["api_port"].default)),
            auth_service_url=resolved_payload.get("auth_service_url") or os.getenv("AUTH_SERVICE_URL", cls.model_fields["auth_service_url"].default),
        )
