# `init.sql` — local PostgreSQL container initialization

## Purpose

Documents the initialization script mounted into the local `postgres` container's `/docker-entrypoint-initdb.d/` (see [`docker-compose.yml`](../../docker-compose.yml)), which runs automatically once, the first time the container's data volume is created.

## What it does

1. Creates one PostgreSQL database per service (or a shared `pesaguard` database with per-service schemas, depending on environment — local Docker Compose uses the shared-database/per-schema model for simplicity; staging/production use genuinely separate databases per service for stronger isolation, see [`../../docs/database/erd-overview.md#scope`](../../docs/database/erd-overview.md)).
2. Creates each service's application role with least-privilege grants, matching the roles created by [`../../database/migrations/0001_init.sql.README.md`](../../database/migrations/0001_init.sql.README.md).
3. Enables required extensions (`pgcrypto`, UUID generation support).
4. Runs each service's `0001_init.sql` baseline in sequence.

## Local-vs-production divergence

This script is explicitly a **local development convenience** — it is not what runs in staging or production, where each service's database is a separately provisioned RDS/Aurora instance created via Terraform (`infrastructure/terraform/`), and roles/permissions are managed via Vault-issued dynamic credentials rather than a static init script. Keeping local setup simple (one container, one init script) is worth the divergence, as long as the actual schema/migration chain (Alembic) is identical between environments — only the bootstrapping mechanism differs.

## Running

Automatic via `docker compose up --build` from the repository root. To reset a local database from scratch (re-running this script):

```bash
docker compose down -v   # removes the postgres data volume
docker compose up --build
```

## Troubleshooting

If a local database seems to be in a stale or inconsistent state, the first troubleshooting step is confirming `init.sql` actually ran (it only runs on volume *creation*, not on every container start) — check `docker compose logs postgres` for the initialization output, or reset per above.

See also: [`../../database/migrations/README.md`](../../database/migrations/README.md), [`../../docker-compose.yml`](../../docker-compose.yml).
