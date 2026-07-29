# Environment configuration

## Setup

Copy `.env.example` to `.env` for local development only — production configuration is injected via Vault-backed Kubernetes secrets, never a committed `.env` file (see [`../../docs/deployment/gateway-production-inputs.md`](../../docs/deployment/gateway-production-inputs.md)).

```bash
cp .env.example .env
```

All settings are typed and validated at startup via a `pydantic-settings` `Settings` object (`app/config/settings.py`) using the `PESAGUARD_` environment variable prefix — there is no scattered `os.environ` access anywhere else in the application. List-typed settings (e.g., `allowed_origins`) are supplied as JSON arrays in the environment variable value.

## Core settings

| Variable | Default | Notes |
|---|---|---|
| `PESAGUARD_ENVIRONMENT` | `development` | Gates production-only hardening checks at startup |
| `PESAGUARD_APP_NAME` | `PesaGuard API Gateway` | |
| `PESAGUARD_VERSION` | `0.1.0` | |
| `PESAGUARD_DEBUG` | `false` | |
| `PESAGUARD_HOST` / `PESAGUARD_PORT` | `0.0.0.0` / `8000` | |
| `PESAGUARD_LOG_LEVEL` | `INFO` | |
| `PESAGUARD_DOCS_ENABLED` | `true` | Must be `false` in production — enforced at startup |

## Network and CORS

| Variable | Default | Notes |
|---|---|---|
| `PESAGUARD_ALLOWED_ORIGINS` | `["http://localhost:3000"]` | Must be explicit (no wildcard) in production |
| `PESAGUARD_ALLOWED_HOSTS` | `["localhost","127.0.0.1","testserver"]` | Must be explicit (no wildcard) in production |
| `PESAGUARD_TRUSTED_PROXY_IPS` | `[]` | Private CIDRs of the load balancer terminating TLS in front of the gateway |
| `PESAGUARD_ALLOWED_IPS` / `PESAGUARD_DENIED_IPS` | `[]` | Optional IP allow/deny lists |

## Authentication

| Variable | Default | Notes |
|---|---|---|
| `PESAGUARD_JWT_SECRET` | dev placeholder | Must be 32+ characters and unique in production; used for `HS256` |
| `PESAGUARD_JWT_ALGORITHM` | `HS256` | Production should use `RS256`/`ES256` with `PESAGUARD_JWT_JWKS_URL` set |
| `PESAGUARD_JWT_JWKS_URL` | unset | JWKS endpoint for asymmetric verification |
| `PESAGUARD_JWT_JWKS_CACHE_SECONDS` | `300` | |
| `PESAGUARD_JWT_AUDIENCE` | `pesaguard-api` | |
| `PESAGUARD_JWT_ISSUER` | `pesaguard` | |
| `PESAGUARD_API_KEY_HASHES` | `[]` | SHA-256 digests of accepted API keys — never plaintext |
| `PESAGUARD_API_KEY_SCOPES` | `{}` | Maps each key's hash to its granted scopes |

## Rate limiting and idempotency

| Variable | Default | Notes |
|---|---|---|
| `PESAGUARD_RATE_LIMIT_REQUESTS` | `120` | Sustained request budget per window |
| `PESAGUARD_RATE_LIMIT_WINDOW_SECONDS` | `60` | |
| `PESAGUARD_RATE_LIMIT_BURST` | `0` | Additional burst allowance above the sustained rate |
| `PESAGUARD_RATE_LIMIT_FAIL_OPEN` | `false` | Production should leave this `false` — fail closed if Redis is unavailable |
| `PESAGUARD_IDEMPOTENCY_TTL_SECONDS` | `86400` | How long an `Idempotency-Key` response is replayed |
| `PESAGUARD_IDEMPOTENCY_LOCK_SECONDS` | `120` | Lock duration guarding concurrent requests with the same key |

## Request limits

| Variable | Default | Notes |
|---|---|---|
| `PESAGUARD_REQUEST_MAX_BYTES` | `1048576` (1 MiB) | |
| `PESAGUARD_ALLOWED_CONTENT_TYPES` | JSON/form/multipart | |

## Datastores and telemetry

| Variable | Default | Notes |
|---|---|---|
| `PESAGUARD_REDIS_URL` | unset | Required in production (startup fails without it) |
| `PESAGUARD_DATABASE_URL` | unset | Optional — gateway owns no business data (see [`architecture.md`](architecture.md)) |
| `PESAGUARD_OTEL_ENDPOINT` | unset | OpenTelemetry collector endpoint; instrumentation only activates if set |

## Downstream service URLs

Each proxied domain has its own origin URL setting — the gateway forwards to the *origin*, not a path prefix (see [`../README.md#api-routing`](../README.md#api-routing)):

`PESAGUARD_AUTH_SERVICE_URL`, `PESAGUARD_ORGANIZATIONS_SERVICE_URL`, `PESAGUARD_MERCHANTS_SERVICE_URL`, `PESAGUARD_PAYMENTS_SERVICE_URL`, `PESAGUARD_RECONCILIATION_SERVICE_URL`, `PESAGUARD_NOTIFICATIONS_SERVICE_URL`, `PESAGUARD_TRANSACTIONS_SERVICE_URL`, `PESAGUARD_REPORTS_SERVICE_URL`, `PESAGUARD_AUDIT_SERVICE_URL`.

A route whose service URL is unset returns `503 SERVICE_UNAVAILABLE` rather than failing unpredictably.

## Upstream resilience

| Variable | Default | Notes |
|---|---|---|
| `PESAGUARD_UPSTREAM_TIMEOUT_SECONDS` | `10` | |
| `PESAGUARD_UPSTREAM_MAX_RETRIES` | `2` | Applied only to safe/idempotency-keyed requests |
| `PESAGUARD_UPSTREAM_FAILURE_THRESHOLD` | `5` | Consecutive failures before a circuit opens |
| `PESAGUARD_UPSTREAM_CIRCUIT_RESET_SECONDS` | `30` | |
| `PESAGUARD_DOWNSTREAM_MTLS_REQUIRED` | `false` | If `true`, requires the three settings below |
| `PESAGUARD_DOWNSTREAM_CA_BUNDLE`, `PESAGUARD_DOWNSTREAM_CLIENT_CERTIFICATE`, `PESAGUARD_DOWNSTREAM_CLIENT_KEY` | unset | Filesystem paths, mounted from the secret manager |
| `PESAGUARD_SERVICE_HEALTH_CACHE_SECONDS` | `15` | |

## Production validation

Production configuration is enforced, not just recommended — the gateway deliberately **fails to start** if any of the following hold while `PESAGUARD_ENVIRONMENT=production`: `PESAGUARD_DOCS_ENABLED=true`, a wildcard in `PESAGUARD_ALLOWED_ORIGINS`/`PESAGUARD_ALLOWED_HOSTS`, a weak/default `PESAGUARD_JWT_SECRET`, or `PESAGUARD_REDIS_URL` unset. See [`security.md`](security.md#deployment-baseline).

See also: [`../README.md`](../README.md), [`architecture.md`](architecture.md), [`../../docs/deployment/gateway-production-inputs.md`](../../docs/deployment/gateway-production-inputs.md).
