# `reference_data_seed` — static reference data

## Purpose

Seeds data that isn't test/demo data in the usual sense — it's static reference data every environment (including production) needs to function correctly, versioned here rather than treated as one-off application state. Distinct from [`README.md`](README.md)'s test/demo organization and user seeding, which only runs in non-production environments.

## What it seeds

| Reference set | Target schema | Notes |
|---|---|---|
| ISO 4217 currency codes | `shared` (referenced by all money-handling schemas) | KES as default/primary; others present for future multi-currency support |
| Provider registry (`mpesa`, `airtel_money`, `bank`) | `payments` | Canonical provider identifiers used across `payment_attempts.provider` |
| Standard role/permission templates | `role`, `permission` (via `role-service`/`permission-service`) | The baseline roles described in [`../../security/policies/access-control-policy.md#standard-roles-illustrative`](../../security/policies/access-control-policy.md) — organizations customize from this template, they don't start from nothing |
| CBK regulatory report type catalog | `report` | Report template identifiers consumed by `report-service`'s scheduler |
| Fraud rule catalog (rule IDs, not thresholds) | `fraud` | Static catalog of known rule types; actual thresholds are per-organization configuration, not seeded |

## Environments where this runs

Unlike `README.md`'s test-data seeding, `reference_data_seed` runs in **every** environment, including production, as part of initial environment setup and whenever a new reference value is added (e.g., a new supported provider) — it is idempotent and safe to re-run.

## Running

```bash
python -m scripts.seed_reference_data --environment <dev|staging|production>
```

Production runs of this script require the same change-review process as a migration (see [`../migrations/README.md#review-requirements`](../migrations/README.md)), since it can affect every service that reads these reference tables.

## Change process

Adding a new reference value (e.g., onboarding a new payment provider) is a PR to the seed data file itself, reviewed like any schema change, then applied via the script above — not a manual `INSERT` against any environment.

See also: [`README.md`](README.md), [`../../security/policies/access-control-policy.md`](../../security/policies/access-control-policy.md).
