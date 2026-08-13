from __future__ import annotations

from pydantic import BaseModel, field_validator

from shared.configuration.schemas.security import SecuritySettings


class SecurityValidator(BaseModel):
    security: SecuritySettings

    @field_validator("security")
    @classmethod
    def validate_security_secrets(cls, value: SecuritySettings) -> SecuritySettings:
        if len(value.jwt_secret.get_secret_value()) < 32:
            raise ValueError("JWT secret must be at least 32 characters")
        if len(value.encryption_key.get_secret_value()) < 32:
            raise ValueError("Encryption key must be at least 32 characters")
        return value
