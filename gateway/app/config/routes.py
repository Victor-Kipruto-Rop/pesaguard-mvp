"""Route metadata and environment variable bindings for the gateway."""
from __future__ import annotations

import random
import re
from pathlib import Path
from typing import Any

import yaml
from app.constants import DEFAULT_API_PREFIX, DEFAULT_HTTP_METHODS
from pydantic import BaseModel, Field, field_validator, model_validator


_ALLOWED_HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}
_SERVICE_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
_ENV_VAR_NAME_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")


class UpstreamDefinition(BaseModel):
    env_var: str | None = None
    url: str | None = None
    weight: int = Field(default=1, ge=1)

    model_config = {
        "extra": "forbid",
    }

    @field_validator("env_var")
    @classmethod
    def validate_env_var(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or not _ENV_VAR_NAME_PATTERN.match(value):
            raise ValueError("env_var must be a valid environment variable name")
        return value

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or not (value.startswith("http://") or value.startswith("https://")):
            raise ValueError("url must be an absolute HTTP or HTTPS URL")
        return value.rstrip("/")

    @model_validator(mode="after")
    def validate_definition(self) -> "UpstreamDefinition":
        if not self.env_var and not self.url:
            raise ValueError("upstream definition must declare env_var or url")
        return self

    def resolve_url(self, env: dict[str, str] | None = None) -> str | None:
        env = env or __import__("os").environ
        if self.url:
            return self.url
        if self.env_var:
            value = env.get(self.env_var)
            return value.rstrip("/") if value else None
        return None


class ServiceDefinition(BaseModel):
    env_var: str | None = None
    upstreams: list[UpstreamDefinition] = Field(default_factory=list)
    health_path: str = "/health"
    health_method: str = "GET"
    methods: list[str] = Field(default_factory=lambda: list(DEFAULT_HTTP_METHODS))
    path_prefix: str = Field(default=DEFAULT_API_PREFIX)
    gateway_path: str | None = None
    group: str | None = None
    priority: int = 0
    fallback: bool = False
    websocket: bool = False
    cache_control: str | None = None
    response_headers: dict[str, str] = Field(default_factory=dict)
    response_body_rewrite: str | None = None

    model_config = {
        "extra": "forbid",
    }

    @field_validator("env_var")
    @classmethod
    def validate_env_var(cls, value: str | None) -> str | None:
        if value is None:
            return None
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

    @field_validator("path_prefix")
    @classmethod
    def validate_path_prefix(cls, value: str) -> str:
        if not isinstance(value, str) or not value.startswith("/"):
            raise ValueError("path_prefix must be an absolute path starting with '/'")
        return value.rstrip("/") or "/"

    @field_validator("gateway_path")
    @classmethod
    def validate_gateway_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or not value.startswith("/"):
            raise ValueError("gateway_path must be an absolute path starting with '/'")
        return value.rstrip("/") or "/"

    @field_validator("response_headers")
    @classmethod
    def validate_response_headers(cls, value: dict[str, str]) -> dict[str, str]:
        if not isinstance(value, dict):
            raise TypeError("response_headers must be a mapping of header names to values")
        normalized: dict[str, str] = {}
        for key, header_value in value.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("response_headers keys must be non-empty strings")
            if not isinstance(header_value, str):
                raise TypeError("response_headers values must be strings")
            normalized[key] = header_value
        return normalized

    @field_validator("response_body_rewrite")
    @classmethod
    def validate_response_body_rewrite(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError("response_body_rewrite must be a non-empty string")
        return value

    @model_validator(mode="after")
    def validate_service_definition(self) -> "ServiceDefinition":
        if self.upstreams:
            return self
        if self.env_var:
            self.upstreams = [UpstreamDefinition(env_var=self.env_var)]
            return self
        raise ValueError("service definition must include env_var or upstreams")

    def gateway_path_for(self, service: str) -> str:
        configured_path = self.gateway_path
        if configured_path:
            return configured_path.format(service=service) if "{service}" in configured_path else configured_path
        return f"/{service}"

    def path_prefix_for(self, service: str) -> str:
        return self.path_prefix

    def upstream_definitions(self) -> tuple[UpstreamDefinition, ...]:
        return tuple(self.upstreams)


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
        fallback_service: str | None = None
        for service_name, service_definition in value.items():
            if not isinstance(service_name, str) or not _SERVICE_NAME_PATTERN.match(service_name):
                raise ValueError(f"invalid service name '{service_name}'")
            if service_definition.fallback:
                if fallback_service is not None:
                    raise ValueError("route config may only declare a single fallback service")
                fallback_service = service_name
            env_vars: list[str] = []
            if service_definition.env_var:
                env_vars.append(service_definition.env_var)
            for upstream in service_definition.upstreams:
                if upstream.env_var and upstream.env_var != service_definition.env_var:
                    env_vars.append(upstream.env_var)
            for env_var in env_vars:
                if env_var in seen_env_vars:
                    raise ValueError(f"duplicate environment variable '{env_var}' in route config")
                seen_env_vars.add(env_var)
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
        return tuple(
            service_name
            for service_name, _ in sorted(
                self.services.items(),
                key=lambda item: self._service_sort_key(item[0], item[1]),
            )
        )

    def _service_sort_key(self, service_name: str, service_definition: ServiceDefinition) -> tuple[str, int, str]:
        return (
            service_definition.group or "",
            -service_definition.priority,
            service_name,
        )

    def service_definition(self, service: str) -> ServiceDefinition:
        return self.services[service]

    def env_var_for(self, service: str) -> str | None:
        return self.service_definition(service).env_var

    def upstream_definitions_for(self, service: str) -> tuple[UpstreamDefinition, ...]:
        service_definition = self.service_definition(service)
        if service_definition.upstreams:
            return tuple(service_definition.upstreams)
        if service_definition.env_var:
            return (UpstreamDefinition(env_var=service_definition.env_var),)
        return ()

    def health_path_for(self, service: str) -> str:
        return self.service_definition(service).health_path

    def health_method_for(self, service: str) -> str:
        return self.service_definition(service).health_method

    def supported_methods_for(self, service: str) -> tuple[str, ...]:
        return tuple(self.service_definition(service).methods)

    def path_prefix_for(self, service: str) -> str:
        return self.service_definition(service).path_prefix

    def gateway_path_for(self, service: str) -> str:
        configured_path = self.service_definition(service).gateway_path
        if configured_path:
            return configured_path.format(service=service) if "{service}" in configured_path else configured_path
        return f"/{service}"

    def supports_websocket_for(self, service: str) -> bool:
        return self.service_definition(service).websocket

    def cache_control_for(self, service: str) -> str | None:
        return self.service_definition(service).cache_control

    def response_headers_for(self, service: str) -> dict[str, str]:
        return self.service_definition(service).response_headers

    def response_body_rewrite_for(self, service: str) -> str | None:
        return self.service_definition(service).response_body_rewrite

    def service_url_from_environment(self, service: str, env: dict[str, str] | None = None) -> str | None:
        return self.select_upstream_for(service, env)

    def fallback_service_for(self, service: str) -> str | None:
        definition = self.service_definition(service)
        for candidate, metadata in self.services.items():
            if metadata.fallback and candidate != service:
                return candidate
        return None

    def select_upstream_for(self, service: str, env: dict[str, str] | None = None) -> str | None:
        env = env or __import__("os").environ
        upstreams = self.upstream_definitions_for(service)
        available: list[tuple[str, int]] = []
        for upstream in upstreams:
            upstream_url = upstream.resolve_url(env)
            if upstream_url:
                available.append((upstream_url.rstrip("/"), upstream.weight))
        if not available:
            return None
        urls, weights = zip(*available)
        return random.choices(urls, weights, k=1)[0]
