from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from shared.configuration.schema_generation import ServiceConfigSchemaGenerator


class SchemaRegistry:
    """Persist generated service config schemas for downstream services."""

    def __init__(self, output_dir: str | None = None) -> None:
        self.output_dir = Path(output_dir or ".schema_registry")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.generator = ServiceConfigSchemaGenerator()

    def publish(self, model_cls: type[BaseModel], *, service_name: str, version: str = "1.0") -> Path:
        schema = self.generator.generate(model_cls, service_name=service_name)
        schema["x-schema-version"] = version
        output_path = self.output_dir / f"{service_name}-{version}.json"
        output_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        return output_path
