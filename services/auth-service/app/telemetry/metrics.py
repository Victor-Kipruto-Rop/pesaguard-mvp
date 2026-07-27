from prometheus_client import CollectorRegistry, Counter, Gauge, generate_latest

registry = CollectorRegistry(auto_describe=True)
requests_total = Counter("auth_requests_total", "Total auth requests", registry=registry)
active_sessions = Gauge("auth_active_sessions", "Active auth sessions", registry=registry)


def metrics_payload() -> bytes:
    return generate_latest(registry)
