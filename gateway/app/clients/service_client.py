"""Robust, injectable HTTP client for upstream service orchestration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
from httpx import AsyncClient, HTTPStatusError, RequestError, Response, TimeoutException


class ServiceClientError(Exception):
    """Base exception for service client failures."""


class ServiceClientTimeout(ServiceClientError):
    """Indicates the upstream service did not respond in time."""


class ServiceClientResponseError(ServiceClientError):
    """Indicates a non-retryable response from the upstream service."""

    def __init__(self, status_code: int, content: str) -> None:
        super().__init__(f"upstream response error {status_code}")
        self.status_code = status_code
        self.content = content


class ServiceClientConnectionError(ServiceClientError):
    """Indicates a network or connection failure while communicating with upstream."""


class ServiceClient:
    """HTTP client wrapper that centralizes calls, retries, and error translation."""

    def __init__(self, client: AsyncClient, base_url: str | None = None, *, default_timeout: float = 10.0,
                 max_retries: int = 2, retry_backoff_seconds: float = 0.05,
                 retry_statuses: set[int] | None = None) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/") if base_url else ""
        self._default_timeout = default_timeout
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds
        self._retry_statuses = retry_statuses or {502, 503, 504}
        self._logger = logging.getLogger("pesaguard.gateway.service_client")

    def _build_url(self, path: str) -> str:
        if path.startswith(("http://", "https://")):
            return path
        if self._base_url:
            suffix = path.lstrip("/")
            return f"{self._base_url}/{suffix}" if suffix else self._base_url
        if not path:
            raise ValueError("path is required when no base_url is configured")
        return path if path.startswith("/") else f"/{path}"

    async def request(self, method: str, path: str, *, headers: dict[str, str] | None = None,
                      params: dict[str, Any] | None = None, json: Any | None = None,
                      content: Any | None = None, timeout: float | None = None,
                      raise_for_status: bool = True, **kwargs: Any) -> Response:
        """Send an HTTP request to the configured service endpoint."""
        if json is not None and content is not None:
            raise ValueError("Provide either json or content, not both.")

        url = self._build_url(path)
        request_timeout = timeout if timeout is not None else self._default_timeout
        headers = headers or {}
        attempt = 0
        last_error: ServiceClientError | None = None

        while attempt <= self._max_retries:
            attempt += 1
            try:
                response = await self._client.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=json,
                    content=content,
                    timeout=request_timeout,
                    **kwargs,
                )
                if raise_for_status:
                    response.raise_for_status()
                return response
            except TimeoutException as exc:
                self._logger.warning(
                    "service_request_timeout %s attempt=%s",
                    url,
                    attempt,
                    exc_info=exc,
                )
                last_error = ServiceClientTimeout(str(exc))
                if attempt > self._max_retries:
                    raise last_error from exc
            except HTTPStatusError as exc:
                status_code = exc.response.status_code
                self._logger.warning(
                    "service_request_http_error %s status=%s attempt=%s",
                    url,
                    status_code,
                    attempt,
                )
                if status_code in self._retry_statuses and attempt <= self._max_retries:
                    await asyncio.sleep(self._retry_backoff_seconds * (2 ** (attempt - 1)))
                    continue
                raise ServiceClientResponseError(status_code, exc.response.text) from exc
            except RequestError as exc:
                self._logger.warning(
                    "service_request_connection_error %s attempt=%s",
                    url,
                    attempt,
                    exc_info=exc,
                )
                last_error = ServiceClientConnectionError(str(exc))
                if attempt > self._max_retries:
                    raise last_error from exc
                await asyncio.sleep(self._retry_backoff_seconds * (2 ** (attempt - 1)))

        raise last_error or ServiceClientError("service request failed unexpectedly")

    async def get(self, path: str, **kwargs: Any) -> Response:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> Response:
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs: Any) -> Response:
        return await self.request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs: Any) -> Response:
        return await self.request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> Response:
        return await self.request("DELETE", path, **kwargs)
