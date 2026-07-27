"""FastAPI dependencies used by routers that need a principal."""
from fastapi import Request

from app.core.security import Principal
from app.exceptions.handlers import GatewayError


def current_principal(request: Request) -> Principal:
    principal = getattr(request.state, "principal", None)
    if not principal:
        raise GatewayError(401, "UNAUTHENTICATED", "Authentication is required")
    return principal
