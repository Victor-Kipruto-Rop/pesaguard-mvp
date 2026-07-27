"""Security audit event emitter; forwarding to SIEM is configured through structured logs."""
from typing import Any

import structlog


def emit(event: str, *, request_id: str | None, subject: str | None = None, outcome: str, **fields: Any) -> None:
    """Emit metadata only; callers must never provide credentials or request payloads."""
    structlog.get_logger("pesaguard.gateway.audit").info(
        "security_audit", audit_event=event, outcome=outcome, request_id=request_id, subject=subject, **fields
    )
