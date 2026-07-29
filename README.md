# PesaGuard

PesaGuard is a modular payments and fraud-control platform with a public API gateway, internal services, and supporting infrastructure.

## Gateway deployment

The API gateway is the public entry point for the platform. It provides authentication, rate limiting, request context propagation, health probes, metrics, and upstream routing for internal services.

### Local development

```bash
cd gateway
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

The gateway will be available at http://localhost:8000 and exposes:
- GET /health
- GET /live
- GET /ready
- GET /metrics
- Swagger UI at /docs

### Docker Compose

From the repository root:

```bash
docker compose up --build gateway
```

This starts the gateway alongside PostgreSQL and Redis using the configuration in [docker-compose.yml](docker-compose.yml).

### Production guidance

- Copy [gateway/.env.example](gateway/.env.example) to [gateway/.env](gateway/.env) and replace secrets.
- Set `PESAGUARD_ENVIRONMENT=production` and disable docs with `PESAGUARD_DOCS_ENABLED=false`.
- Ensure Redis is reachable through `PESAGUARD_REDIS_URL`.
- Configure upstream services through the corresponding `PESAGUARD_*_SERVICE_URL` variables.
- Use a secret manager for JWT secrets, mTLS material, and other sensitive runtime values.

### Validation

```bash
cd gateway
pytest -q
```
