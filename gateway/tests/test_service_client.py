from unittest.mock import AsyncMock, Mock

import pytest
from httpx import AsyncClient, HTTPStatusError, RequestError, Request, Response, TimeoutException

from app.clients.service_client import ServiceClient, ServiceClientConnectionError, ServiceClientResponseError, ServiceClientTimeout


@pytest.mark.asyncio
async def test_request_builds_url_and_returns_response():
    client = AsyncMock(spec=AsyncClient)
    response = Response(
        200,
        request=Request("GET", "https://api.example.com/v1/resource"),
        content=b"ok",
    )
    client.request.return_value = response
    service = ServiceClient(client, "https://api.example.com/v1")

    result = await service.get("resource")

    client.request.assert_awaited_once_with(
        "GET",
        "https://api.example.com/v1/resource",
        headers={"X-Request-Client": "pesaguard-gateway"},
        params=None,
        json=None,
        content=None,
        timeout=10.0,
    )
    assert result.status_code == 200


@pytest.mark.asyncio
async def test_request_raises_value_error_when_json_and_content_both_provided():
    client = AsyncMock(spec=AsyncClient)
    service = ServiceClient(client, "https://api.example.com")

    with pytest.raises(ValueError):
        await service.request("POST", "/resource", json={"a": 1}, content=b"data")


@pytest.mark.asyncio
async def test_request_retries_on_retryable_status_code_then_returns_response():
    client = AsyncMock(spec=AsyncClient)
    error_response = Response(
        503,
        request=Request("GET", "https://api.example.com/resource"),
        content=b"service unavailable",
    )
    http_error = HTTPStatusError("error", request=Mock(), response=error_response)
    second_response = Response(
        200,
        request=Request("GET", "https://api.example.com/resource"),
        content=b"ok",
    )
    client.request.side_effect = [http_error, second_response]

    service = ServiceClient(client, "https://api.example.com", max_retries=1)
    response = await service.get("resource")

    assert response.status_code == 200
    assert client.request.await_count == 2


@pytest.mark.asyncio
async def test_request_raises_response_error_for_non_retryable_status_code():
    client = AsyncMock(spec=AsyncClient)
    response = Response(
        400,
        request=Request("GET", "https://api.example.com/resource"),
        content=b"bad request",
    )
    client.request.side_effect = HTTPStatusError("error", request=Mock(), response=response)

    service = ServiceClient(client, "https://api.example.com", max_retries=2)

    with pytest.raises(ServiceClientResponseError) as exc:
        await service.get("resource")

    assert exc.value.status_code == 400
    assert "bad request" in exc.value.content
    assert client.request.await_count == 1


@pytest.mark.asyncio
async def test_request_retries_on_request_error_then_raises_when_exhausted():
    client = AsyncMock(spec=AsyncClient)
    client.request.side_effect = RequestError("connection failed")

    service = ServiceClient(client, "https://api.example.com", max_retries=1, retry_backoff_seconds=0)

    with pytest.raises(ServiceClientConnectionError):
        await service.get("resource")

    assert client.request.await_count == 2


@pytest.mark.asyncio
async def test_request_sets_trace_headers_when_trace_id_provided():
    client = AsyncMock(spec=AsyncClient)
    response = Response(200, request=Request("GET", "https://api.example.com/resource"), content=b"ok")
    client.request.return_value = response
    service = ServiceClient(client, "https://api.example.com")

    await service.get("resource", trace_id="trace-123")

    client.request.assert_awaited_once()
    assert client.request.await_args.kwargs["headers"]["X-Trace-ID"] == "trace-123"
    assert client.request.await_args.kwargs["headers"]["X-Correlation-ID"] == "trace-123"


@pytest.mark.asyncio
async def test_request_raises_timeout_after_retries():
    client = AsyncMock(spec=AsyncClient)
    client.request.side_effect = TimeoutException("timeout")

    service = ServiceClient(client, "https://api.example.com", max_retries=1, retry_backoff_seconds=0)

    with pytest.raises(ServiceClientTimeout):
        await service.get("resource")

    assert client.request.await_count == 2


@pytest.mark.asyncio
async def test_request_sets_gateway_identity_header():
    client = AsyncMock(spec=AsyncClient)
    response = Response(200, request=Request("GET", "https://api.example.com/resource"), content=b"ok")
    client.request.return_value = response
    service = ServiceClient(client, "https://api.example.com")

    await service.get("resource")

    assert client.request.await_args.kwargs["headers"]["X-Request-Client"] == "pesaguard-gateway"
