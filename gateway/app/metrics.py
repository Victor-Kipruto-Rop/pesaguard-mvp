"""Prometheus metric instruments, imported once per process."""
from prometheus_client import Counter, Histogram

REQUESTS = Counter("pesaguard_gateway_requests_total", "HTTP requests", ["method", "path", "status"])
LATENCY = Histogram("pesaguard_gateway_request_duration_seconds", "HTTP request duration", ["method", "path"])
