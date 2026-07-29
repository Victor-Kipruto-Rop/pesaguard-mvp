# Reporting views

## Purpose

Documents read-only SQL views used by `report-service` and `analytics-service` for regulatory and operational reporting. These sit on top of each service's own schema (never cross-schema joins at the database level — views are scoped within a single service's schema, consistent with database-per-service) and are the query surface reporting code targets instead of raw tables, so a table refactor doesn't necessarily break every report.

## `payments` schema

### `payments.v_daily_payment_summary`

Aggregates `payment_requests` by `organization_id`, `date_trunc('day', created_at)`, and `status`, with count and sum(amount). Backs the daily merchant settlement summary in `report-service`.

### `payments.v_provider_success_rate`

Rolling success/failure rate by provider (`mpesa`, `airtel_money`, `bank`) over a trailing 24-hour window, refreshed via a materialized view refreshed every 5 minutes by `scheduler-service` — used on the operational dashboard (`monitoring/dashboards/`) rather than computed live on every page load.

## `ledger` schema

### `ledger.v_trial_balance`

Standard trial balance view: sum of debits and credits per `ledger_accounts.id`, used by `ledger.close_accounting_period` (see [`../procedures/procedures-catalog.md`](../procedures/procedures-catalog.md)) and exposed read-only to compliance reporting.

### `ledger.v_period_end_balances`

Snapshot of account balances as of each closed accounting period — append-only by construction (each period close inserts new rows, never mutates prior periods), giving CBK-auditable historical balances without recomputing from the full transaction history each time.

## `fraud` schema

### `fraud.v_case_summary`

Case counts and resolution outcomes by `organization_id`, `decision`, and month — feeds the AML/CFT regulatory reporting templates referenced in [`../../security/policies/cbk-compliance.md#anti-money-laundering--countering-the-financing-of-terrorism-amlcft`](../../security/policies/cbk-compliance.md).

## `audit` schema

### `audit.v_privileged_actions`

Filters `audit_entries` to actions tagged `privileged` (role changes, manual reversal approvals, break-glass access grants) — the primary source for access-review reporting per [`../../security/policies/access-control-policy.md#review-cadence`](../../security/policies/access-control-policy.md#review-cadence).

## Convention

Views are prefixed `v_`; materialized views (refreshed on a schedule rather than computed live) are documented as such explicitly, since they carry a staleness window reporting consumers need to be aware of.

See also: [`../../architecture/cqrs-design.md`](../../architecture/cqrs-design.md), [`../schemas/ledger_schema.md`](../schemas/ledger_schema.md).
