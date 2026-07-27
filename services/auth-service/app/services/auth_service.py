from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import jwt
from sqlalchemy.orm import Session

from app.config.settings import Settings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from app.security.password import hash_password, verify_password


class AuthService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.user_repository = UserRepository(db)

    def register(self, payload: RegisterRequest) -> tuple[User, TokenResponse]:
        if self.user_repository.get_by_email(payload.email):
            raise ValueError("Email already registered")
        if self.user_repository.get_by_username(payload.username):
            raise ValueError("Username already taken")

        user = User(
            email=str(payload.email),
            username=payload.username,
            full_name=payload.full_name,
            password_hash=hash_password(payload.password),
        )
        self.user_repository.add(user)
        tokens = self._issue_tokens(user)
        return user, tokens

    def login(self, payload: LoginRequest) -> tuple[User, TokenResponse]:
        user = self.user_repository.get_by_email(str(payload.email))
        if not user or not verify_password(payload.password, user.password_hash):
            raise ValueError("Invalid credentials")
        if not user.is_active:
            raise ValueError("Account disabled")
        user.last_login_at = datetime.now(timezone.utc)
        self.user_repository.update(user)
        tokens = self._issue_tokens(user)
        return user, tokens

    def refresh(self, payload: RefreshRequest) -> TokenResponse:
        try:
            decoded = jwt.decode(
                payload.refresh_token, self.settings.secret_key, algorithms=[self.settings.jwt_algorithm],
                audience=self.settings.jwt_audience, issuer=self.settings.jwt_issuer,
                options={"require": ["exp", "sub", "aud", "iss", "type"]},
            )
        except Exception as exc:  # pragma: no cover - security boundary
            raise ValueError("Invalid refresh token") from exc

        user_id = decoded.get("sub")
        if not user_id or decoded.get("type") != "refresh":
            raise ValueError("Invalid refresh token")
        user = self.user_repository.get_by_id(UUID(user_id))
        if not user or not user.is_active:
            raise ValueError("Invalid refresh token")
        return self._issue_tokens(user)

    def forgot_password(self, email: str) -> None:
        user = self.user_repository.get_by_email(email)
        if not user:
            return
        # Placeholder for email sending; enterprise implementation would dispatch a task.

    def _issue_tokens(self, user: User) -> TokenResponse:
        access_exp = datetime.now(timezone.utc) + timedelta(minutes=self.settings.access_token_ttl_minutes)
        refresh_exp = datetime.now(timezone.utc) + timedelta(days=self.settings.refresh_token_ttl_days)
        scopes = self._scopes_for(user)
        common = {"sub": str(user.id), "aud": self.settings.jwt_audience, "iss": self.settings.jwt_issuer, "scope": " ".join(scopes)}
        access_payload = {**common, "type": "access", "exp": int(access_exp.timestamp())}
        refresh_payload = {**common, "type": "refresh", "exp": int(refresh_exp.timestamp())}
        access_token = jwt.encode(access_payload, self.settings.secret_key, algorithm=self.settings.jwt_algorithm)
        refresh_token = jwt.encode(refresh_payload, self.settings.secret_key, algorithm=self.settings.jwt_algorithm)
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    @staticmethod
    def _scopes_for(user: User) -> list[str]:
        """Default least-privilege scopes; membership/RBAC can extend this without changing token shape."""
        if user.is_superuser:
            return ["gateway:admin"]
        return ["auth:read", "organizations:read", "merchants:read", "payments:read", "payments:write", "reconciliation:read", "notifications:read"]

    def to_user_response(self, user: User) -> UserResponse:
        return UserResponse.model_validate(user)
