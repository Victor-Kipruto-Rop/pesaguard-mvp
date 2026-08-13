from __future__ import annotations

from pydantic import BaseModel, Field, SecretStr, constr


class EmailSettings(BaseModel):
    smtp_host: str = Field(..., description="SMTP server host")
    smtp_port: int = Field(..., ge=1, le=65535, description="SMTP server port")
    username: str = Field(..., description="SMTP username")
    password: SecretStr = Field(..., description="SMTP password")
    default_from_address: constr(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$") = Field(..., description="Default email from address")
    use_tls: bool = Field(True, description="Use TLS for SMTP connections")
    webhook_endpoint: constr(min_length=1) | None = Field(None, description="Optional email delivery webhook endpoint")
