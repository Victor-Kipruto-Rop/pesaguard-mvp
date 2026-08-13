from __future__ import annotations

from pydantic import BaseModel, PostgresDsn, field_validator

from shared.configuration.schemas.database import DatabaseSettings


class DatabaseValidator(BaseModel):
    database: DatabaseSettings

    @field_validator("database")
    @classmethod
    def validate_postgres_url(cls, value: DatabaseSettings) -> DatabaseSettings:
        if not value.url.startswith("postgresql://"):
            raise ValueError("Database URL must use postgresql scheme")
        return value
