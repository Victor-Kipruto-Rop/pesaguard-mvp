# `ledger` schema

Owning service: `ledger-service`. See [`../../services/ledger-service/docs/ARCHITECTURE.md`](../../services/ledger-service/docs/ARCHITECTURE.md).

## Design principle

Double-entry accounting: every economic event produces at least one debit and one balancing credit. Entries are immutable once written — corrections happen only via new, balancing compensating entries, never `UPDATE`/`DELETE` against a posted entry (see [`../../architecture/domain-model.md`](../../architecture/domain-model.md#invariants-enforced-at-the-domain-layer)).

## Tables

### `ledger_accounts`

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID` | Primary key |
| `account_type` | `VARCHAR(30)` | `merchant_settlement`, `customer_wallet`, `platform_fee_revenue`, `provider_clearing`, ... |
| `organization_id` | `UUID NULL` | Null for platform-internal accounts |
| `currency` | `CHAR(3)` | ISO 4217 |
| `status` | `VARCHAR(20)` | `active`, `frozen` |
| `created_at`, `updated_at` | `TIMESTAMPTZ` | |

Note: `ledger_accounts` does **not** store a running `balance` column — balance is always derived by summing `ledger_entries`, avoiding balance/entry drift as a class of bug. Materialized balance snapshots for performance are described below.

### `ledger_entries`

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID` | Primary key, chronologically sortable (UUIDv7) |
| `batch_id` | `UUID` | Groups entries that must balance together — see constraint below |
| `account_id` | `UUID` | FK to `ledger_accounts.id` |
| `transaction_id` | `UUID` | Logical FK to `transaction-service`'s `transactions.id` |
| `direction` | `VARCHAR(6)` | `debit` or `credit` |
| `amount` | `NUMERIC(19,4)` | Always positive; sign is carried by `direction`, never a negative amount |
| `posted_at` | `TIMESTAMPTZ` | Immutable once set |
| `reversal_of_entry_id` | `UUID NULL` | Set only on a compensating entry, referencing the entry it offsets |

### `ledger_balance_snapshots`

Periodic materialized snapshot (not authoritative — always reconcilable against `ledger_entries`) for read performance on high-volume accounts:

| Column | Type | Notes |
|---|---|---|
| `account_id` | `UUID` | |
| `as_of` | `TIMESTAMPTZ` | |
| `balance` | `NUMERIC(19,4)` | Sum of entries up to `as_of` |

## Constraints

- **Balanced batch constraint**: for any `batch_id`, `SUM(amount WHERE direction='debit') = SUM(amount WHERE direction='credit')`. Enforced via a deferred constraint trigger evaluated at transaction commit, not a simple `CHECK` (since a batch is built from multiple inserted rows within one transaction).
- No `UPDATE` or `DELETE` grant exists on `ledger_entries` for any application role — only `INSERT`. Migrations that need schema changes (adding a column) are the sole exception, and never touch existing row values.
- `CHECK (amount > 0)` on `ledger_entries`.

## Indexes

- `ledger_entries(account_id, posted_at)` — supports statement/balance queries
- `ledger_entries(transaction_id)` — supports reconciliation lookups
- `ledger_entries(batch_id)` — supports the balance constraint check and audit queries

## Reconciliation

`reconciliation-service` periodically recomputes account balances from `ledger_entries` and compares against `ledger_balance_snapshots` and provider settlement statements, flagging any variance to `fraud-service`/compliance review — see [`../../security/policies/cbk-compliance.md`](../../security/policies/cbk-compliance.md#fund-safety-and-ledger-integrity).

See also: [`../../docs/runbooks/database-failover-runbook.md`](../../docs/runbooks/database-failover-runbook.md), [`../constraints/constraints-catalog.md`](../constraints/constraints-catalog.md).
