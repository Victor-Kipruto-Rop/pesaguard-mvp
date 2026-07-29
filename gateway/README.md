# PesaGuard API Gateway

The gateway is the only public API entry point for the PesaGuard platform. It authenticates requests, enforces per-client rate limits, creates request/correlation IDs, applies response hardening, emits Prometheus metrics, and forwards versioned traffic to internal services. See [`docs/architecture.md`](docs/architecture.md) for the full request-flow diagram.

## Run locally

```bash
cd gateway
python3.13 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for interactive OpenAPI documentation (development only — `PESAGUARD_DOCS_ENABLED` must be `false` in production). Operational probes:

| Endpoint | Purpose |
|---|---|
| `GET /health` | Process health and version |
| `GET /live` | Kubernetes liveness probe |
| `GET /ready` | Dependency readiness probe (Redis, and database if configured) |
| `GET /metrics` | Prometheus scrape endpoint |

## API routing

`/api/v1/{auth\|organizations\|merchants\|payments\|reconciliation\|notifications}` is forwarded to the matching `/api/v1/<service>` path on its configured origin (`PESAGUARD_<SERVICE>_SERVICE_URL`). Configure each URL as the service **origin**, not a path prefix — the gateway appends the versioned path itself (see `app/config/routes.py`).

All non-public API routes require a valid bearer JWT (issuer/audience checked against `PESAGUARD_JWT_ISSUER`/`PESAGUARD_JWT_AUDIENCE`) or a SHA-256-hashed configured API key. A route whose downstream service URL is not configured intentionally returns `503 SERVICE_UNAVAILABLE`, avoiding a misleading success response before a downstream service actually exists.

## Project layout

```
gateway/
├── app/
│   ├── main.py              # Application factory (create_app)
│   ├── lifecycle.py          # Startup/shutdown (Redis, DB, telemetry init)
│   ├── config/                # Settings (typed, PESAGUARD_ prefixed) and route registration
│   ├── middleware/             # Request context, auth, idempotency, rate limiting, security headers
│   ├── routes/                  # health, auth_proxy, payment_proxy, proxy (generic), admin
│   ├── clients/                   # Outbound HTTP client to internal services
│   ├── core/                       # Security (JWT/API key), resilience (retry/circuit breaker), audit
│   ├── cache/                       # Redis cache wrapper
│   ├── exceptions/                   # Centralized exception handlers
│   ├── logging/                       # Structured logging + PII redaction
│   ├── telemetry.py, metrics.py        # OpenTelemetry and Prometheus instrumentation
│   └── schemas/, validators/, constants/
└── tests/                                # Config, health, rate limiter, redis cache/resilience, security, service client
```

## Configuration

All settings use the `PESAGUARD_` prefix and are read from environment variables or `.env` into a typed `Settings` object (`app/config/settings.py`) — see [`docs/environment.md`](docs/environment.md) for the full reference. Production rejects weak JWT secrets and wildcard CORS/host configuration at startup. Use managed secret injection in production; never commit `.env` files. See [`../docs/deployment/gateway-production-inputs.md`](../docs/deployment/gateway-production-inputs.md) for the Helm-level inputs required before deploying.

Read the [security and production operations guide](docs/security.md) before deploying. Production requires Redis, disables interactive docs, fails closed when distributed rate limiting is unavailable, applies scope-based authorization, and supports safe upstream retries/circuit breaking.

Operational response guidance is available in the [gateway runbook](../docs/operations/gateway-runbook.md).

## Deployment

For a local container stack, run `docker compose up --build` from the repository root. The gateway service will bind to port `8000` and expect Redis and PostgreSQL to be available through the compose network.

For non-development deployments:

1. Copy [gateway/.env.example](.env.example) to [gateway/.env](.env) and replace secrets.
2. Set `PESAGUARD_ENVIRONMENT=production` and disable docs with `PESAGUARD_DOCS_ENABLED=false`.
3. Ensure Redis is reachable at `PESAGUARD_REDIS_URL` and upstream services are configured via their `PESAGUARD_*_SERVICE_URL` values.
4. Mount secrets for mTLS and JWT verification when required.

## Verification

```bash
pytest tests
```

For a containerized smoke test, run:

```bash
docker compose up --build gateway
```
Test coverage: configuration validation, health endpoints, rate limiter behavior, Redis cache and resilience (circuit breaker), security header enforcement, and the outbound service client. See `pesaguard_gateway.egg-info/SOURCES.txt` for the full file manifest packaged by `pyproject.toml`.

For a local container stack, run `docker compose up --build` from the repository root. It uses the committed development defaults; create `gateway/.env` from the example and use your secret-management system for any non-development deployment.

See also: [`docs/architecture.md`](docs/architecture.md), [`docs/security.md`](docs/security.md), [`docs/environment.md`](docs/environment.md), [`../README.md`](../README.md).
