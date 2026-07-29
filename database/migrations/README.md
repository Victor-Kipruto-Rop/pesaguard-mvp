# Database migrations

## Scope

This directory documents cross-service migration conventions. Each service manages its own Alembic migration chain under `services/<name>/app/database/migrations/` — there is no single platform-wide migration chain, consistent with database-per-service (see [`../../architecture/domain-driven-design.md`](../../architecture/domain-driven-design.md)).

## Convention

- One Alembic chain per service, versioned independently.
- Migration files: `<revision>_<description>.py`, auto-generated via `alembic revision --autogenerate -m "<description>"` from within the service directory, then hand-reviewed — autogenerate reliably catches column/table changes but not renames (it will otherwise generate a drop+add instead of a rename) and not constraint intent.
- Every migration implements `downgrade()`, unless the change is a documented, irreversible data cleanup — in which case `downgrade()` raises `NotImplementedError` with an explanation, rather than silently being a no-op.
- Migrations never edit a revision that has already merged to `main` — a mistake is fixed with a new forward migration, keeping the chain an honest history of what actually ran in each environment.

## Execution

Migrations run automatically via an init container ahead of the new application version receiving traffic (see [`../../docs/deployment/kubernetes-guide.md`](../../docs/deployment/kubernetes-guide.md)). Locally:

```bash
cd services/<service-name>
alembic upgrade head
```

## Review requirements

A migration PR requires review from a database-owning lead when it:

- Adds a `NOT NULL` column to a large existing table (needs a safe multi-step rollout: add nullable → backfill → add constraint, not a single blocking migration)
- Adds or changes a constraint covered in [`../constraints/constraints-catalog.md`](../constraints/constraints-catalog.md)
- Touches a payment-critical schema (`payments`, `ledger`, `transaction`)

## Zero-downtime pattern

For any change that could lock a large table or briefly break compatibility with the currently-running application version (which a rolling deploy guarantees will exist briefly alongside the new one):

1. Additive migration ships first (new nullable column, new table) — compatible with both old and new app code.
2. New application version ships, using the new schema.
3. A follow-up migration removes anything the old version needed but the new version doesn't, only after the old version is fully rolled out.

See also: [`0001_init.sql.README.md`](0001_init.sql.README.md), [`../../CONTRIBUTING.md#database-migrations`](../../CONTRIBUTING.md#database-migrations).
