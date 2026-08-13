from __future__ import annotations

from pydantic import BaseModel, Field, SecretStr, constr, field_validator


class SecuritySettings(BaseModel):
    jwt_secret: SecretStr = Field(..., description="Primary JWT signing secret")
    encryption_key: SecretStr = Field(..., description="Primary encryption key for data at rest")
    allowed_hosts: list[constr(min_length=1)] = Field(default_factory=list, description="Trusted host names")
    password_salt_rounds: int = Field(12, ge=8, le=20, description="Work factor for password hashing")

    @field_validator("jwt_secret", "encryption_key")
    @classmethod
    def validate_secret_not_empty(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("Secret values cannot be empty")
        return value
