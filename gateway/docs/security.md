# Security and production operations

## Deployment baseline

Terminate TLS at a managed load balancer, allow only that load balancer to reach the gateway, and set `PESAGUARD_TRUSTED_PROXY_IPS` to its private CIDRs. Supply a unique 32+ character JWT secret through a managed secret store — never a committed `.env` file. Rotate JWT signing material and API keys through a controlled overlap period (see [`../../security/secrets-management/rotation-schedule.md`](../../security/secrets-management/rotation-schedule.md)).

Production startup deliberately **fails** if any of the following hold: Redis is missing (`PESAGUARD_REDIS_URL` unset), API docs are enabled (`PESAGUARD_DOCS_ENABLED=true`), CORS/host wildcards are configured, or the JWT secret is weak or the default placeholder. This is intentional, fail-fast behavior — a gateway that silently started in a weak configuration is a worse outcome than one that refuses to boot. Redis provides distributed rate limiting; if it becomes unavailable at runtime, the gateway fails closed by default (`PESAGUARD_RATE_LIMIT_FAIL_OPEN=false`) rather than silently losing abuse protection.

## Access model

JWTs must contain `sub`, `exp`, `aud`, and `iss` claims; their `scope` claim is enforced at the service and HTTP-method level (`payments:read`, `payments:write`, and so on — see [`../../security/policies/access-control-policy.md`](../../security/policies/access-control-policy.md) for the platform-wide scope model). Production uses asymmetric `RS256` or `ES256` verification against a trusted JWKS endpoint (`PESAGUARD_JWT_JWKS_URL`), not the shared-secret `HS256` mode used for local development.

API keys are accepted only as SHA-256 digests in configuration (`PESAGUARD_API_KEY_HASHES`) — plaintext keys are never stored — and receive only the explicit scopes granted in `PESAGUARD_API_KEY_SCOPES`. `gateway:admin` is an intentional break-glass scope reserved for the admin router (`app/routes/admin.py`) and should be tightly controlled and rarely granted, consistent with the break-glass procedure in [`../../security/policies/access-control-policy.md#emergency-access`](../../security/policies/access-control-policy.md#emergency-access).

The gateway strips client-supplied `Authorization` and internal identity headers before forwarding a request downstream. It then supplies verified subject/scope context — derived from its own JWT/API-key validation, not trusted blindly from the client — only to the private service network. Never expose a downstream service directly to the internet; every domain service's Kubernetes `Service` is `ClusterIP`-only (see [`../../docs/deployment/kubernetes-guide.md#networking`](../../docs/deployment/kubernetes-guide.md#networking)).

## Idempotency

Payment creation (and other unsafe methods routed through the proxy) requires an `Idempotency-Key` header. The key is tenant/identity-scoped, cannot be reused with a different request payload (a mismatch is rejected, not silently accepted), and its response is replayed from Redis for `PESAGUARD_IDEMPOTENCY_TTL_SECONDS` (default 24 hours). A concurrent request with the same key is held behind a short-lived lock (`PESAGUARD_IDEMPOTENCY_LOCK_SECONDS`) rather than allowed to race. Clients must preserve this key across retries — generating a new key after an ambiguous/timeout response is the single most common cause of duplicate-charge incidents (see [`../../docs/runbooks/payment-service-runbook.md#suspected-duplicate-charge`](../../docs/runbooks/payment-service-runbook.md#suspected-duplicate-charge)).

## Rate limiting

Rate limiting uses an atomic Redis token bucket (`app/middleware/rate_limiter.py`). Tune the sustained request rate with `PESAGUARD_RATE_LIMIT_REQUESTS` and `PESAGUARD_RATE_LIMIT_WINDOW_SECONDS`, then set a deliberately bounded `PESAGUARD_RATE_LIMIT_BURST` above that sustained rate rather than leaving it unbounded. Production can also require downstream mTLS (`PESAGUARD_DOWNSTREAM_MTLS_REQUIRED=true`) by mounting a CA bundle and client certificate/key through the secret manager, for defense in depth on top of the Istio mesh's own mTLS enforcement.

## Reliability controls

Run at least two gateway replicas, Redis in highly available mode, and PostgreSQL managed backups where gateway persistence is enabled (see [`../../database/backups/backup-policy.md`](../../database/backups/backup-policy.md)). Wire up readiness probes and Prometheus alerting (`monitoring/alerts/`). The gateway retries only safe or idempotency-keyed requests, using bounded exponential backoff (`PESAGUARD_UPSTREAM_MAX_RETRIES`, default 2), and opens a service-local circuit after `PESAGUARD_UPSTREAM_FAILURE_THRESHOLD` repeated upstream failures, resetting after `PESAGUARD_UPSTREAM_CIRCUIT_RESET_SECONDS`. Clients making write requests should always supply a stable `Idempotency-Key` so a retried request during a circuit-open recovery window is safe by construction rather than merely likely-safe.

## Response hardening

`SecurityMiddleware` adds standard hardening headers to every response (see `app/middleware/security.py`) before `RequestContextMiddleware` finalizes logging/metrics — see [`architecture.md#request-flow`](architecture.md#request-flow) for where this sits in the overall middleware chain.

See also: [`environment.md`](environment.md), [`architecture.md`](architecture.md), [`../../docs/operations/gateway-runbook.md`](../../docs/operations/gateway-runbook.md), [`../../SECURITY.md`](../../SECURITY.md).
