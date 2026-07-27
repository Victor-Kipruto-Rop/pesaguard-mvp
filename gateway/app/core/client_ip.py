"""Resolve a client address without trusting spoofable forwarding headers."""
from ipaddress import ip_address, ip_network

from starlette.requests import Request


def client_ip(request: Request) -> str:
    peer = request.client.host if request.client else "unknown"
    settings = request.app.state.settings
    try:
        trusted = any(ip_address(peer) in ip_network(network, strict=False) for network in settings.trusted_proxy_ips)
    except ValueError:
        trusted = False
    if trusted:
        forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if forwarded:
            return forwarded
    return peer
