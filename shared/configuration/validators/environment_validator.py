from __future__ import annotations

from pydantic import BaseModel, field_validator

from shared.configuration.constants import SUPPORTED_ENVIRONMENTS
from shared.configuration.environment import EnvironmentProfile


class EnvironmentValidator(BaseModel):
    environment: EnvironmentProfile

    @field_validator("environment")
    @classmethod
    def ensure_supported_environment(cls, value: EnvironmentProfile) -> EnvironmentProfile:
        if value.name not in SUPPORTED_ENVIRONMENTS:
            raise ValueError(f"Environment '{value.name}' is not supported")
        return value
