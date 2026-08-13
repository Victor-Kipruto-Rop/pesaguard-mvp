from shared.http.middleware import ExceptionHandlingMiddleware, HTTPException
from shared.integrations.adapters import EventBusAdapter
from shared.observability.metrics import MetricsRegistry, Timer, timed
from shared.observability.tracing import TraceSpan, trace_span
from shared.uploads.file_transport import FileTransport


def test_metrics_and_timing():
    registry = MetricsRegistry()
    registry.increment("requests")
    registry.observe("latency", 0.25)
    snapshot = registry.snapshot()
    assert snapshot["counters"]["requests"] == 1
    assert snapshot["timings"]["latency"][0] == 0.25

    timer = Timer(registry, "db")
    assert timer.stop() >= 0.0

    @timed(registry, "handler")
    def handler():
        return "ok"

    assert handler() == "ok"


def test_tracing_span_and_http_middleware():
    with trace_span("payment.create") as span:
        assert isinstance(span, TraceSpan)
        span.set_attribute("tenant", "acme")
        assert span.attributes["tenant"] == "acme"

    middleware = ExceptionHandlingMiddleware(lambda request: request["value"])
    assert middleware({"value": 1}) == {"ok": True, "data": 1}
    assert middleware({"value": 2}) == {"ok": True, "data": 2}

    error_middleware = ExceptionHandlingMiddleware(lambda request: (_ for _ in ()).throw(HTTPException(400, "bad request")))
    result = error_middleware({"value": 1})
    assert result["ok"] is False
    assert result["error"]["status_code"] == 400


def test_file_transport_and_event_adapter(tmp_path):
    transport = FileTransport(str(tmp_path))
    path = transport.upload("receipt.pdf", b"pdf")
    assert transport.download("receipt.pdf") == b"pdf"
    assert transport.remove("receipt.pdf") is True

    adapter = EventBusAdapter("payments")
    received = []
    adapter.register_handler(lambda event: received.append(event["kind"]))
    adapter.publish({"kind": "payment.created"})
    assert received == ["payment.created"]
