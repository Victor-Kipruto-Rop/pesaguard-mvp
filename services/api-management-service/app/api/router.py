from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")


@router.get("/health/live")
def liveness() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/health/ready")
def readiness() -> dict[str, str]:
    return {"status": "ready"}


@router.get("/gateway-info")
def gateway_info() -> dict[str, str]:
    return {"service": "api-gateway", "status": "operational"}
