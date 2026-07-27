# API contracts

The PesaGuard gateway exposes versioned APIs under `/api/v1`. Interactive OpenAPI documentation is enabled only in development and test environments at `/docs` and `/openapi.json`.

| Public route | Purpose |
|---|---|
| `GET /health` | Process health and version |
| `GET /live` | Kubernetes liveness probe |
| `GET /ready` | Dependency readiness probe |
| `GET /metrics` | Prometheus scrape endpoint |
| `POST /api/v1/auth/login` | Authentication service proxy |
| `POST /api/v1/auth/refresh` | Authentication token refresh proxy |
| `/api/v1/{organizations,merchants,payments,reconciliation,notifications}` | Authenticated service proxies |

All non-public API calls require a bearer token or scoped API key. Write requests to `/api/v1/payments` require an `Idempotency-Key`. Internal services must publish their authoritative request/response OpenAPI contracts under `api-specs/openapi`; CI should validate compatibility before each release.
