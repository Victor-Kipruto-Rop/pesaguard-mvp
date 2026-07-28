"""Optional OpenTelemetry configuration; absence of a collector is non-fatal."""
from __future__ import annotations

from app.config.settings import Settings


def configure_tracing(settings: Settings) -> None:
    if not settings.otel_endpoint:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        return

    provider = TracerProvider(resource=Resource.create({"service.name": "pesaguard-gateway"}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_endpoint, insecure=True)))
    trace.set_tracer_provider(provider)


def instrument_application(app) -> None:
    """Install ASGI and HTTP client instrumentation once during application creation."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    except ImportError:
        return
    FastAPIInstrumentor.instrument_app(app, excluded_urls="health,live,ready,metrics")
