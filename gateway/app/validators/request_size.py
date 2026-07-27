"""Reusable request-size validation."""

from app.exceptions.handlers import GatewayError


def validate_content_length(content_length: str | None, maximum: int) -> None:
    if content_length and int(content_length) > maximum:
        raise GatewayError(413, "PAYLOAD_TOO_LARGE", "Request body exceeds limit")
