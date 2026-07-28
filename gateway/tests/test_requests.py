from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.requests import GatewayRequest, RequestMetadata


def test_request_metadata_normalizes_and_validates_values():
    metadata = RequestMetadata(
        request_id="  req-001  ",
        correlation_id=" corr-002 ",
        trace_id=" trace-003 ",
        client_ip=" 203.0.113.8 ",
        method=" get ",
        path=" /api/v1/payments ",
        user_agent="  premium-client/1.0  ",
    )

    assert metadata.request_id == "req-001"
    assert metadata.correlation_id == "corr-002"
    assert metadata.trace_id == "trace-003"
    assert metadata.client_ip == "203.0.113.8"
    assert metadata.method == "GET"
    assert metadata.path == "/api/v1/payments"
    assert metadata.user_agent == "premium-client/1.0"


def test_gateway_request_builds_from_request_like_object():
    request = SimpleNamespace(
        method="POST",
        url=SimpleNamespace(path="/api/v1/payments"),
        headers={"user-agent": "demo-client/2.0"},
        state=SimpleNamespace(request_id="req-100", correlation_id="corr-100", trace_id="trace-100", client_ip="198.51.100.9"),
        scope={"client": ("198.51.100.7", 1234)},
    )

    envelope = GatewayRequest.from_request(request, data={"amount": 150}, source="external")

    assert envelope.data == {"amount": 150}
    assert envelope.metadata.request_id == "req-100"
    assert envelope.metadata.correlation_id == "corr-100"
    assert envelope.metadata.trace_id == "trace-100"
    assert envelope.metadata.client_ip == "198.51.100.9"
    assert envelope.metadata.path == "/api/v1/payments"
    assert envelope.metadata.method == "POST"
    assert envelope.metadata.user_agent == "demo-client/2.0"


def test_gateway_request_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        GatewayRequest(data={"amount": 25}, metadata={"request_id": "req-1"}, unexpected=True)
