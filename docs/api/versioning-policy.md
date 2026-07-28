# API versioning policy

## Scheme

PesaGuard APIs are versioned in the URL path: `/api/v1/...`, `/api/v2/...`. Each service's router (`app/api/v1/`, `app/api/v2/`) implements one major version at a time; both can run concurrently during a deprecation window.

## When to bump a version

| Change | Version impact |
|---|---|
| Add an optional request field | None — same version |
| Add a response field | None — same version (clients must ignore unknown fields) |
| Add a new endpoint | None — same version |
| Remove or rename a field | New major version |
| Change a field's type or semantics | New major version |
| Change authentication/authorization requirements | New major version |
| Change an error response shape | New major version |

This mirrors the additive-only rule for Kafka event schemas — see [`event-schemas/schema-registry-config.md`](../../event-schemas/schema-registry-config.md).

## Deprecation process

1. New version ships alongside the old one; both are documented in `api-specs/openapi/`.
2. The old version's responses include a `Deprecation` header and `Sunset` date (RFC 8594).
3. Deprecation is announced in [`CHANGELOG.md`](../../CHANGELOG.md) and, for external/partner-facing routes, communicated via `developer-platform`.
4. Minimum deprecation window: 90 days for internal service-to-service routes, 180 days for gateway-public routes consumed by merchants.
5. The old version is removed only after usage telemetry (via `analytics-service`) confirms traffic has dropped to zero or all known consumers have confirmed migration.

## Gateway routing

The gateway forwards `/api/v{n}/<service>/...` to the matching version path on the target service. A service that hasn't yet implemented `v2` for a given route returns `404`, not a silent fallback to `v1` — version negotiation is explicit, never implicit.

## Current status

`/api/v0/*` legacy routes are deprecated as of `1.2.0` and scheduled for removal in `2.0.0` (see [`CHANGELOG.md`](../../CHANGELOG.md)). All services support `v1`; a subset (`payment-service`, `transaction-service`, `mpesa-service`) additionally support `v2` for the batch-payment and enhanced-idempotency features introduced in `1.4.0`.

See also: [`openapi-index.md`](openapi-index.md), [`../architecture/overview.md`](../architecture/overview.md).
