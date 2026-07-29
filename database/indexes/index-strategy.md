# Index strategy

## Principle

Indexes are added against an observed slow query (via `pg_stat_statements`, reviewed as part of the quarterly capacity review — see [`../../docs/operations/capacity-planning.md`](../../docs/operations/capacity-planning.md)), not speculatively. Every service's baseline indexes (see [`../../docs/database/schema-conventions.md#indexing-baseline`](../../docs/database/schema-conventions.md#indexing-baseline)) — `organization_id`, event partition-key columns — are the exception, applied by default from the first migration.

## Baseline indexes (every tenant-scoped table)

| Index | Reason |
|---|---|
| `(organization_id)` | Every query is tenant-scoped; without this, every query is a sequential scan filtered post-hoc |
| `(id)` | Primary key, always indexed by default |
| `(created_at)` where time-range queries are common | Supports reporting and pagination by date |

## Service-specific high-value indexes

| Table | Index | Reason |
|---|---|---|
| `payments.payment_requests` | `UNIQUE (merchant_id, idempotency_key)` | Idempotency enforcement (also a constraint — see [`../constraints/constraints-catalog.md`](../constraints/constraints-catalog.md)) |
| `payments.payment_requests` | `(organization_id, status, created_at)` | Powers the merchant dashboard's "pending payments" and "recent payments" views without a sequential scan |
| `transaction.transactions` | `(id)` used as Kafka partition key — indexed for point lookup on event replay | Consumer catch-up performance |
| `ledger.ledger_entries` | `(transaction_id)` | Every ledger operation looks up entries by transaction |
| `ledger.ledger_entries` | `(account_id, created_at)` | Trial balance and statement queries |
| `fraud.fraud_cases` | `(transaction_id)` | 1:1 lookup from transaction to case |
| `fraud.transaction_events` | `(customer_id, created_at)` | Velocity window queries (fallback path — see [`../functions/functions-catalog.md#velocity_window_countcustomer_id-uuid-window_minutes-int-returns-int`](../functions/functions-catalog.md)) |
| `audit.audit_entries` | `(entity_type, entity_id, created_at)` | "Show me the history of this record" is the most common audit query shape |
| `auth.sessions` | `(user_id, expires_at)` | Active-session lookups |

## Composite index ordering

Composite indexes are ordered highest-selectivity-first only where the query pattern always filters on the leading column; where queries sometimes omit a leading filter (e.g., an admin query across all organizations), a separate single-column index is added rather than relying on index skip-scan behavior.

## Partial indexes

Used where a status column is heavily skewed and queries only ever target the minority state — e.g., `payments.payment_requests (organization_id, created_at) WHERE status = 'pending'` is a partial index supporting the "what's still pending" dashboard query without indexing the much larger set of terminal-state rows.

## Anti-patterns avoided

- No index added purely because a column "might be queried later" — see Principle above.
- No unbounded number of indexes on write-heavy tables (`ledger_entries`, `transactions`) — each additional index has a real write-amplification cost, weighed explicitly against the read benefit before adding.

See also: [`../../docs/database/schema-conventions.md`](../../docs/database/schema-conventions.md), [`../constraints/constraints-catalog.md`](../constraints/constraints-catalog.md).
