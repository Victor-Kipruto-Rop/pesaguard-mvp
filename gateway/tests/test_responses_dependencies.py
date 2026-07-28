from types import SimpleNamespace

import pytest
from fastapi import Request

from app.dependencies import current_principal, get_request_context, get_settings
from app.responses import ErrorDetail, GatewayResponse, ResponseMetadata, error_response, success_response


def test_success_response_builds_consistent_payload():
    payload = success_response({"status": "ok"}, request_id="req-1", correlation_id="corr-1", trace_id="trace-1")

    assert payload.success is True
    assert payload.data == {"status": "ok"}
    assert payload.metadata.request_id == "req-1"
    assert payload.metadata.correlation_id == "corr-1"
    assert payload.metadata.trace_id == "trace-1"


def test_error_response_contains_error_details():
    payload = error_response("INVALID_REQUEST", "The request body is invalid", request_id="req-2")

    assert payload.success is False
    assert payload.error is not None
    assert payload.error.code == "INVALID_REQUEST"
    assert payload.error.message == "The request body is invalid"
    assert payload.error.request_id == "req-2"


def test_request_context_dependency_assembles_metadata_from_request_state():
    request = SimpleNamespace(
        state=SimpleNamespace(request_id="req-3", correlation_id="corr-3", trace_id="trace-3", client_ip="203.0.113.10"),
        method="GET",
        url=SimpleNamespace(path="/api/v1/payments"),
    )

    context = get_request_context(request)

    assert context.request_id == "req-3"
    assert context.path == "/api/v1/payments"
    assert context.method == "GET"


def test_current_principal_dependency_requires_authenticated_request():
    request = SimpleNamespace(state=SimpleNamespace())

    with pytest.raises(Exception):
        current_principal(request)
