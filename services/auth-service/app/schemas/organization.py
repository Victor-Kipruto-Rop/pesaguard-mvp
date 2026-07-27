from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=120)


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    owner_id: UUID
    is_active: bool
