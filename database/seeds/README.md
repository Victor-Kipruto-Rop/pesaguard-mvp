# Database seeds

## Purpose

Seed data for local development, CI test databases, and staging — never real customer data (see [`../../docs/security/data-classification.md#internal--public`](../../docs/security/data-classification.md), and the non-production data rule in [`../../security/policies/kenya-dpa-compliance.md`](../../security/policies/kenya-dpa-compliance.md)).

## Structure

Each service's seeder lives at `services/<name>/app/database/seeders/<name>_seeder.py`, invoked via that service's `Makefile` (`make seed`). This directory holds cross-service reference data seeds — data that multiple services need consistently (e.g., a consistent set of test organizations/merchants so a local end-to-end payment flow actually works across services).

## Seeding order

Because services don't share a database but do have logical references (`organization_id`, `merchant_id`), seeding order matters for a coherent local environment:

1. `organization-service` — organizations, branches
2. `auth-service` — users, roles, memberships
3. `merchant-service`, `customer-service` — merchants and customers scoped to seeded organizations
4. `mpesa-service` / `airtel-money-service` / `bank-service` — sandbox provider credentials/configuration
5. Everything else — no strict ordering requirement

`scripts/seed-all.sh` runs this sequence against a local Docker Compose environment.

## Running

```bash
# single service
cd services/<name> && python -m app.database.seeders.<name>_seeder

# full local environment
./scripts/seed-all.sh
```

## Conventions

- Seed data uses obviously-fake identifiers (e.g., MSISDN `2547XXXXXXXX` test-range numbers issued by Safaricom's sandbox, not real subscriber ranges).
- Seeded amounts and volumes are chosen to exercise realistic edge cases (a merchant with a payment right at a fraud-scoring threshold, an organization with a soon-to-expire session) rather than uniform placeholder values.
- Seeds are idempotent — re-running a seeder against an already-seeded database updates/skips rather than duplicating.

See also: [`reference_data_seed.README.md`](reference_data_seed.README.md), [`../../docs/database/schema-conventions.md`](../../docs/database/schema-conventions.md).
