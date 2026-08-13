from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from shared.configuration.schema_registry import SchemaRegistry


class ExampleConfig(BaseModel):
    host: str


def test_schema_registry_publishes_service_schema(tmp_path: Path) -> None:
    registry = SchemaRegistry(str(tmp_path))
    output_path = registry.publish(ExampleConfig, service_name="billing", version="1.0")

    assert output_path.exists()
    assert "billing" in output_path.name
    assert "x-schema-version" in output_path.read_text(encoding="utf-8")
