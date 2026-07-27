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

`/api/v1/{auth|organizations|merchants|payments|reconciliation|notifications}` is forwarded to its corresponding `PESAGUARD_<SERVICE>_SERVICE_URL`. All non-auth API routes require a valid bearer JWT (issuer/audience checked) or a SHA-256-hashed configured API key. Missing service URLs intentionally return `503 SERVICE_UNAVAILABLE`, avoiding a misleading success before a downstream service exists.

## Configuration

All settings use the `PESAGUARD_` prefix and are read from environment variables or `.env`. Production rejects weak JWT secrets and wildcard CORS/host configuration. Use managed secret injection in production; never commit `.env` files.

## Verification

```bash
pytest tests
```
