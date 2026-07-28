from types import SimpleNamespace

from app.telemetry import configure_tracing, instrument_application


def test_configure_tracing_skips_when_endpoint_missing(monkeypatch):
    monkeypatch.delenv("PESAGUARD_OTEL_ENDPOINT", raising=False)
    configure_tracing(SimpleNamespace(otel_endpoint=None))


def test_instrument_application_uses_fastapi_instrumentor(monkeypatch):
    calls = []

    class DummyInstrumentor:
        @staticmethod
        def instrument_app(app, excluded_urls=None):
            calls.append((app, excluded_urls))

    import app.telemetry as telemetry_module

    monkeypatch.setattr(telemetry_module, "FastAPIInstrumentor", DummyInstrumentor)
    app = object()
    instrument_application(app)

    assert calls == [(app, "health,live,ready,metrics")]
