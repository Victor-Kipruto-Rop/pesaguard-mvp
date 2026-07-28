"""Route metadata and environment variable bindings for the gateway."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator


_ALLOWED_HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}
_SERVICE_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
_ENV_VAR_NAME_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")


class ServiceDefinition(BaseModel):
    env_var: str
    health_path: str = "/health"
    health_method: str = "GET"
    methods: list[str] = Field(default_factory=lambda: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])

    model_config = {
        "extra": "forbid",
    }

    @field_validator("env_var")
    @classmethod
    def validate_env_var(cls, value: str) -> str:
        if not isinstance(value, str) or not _ENV_VAR_NAME_PATTERN.match(value):
            raise ValueError("env_var must be a valid environment variable name")
        return value

    @field_validator("health_path")
    @classmethod
    def validate_health_path(cls, value: str) -> str:
        if not isinstance(value, str) or not value.startswith("/"):
            raise ValueError("health_path must be an absolute path starting with '/'")
        return value

    @field_validator("health_method")
    @classmethod
    def validate_health_method(cls, value: str) -> str:
        method = value.upper()
        if method not in _ALLOWED_HTTP_METHODS:
            raise ValueError(f"health_method must be one of {_ALLOWED_HTTP_METHODS}")
        return method

    @field_validator("methods", mode="before")
    @classmethod
    def normalize_methods(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return value
        raise TypeError("methods must be a string or list of strings")

    @field_validator("methods")
    @classmethod
    def validate_methods(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("methods must contain at least one HTTP method")
        normalized: list[str] = []
        for method in value:
            if not isinstance(method, str):
                raise TypeError("each HTTP method must be a string")
            method_upper = method.upper()
            if method_upper not in _ALLOWED_HTTP_METHODS:
                raise ValueError(f"unsupported HTTP method '{method}'")
            normalized.append(method_upper)
        return normalized


class RouteConfig(BaseModel):
    version: str = Field(..., description="Route configuration version")
    services: dict[str, ServiceDefinition] = Field(..., description="Mapping of service key to service configuration")

    model_config = {
        "extra": "forbid",
    }

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        if value != "v1":
            raise ValueError("unsupported route config version")
        return value

    @field_validator("services", mode="before")
    @classmethod
    def normalize_services(cls, value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            services: dict[str, Any] = {}
            for service_name, service_value in value.items():
                if isinstance(service_value, str):
                    services[service_name] = {"env_var": service_value}
                elif isinstance(service_value, dict):
                    services[service_name] = service_value
                else:
                    raise TypeError("service definition must be a string or mapping")
            return services
        if isinstance(value, list):
            services = {}
            for item in value:
                if not isinstance(item, dict) or "name" not in item or "env_var" not in item:
                    raise TypeError("route services list must contain items with name and env_var")
                service_name = item["name"]
                service_data = {k: v for k, v in item.items() if k != "name"}
                services[service_name] = service_data
            return services
        raise TypeError("services must be a mapping or list of route definitions")

    @field_validator("services")
    @classmethod
    def validate_services(cls, value: dict[str, ServiceDefinition]) -> dict[str, ServiceDefinition]:
        if not value:
            raise ValueError("route config must declare at least one service")
        seen_env_vars: set[str] = set()
        for service_name, service_definition in value.items():
            if not isinstance(service_name, str) or not _SERVICE_NAME_PATTERN.match(service_name):
                raise ValueError(f"invalid service name '{service_name}'")
            if service_definition.env_var in seen_env_vars:
                raise ValueError(f"duplicate environment variable '{service_definition.env_var}' in route config")
            seen_env_vars.add(service_definition.env_var)
        return value

    @classmethod
    def load(cls, source: Path | str | None = None) -> "RouteConfig":
        config_path = Path(source) if source else Path(__file__).parent / "routes.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"route config file not found: {config_path}")
        with config_path.open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)
        if not isinstance(raw, dict):
            raise ValueError("route config must be a YAML mapping")
        return cls.model_validate(raw)

    @classmethod
    def load_default(cls) -> "RouteConfig":
        return cls.load(Path(__file__).parent / "routes.yaml")

    def service_names(self) -> tuple[str, ...]:
        return tuple(self.services)

    def service_definition(self, service: str) -> ServiceDefinition:
        return self.services[service]

    def env_var_for(self, service: str) -> str:
        return self.service_definition(service).env_var

    def health_path_for(self, service: str) -> str:
        return self.service_definition(service).health_path

    def health_method_for(self, service: str) -> str:
        return self.service_definition(service).health_method

    def supported_methods_for(self, service: str) -> tuple[str, ...]:
        return tuple(self.service_definition(service).methods)

    def service_url_from_environment(self, service: str, env: dict[str, str] | None = None) -> str | None:
        env = env or __import__("os").environ
        return env.get(self.env_var_for(service))
