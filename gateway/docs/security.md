# Security and production operations

## Deployment baseline

Terminate TLS at a managed load balancer, allow only that load balancer to reach the gateway, and set `PESAGUARD_TRUSTED_PROXY_IPS` to its private CIDRs. Supply a unique 32+ character JWT secret through a managed secret store. Rotate JWT signing material and API keys through a controlled overlap period.

Production startup deliberately fails if Redis is missing, API docs are enabled, CORS/host wildcards are used, or the JWT secret is weak. Redis provides distributed rate limits; if it becomes unavailable, the gateway fails closed by default rather than silently losing abuse protection.

## Access model

JWTs must contain `sub`, `exp`, `aud`, and `iss`; their `scope` claim is enforced at the service and HTTP-method level (`payments:read`, `payments:write`, and so on). Production uses asymmetric `RS256` or `ES256` verification and a trusted JWKS endpoint. API keys are accepted only as SHA-256 digests in configuration and receive only the explicit scopes in `PESAGUARD_API_KEY_SCOPES`. `gateway:admin` is an intentional break-glass scope and should be tightly controlled.

The gateway strips client-supplied authorization and internal identity headers before forwarding. It then supplies verified subject/scopes only to the private service network. Never expose a downstream service directly to the internet.

Payment creation requires an `Idempotency-Key`. The key is tenant/identity scoped, cannot be reused with a different payload, and is replayed from Redis for the configured retention period. Clients must preserve this key across retries.

Rate limiting uses an atomic Redis token bucket. Tune the sustained request rate with `PESAGUARD_RATE_LIMIT_REQUESTS` and `PESAGUARD_RATE_LIMIT_WINDOW_SECONDS`, then set a deliberately bounded `PESAGUARD_RATE_LIMIT_BURST`. Production can also require downstream mTLS by mounting a CA bundle and client certificate/key through the secret manager.

## Reliability controls

Use at least two gateway replicas, Redis in highly available mode, PostgreSQL managed backups where gateway persistence is enabled, readiness probes, and Prometheus alerting. The gateway retries only safe or idempotency-keyed requests, uses bounded exponential backoff, and opens a service-local circuit after repeated upstream failures. Clients making write requests should always supply a stable `Idempotency-Key`.
