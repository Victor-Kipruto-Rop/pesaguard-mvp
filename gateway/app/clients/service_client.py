"""Small, injectable HTTP client for future non-proxy gateway orchestration."""
from typing import Any

import httpx


class ServiceClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str) -> None:
        self._client, self._base_url = client, base_url.rstrip("/")

    async def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        response = await self._client.request(method, f"{self._base_url}/{path.lstrip('/')}", **kwargs)
        response.raise_for_status()
        return response
