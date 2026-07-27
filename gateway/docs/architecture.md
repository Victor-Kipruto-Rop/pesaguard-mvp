# Architecture

The modular-monolith gateway has four execution layers: edge middleware, route selection, proxy/client calls, and managed external resources. Middleware is ordered so rate limiting executes before authentication work, while request context records all outcomes. Internal services receive only validated request/correlation metadata and authenticated subject/scopes; raw credentials are not forwarded.

The gateway owns no business data. PostgreSQL and Redis are optional managed dependencies for operational readiness, distributed rate limiting, and future gateway-owned policy/configuration.

At the edge, request context runs first so every response is traceable. Security headers and network restrictions run before authentication. Authenticated identities are authorized by service/action scope, then the proxy applies circuit breaking and safe retries. Incoming credentials and identity headers are never forwarded; only gateway-verified identity context is sent to private upstream services.
