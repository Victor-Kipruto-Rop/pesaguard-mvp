"""OpenAPI response models shared by gateway extensions."""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str | None = None
    details: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class SuccessResponse(BaseModel, Generic[T]):
    data: T
    request_id: str | None = Field(default=None)
