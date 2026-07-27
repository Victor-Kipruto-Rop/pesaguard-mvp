from fastapi import APIRouter
from fastapi.responses import Response

from app.telemetry.metrics import metrics_payload

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
def metrics() -> Response:
    return Response(content=metrics_payload(), media_type="text/plain")
