# Database procedures catalog

## Purpose

Documents stored procedures used for batch/administrative operations that are either too heavy to run as ordinary application-layer transactions or need to run with atomicity guarantees a multi-statement ORM operation can't cleanly provide.

## `reconciliation` schema

### `reconciliation.run_daily_settlement_match(p_provider TEXT, p_date DATE)`

Invoked nightly by `reconciliation-service` (via `scheduler-service`) to match `transactions` against imported provider settlement statement rows for a given provider and date, flagging unmatched records into `reconciliation.variances` for review. Runs as a single procedure (not a multi-round-trip application job) so a partial failure doesn't leave the day's reconciliation half-applied.

```sql
CALL reconciliation.run_daily_settlement_match('mpesa', '2026-07-28');
```

Emits a `reconciliation.completed.v1` event on success and `reconciliation.variance_detected.v1` per flagged row, consumed by `fraud-service` and the compliance dashboard.

## `ledger` schema

### `ledger.close_accounting_period(p_organization_id UUID, p_period DATE)`

Locks further postings into a closed period for an organization, computing and persisting period-end balances. Requires the caller to hold the `ledger:close_period` scope (see [`../../security/policies/access-control-policy.md`](../../security/policies/access-control-policy.md)) — enforced by the calling service, not the procedure itself, but the procedure additionally validates the caller-supplied role token hash as defense in depth.

### `ledger.reverse_transaction(p_transaction_id UUID, p_reason TEXT, p_actor_id UUID)`

Creates the compensating ledger entries for a transaction reversal atomically — never called directly from application code without going through `transaction-service`'s reversal workflow, which is responsible for the cross-service orchestration (see [`../../docs/runbooks/payment-service-runbook.md#suspected-duplicate-charge`](../../docs/runbooks/payment-service-runbook.md#suspected-duplicate-charge)).

## `audit` schema

### `audit.verify_chain_integrity(p_from TIMESTAMPTZ, p_to TIMESTAMPTZ)`

Recomputes the hash chain (see [`../functions/functions-catalog.md#compute_hashprev_hash-text-payload-jsonb-returns-text`](../functions/functions-catalog.md)) across a date range and returns any entries where the stored hash doesn't match the recomputed value — the primary tool used in an audit or suspected-tampering investigation. Read-only; makes no writes.

## Usage policy

Stored procedures are used sparingly and only where atomicity or performance genuinely requires database-side execution — business logic defaults to living in `app/services/`, not in the database, per [`../../architecture/domain-driven-design.md#anti-patterns-avoided`](../../architecture/domain-driven-design.md#anti-patterns-avoided). Every procedure here is reviewed by a database-owning service lead before merge.

See also: [`../functions/functions-catalog.md`](../functions/functions-catalog.md), [`../constraints/constraints-catalog.md`](../constraints/constraints-catalog.md).
