from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import Settings
from app.database.session import get_db, get_settings
from app.schemas.auth import ForgotPasswordRequest, LoginRequest, MessageResponse, RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    service = AuthService(db, settings)
    try:
        user, _ = service.register(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return service.to_user_response(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    service = AuthService(db, settings)
    try:
        _, tokens = service.login(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    service = AuthService(db, settings)
    try:
        tokens = service.refresh(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return tokens


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    service = AuthService(db, settings)
    service.forgot_password(str(payload.email))
    return MessageResponse(message="Password reset instructions sent")
