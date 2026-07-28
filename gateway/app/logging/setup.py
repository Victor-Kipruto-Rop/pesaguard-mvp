"""Structured logging setup for the gateway application."""
import logging
import sys
from typing import Any

import structlog
from structlog.contextvars import merge_contextvars
from structlog.processors import JSONRenderer, TimeStamper
from structlog.stdlib import LoggerFactory

from app.logging.redaction import redact_sensitive_fields


def configure_logging(settings: Any) -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )
    structlog.configure(
        processors=[
            merge_contextvars,
            structlog.processors.add_log_level,
            TimeStamper(fmt="iso", utc=True),
            redact_sensitive_fields,
            JSONRenderer(),
        ],
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )
