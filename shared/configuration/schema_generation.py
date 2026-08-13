from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ServiceConfigSchemaGenerator:
    """Generate a schema for a service-specific configuration model."""

    def generate(self, model_cls: type[BaseModel], *, service_name: str) -> dict[str, Any]:
        schema = model_cls.model_json_schema()
        schema["title"] = self._service_title(service_name, model_cls.__name__)
        schema["x-service-name"] = service_name
        for _, value in schema.get("properties", {}).items():
            if isinstance(value, dict):
                value.setdefault("description", "Service-specific configuration")
        return schema

    @staticmethod
    def _service_title(service_name: str, model_name: str) -> str:
        prefix = "".join(part.capitalize() for part in service_name.split("-"))
        if model_name == "BaseModel":
            return f"{prefix}ServiceConfig"
        if model_name.endswith("Config"):
            return f"{prefix}{model_name}"
        return f"{prefix}{model_name}"
