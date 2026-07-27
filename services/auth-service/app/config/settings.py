import os
from typing import List

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


class Settings(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    app_name: str = Field(default="PesaGuard Authentication Service", validation_alias=AliasChoices("app_name", "APP_NAME"))
    environment: str = Field(default="development", validation_alias=AliasChoices("environment", "ENVIRONMENT"))
    debug: bool = Field(default=False, validation_alias=AliasChoices("debug", "DEBUG"))
    database_url: str = Field(default="sqlite:///./auth-service.db", validation_alias=AliasChoices("database_url", "DATABASE_URL"))
    secret_key: str = Field(default="development-only-change-me-please-32", validation_alias=AliasChoices("secret_key", "SECRET_KEY"))
    jwt_algorithm: str = Field(default="HS256", validation_alias=AliasChoices("jwt_algorithm", "JWT_ALGORITHM"))
    jwt_issuer: str = Field(default="pesaguard", validation_alias=AliasChoices("jwt_issuer", "JWT_ISSUER"))
    jwt_audience: str = Field(default="pesaguard-api", validation_alias=AliasChoices("jwt_audience", "JWT_AUDIENCE"))
    access_token_ttl_minutes: int = Field(default=15, validation_alias=AliasChoices("access_token_ttl_minutes", "ACCESS_TOKEN_TTL_MINUTES"))
    refresh_token_ttl_days: int = Field(default=7, validation_alias=AliasChoices("refresh_token_ttl_days", "REFRESH_TOKEN_TTL_DAYS"))
    trusted_hosts: List[str] = Field(default_factory=lambda: ["*"], validation_alias=AliasChoices("trusted_hosts", "TRUSTED_HOSTS"))
    cors_origins: List[str] = Field(default_factory=lambda: ["*"], validation_alias=AliasChoices("cors_origins", "CORS_ORIGINS"))

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.environment == "production":
            if self.jwt_algorithm != "HS256" or len(self.secret_key) < 32:
                raise ValueError("production requires a strong HS256 secret or external OIDC integration")
            if "*" in self.trusted_hosts or "*" in self.cors_origins:
                raise ValueError("wildcard trusted hosts and CORS origins are not allowed in production")
        return self

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.getenv("APP_NAME", cls.model_fields["app_name"].default),
            environment=os.getenv("ENVIRONMENT", cls.model_fields["environment"].default),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            database_url=os.getenv("DATABASE_URL", cls.model_fields["database_url"].default),
            secret_key=os.getenv("SECRET_KEY", cls.model_fields["secret_key"].default),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", cls.model_fields["jwt_algorithm"].default),
            jwt_issuer=os.getenv("JWT_ISSUER", cls.model_fields["jwt_issuer"].default),
            jwt_audience=os.getenv("JWT_AUDIENCE", cls.model_fields["jwt_audience"].default),
            access_token_ttl_minutes=int(os.getenv("ACCESS_TOKEN_TTL_MINUTES", cls.model_fields["access_token_ttl_minutes"].default)),
            refresh_token_ttl_days=int(os.getenv("REFRESH_TOKEN_TTL_DAYS", cls.model_fields["refresh_token_ttl_days"].default)),
            trusted_hosts=os.getenv("TRUSTED_HOSTS", "*").split(",") if os.getenv("TRUSTED_HOSTS") else ["*"],
            cors_origins=os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"],
        )


settings = Settings.from_env()


def set_settings(value: Settings) -> None:
    """Replace process settings for an application-factory instance."""
    global settings
    settings = value


def get_current_settings() -> Settings:
    return settings
