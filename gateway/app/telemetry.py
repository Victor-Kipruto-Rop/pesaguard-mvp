"""Optional OpenTelemetry configuration; absence of a collector is non-fatal."""
from __future__ import annotations

from app.config.settings import Settings

FastAPIInstrumentor = None


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
    global FastAPIInstrumentor
    if FastAPIInstrumentor is None:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor as Instrumentor
        except ImportError:
            return
        FastAPIInstrumentor = Instrumentor
    FastAPIInstrumentor.instrument_app(app, excluded_urls="health,live,ready,metrics")
