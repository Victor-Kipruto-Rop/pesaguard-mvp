# Architecture

## Design

The gateway is a **modular monolith**, not a microservice itself — a single FastAPI application (`app/main.py`) with four execution layers:

1. **Edge middleware** — request context, security headers/network restrictions, authentication, idempotency, rate limiting, response compression, CORS, and trusted-host enforcement (`app/middleware/`).
2. **Route selection** — versioned proxy routes plus dedicated health and admin routers (`app/routes/`).
3. **Proxy/client calls** — outbound calls to internal services with retry and circuit-breaking behavior (`app/clients/`, `app/core/resilience.py`).
4. **Managed external resources** — Redis (rate limiting, idempotency) and, optionally, PostgreSQL for future gateway-owned policy/configuration data (`app/cache/`, `app/config/settings.py`).

Middleware is ordered deliberately: request context runs first so every response is traceable end-to-end, security headers and network restrictions run before authentication, authenticated identities are then authorized by service/action scope, and the proxy layer applies circuit breaking and safe retries only after authorization succeeds. See the middleware stack construction in `app/main.py::create_app` for the literal registration order, and [`security.md`](security.md#access-model) for what each stage enforces.

## No business data ownership

The gateway owns no business data. PostgreSQL and Redis are optional managed dependencies used specifically for operational readiness (health/service-status caching), distributed rate limiting, and idempotency-key storage — not for domain state. All domain state lives in the services it proxies to (see the [service catalog](../../README.md#service-catalog)).

## Request flow

```
Client
  │  HTTPS
  ▼
TrustedHostMiddleware ──▶ CORSMiddleware ──▶ GZipMiddleware
  │
  ▼
RateLimitMiddleware (Redis token bucket)
  │
  ▼
IdempotencyMiddleware (Redis-backed replay for POST/PUT/PATCH)
  │
  ▼
AuthenticationMiddleware (JWT or API key → verified subject + scopes)
  │
  ▼
SecurityMiddleware (response hardening headers)
  │
  ▼
RequestContextMiddleware (request/correlation ID, structured logging)
  │
  ▼
Route (health / proxy / admin) ──▶ ServiceClient (app/clients/service_client.py)
  │                                     │  retries + circuit breaker (app/core/resilience.py)
  │                                     ▼
  │                              Internal service (PESAGUARD_<SERVICE>_SERVICE_URL)
  ▼
Response (headers stripped/hardened, metrics recorded)
```

Incoming credentials and internal identity headers are never forwarded downstream as-is; only the gateway's own verified identity context (subject, scopes, correlation ID) is passed to internal services, which sit entirely on the private service network — no internal service is ever exposed directly to the internet (see [`security.md`](security.md#access-model)).

## Observability

Every request is measured via `app/metrics.py` (Prometheus) and, when `PESAGUARD_OTEL_ENDPOINT` is configured, traced via `app/telemetry.py` (OpenTelemetry, `opentelemetry-instrumentation-fastapi`). The request/correlation ID assigned by `RequestContextMiddleware` is the join key across gateway logs, traces, and downstream service logs — see [`../../docs/architecture/overview.md#observability`](../../docs/architecture/overview.md#observability).

## Testability

`create_app(settings: Settings | None = None)` is a pure application factory, not a module-level side effect — this is what makes the gateway independently testable (`tests/`) with injected settings rather than requiring real environment variables or network access in unit tests.

See also: [`../README.md`](../README.md), [`security.md`](security.md), [`environment.md`](environment.md), [`../../docs/architecture/overview.md`](../../docs/architecture/overview.md).
