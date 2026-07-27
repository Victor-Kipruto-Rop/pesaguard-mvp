"""Prometheus metric instruments, imported once per process."""
from prometheus_client import Counter, Histogram

REQUESTS = Counter("pesaguard_gateway_requests_total", "HTTP requests", ["method", "path", "status"])
LATENCY = Histogram("pesaguard_gateway_request_duration_seconds", "HTTP request duration", ["method", "path"])
UPSTREAM_REQUESTS = Counter("pesaguard_gateway_upstream_requests_total", "Upstream requests", ["service", "status"])
UPSTREAM_LATENCY = Histogram("pesaguard_gateway_upstream_duration_seconds", "Upstream request duration", ["service"])
UPSTREAM_RETRIES = Counter("pesaguard_gateway_upstream_retries_total", "Upstream retry attempts", ["service"])
RATE_LIMIT_DECISIONS = Counter("pesaguard_gateway_rate_limit_decisions_total", "Rate-limit outcomes", ["outcome", "backend"])
