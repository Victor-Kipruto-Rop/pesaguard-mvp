from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(min_length=12)
    full_name: Optional[str] = None
    username: str = Field(min_length=3, max_length=100)


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool
    email_verified: bool


class MessageResponse(BaseModel):
    message: str
