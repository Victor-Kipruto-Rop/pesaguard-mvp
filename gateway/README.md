# PesaGuard API Gateway

The gateway is the only public API entry point. It authenticates requests, enforces per-client rate limits, creates request/correlation IDs, applies response hardening, emits Prometheus metrics, and forwards versioned traffic to internal services.

## Run locally

```bash
cd gateway
python3.13 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs`. Operational probes are `GET /health`, `GET /live`, `GET /ready`, and `GET /metrics`.

## API routing

`/api/v1/{auth|organizations|merchants|payments|reconciliation|notifications}` is forwarded to the matching `/api/v1/<service>` path on its `PESAGUARD_<SERVICE>_SERVICE_URL`. Configure each URL as the service origin, not a path prefix. All non-public API routes require a valid bearer JWT (issuer/audience checked) or a SHA-256-hashed configured API key. Missing service URLs intentionally return `503 SERVICE_UNAVAILABLE`, avoiding a misleading success before a downstream service exists.

## Configuration

All settings use the `PESAGUARD_` prefix and are read from environment variables or `.env`. Production rejects weak JWT secrets and wildcard CORS/host configuration. Use managed secret injection in production; never commit `.env` files.

Read the [security and production operations guide](docs/security.md) before deploying. Production requires Redis, disables interactive docs, fails closed when distributed rate limiting is unavailable, applies scope-based authorization, and supports safe upstream retries/circuit breaking.

Operational response guidance is available in the repository [gateway runbook](../docs/operations/gateway-runbook.md).

## Verification

```bash
pytest tests
```

For a local container stack, run `docker compose up --build` from the repository root. It uses the committed development defaults; create `gateway/.env` from the example and use your secret-management system for any non-development deployment.
