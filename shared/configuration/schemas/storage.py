from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl, constr


class StorageSettings(BaseModel):
    provider: constr(min_length=1) = Field("local", description="Storage provider name")
    base_path: constr(min_length=1) = Field("/var/lib/pesaguard/storage", description="Local storage base path")
    endpoint: HttpUrl | None = Field(None, description="Remote storage endpoint URL")
    max_file_size_mb: int = Field(100, ge=1, description="Maximum storage file size in megabytes")
