from __future__ import annotations

from pydantic import BaseModel, Field, constr


class NotificationSettings(BaseModel):
    email_enabled: bool = Field(True, description="Enable notification email delivery")
    sms_enabled: bool = Field(False, description="Enable notification SMS delivery")
    email_from_address: constr(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$") = Field(..., description="Email sender address")
    sms_provider_api_key: str | None = Field(None, description="SMS provider API key")
    webhook_url: constr(min_length=1) | None = Field(None, description="Notifications webhook URL")
