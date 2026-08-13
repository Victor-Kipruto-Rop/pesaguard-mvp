from __future__ import annotations

import os
from typing import Optional

from pydantic import BaseModel, Field, ValidationError, field_validator

from shared.configuration.constants import ENVIRONMENT_VARIABLE, EnvironmentName, SUPPORTED_ENVIRONMENTS
from shared.configuration.exceptions.config_exception import ConfigurationError


class EnvironmentProfile(BaseModel):
    name: EnvironmentName = Field(..., description="Current deployment environment")

    @field_validator("name")
    @classmethod
    def validate_environment_name(cls, value: EnvironmentName) -> EnvironmentName:
        if value not in SUPPORTED_ENVIRONMENTS:
            raise ValueError(f"Unsupported environment: {value}")
        return value


def detect_environment() -> EnvironmentProfile:
    raw_environment = os.environ.get(ENVIRONMENT_VARIABLE, EnvironmentName.DEVELOPMENT.value)
    try:
        return EnvironmentProfile(name=EnvironmentName(raw_environment.lower()))
    except (ValidationError, ValueError) as exc:
        raise ConfigurationError(f"Invalid environment value '{raw_environment}'") from exc
