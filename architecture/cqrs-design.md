# CQRS in PesaGuard

## Where CQRS applies

PesaGuard does not apply CQRS uniformly — most services use a single model for reads and writes because their query patterns are simple (fetch by ID, list by owner). CQRS is applied specifically where write and read workloads diverge sharply:

- **`analytics-service`** and **`report-service`**: read models are denormalized projections built from consumed events (`payment.completed.v1`, `transaction.created.v1`, ...), optimized for aggregation queries (daily volume, merchant-level totals, regulatory report line items) that would be prohibitively expensive against the normalized transactional schema in `payment-service`/`transaction-service`.
- **`search-service`**: an OpenSearch-backed read model, populated by consuming events from `customer-service`, `merchant-service`, and `transaction-service`, supporting full-text and faceted queries the source-of-truth relational schemas aren't designed for.
- **`fraud-service`**: a velocity/behavioral read model (recent transaction counts and amounts per customer/device, held in Redis) is maintained separately from the durable `FraudCase` write model in PostgreSQL, because fraud scoring needs sub-10ms reads that a relational aggregate query cannot guarantee under load.

## Write side

The write model in each of these services remains a conventional normalized relational schema, owned exclusively by that service, mutated only through its own API — the source of truth never moves.

## Read side

Read models are:

1. **Derived, not authoritative** — rebuildable from the event log at any time; a read model is a projection, not a second source of truth.
2. **Populated asynchronously** — via Kafka consumers, with eventual consistency between write and read (see [`event-driven-design.md`](event-driven-design.md#consistency-model)).
3. **Independently scaled and independently shaped** — `analytics-service`'s PostgreSQL read replica schema looks nothing like `payment-service`'s write schema; it's shaped for the queries it serves (star-schema-like fact/dimension tables — see `database/schemas/`).

## Consequences accepted

- **Staleness window**: analytics/search/fraud-velocity reads can lag the write model by up to a few seconds under normal load. This is explicitly acceptable for these use cases — none of them gate a payment's success/failure decision on stale data alone (fraud scoring combines the fast Redis read model with synchronous checks where a decision is time-critical).
- **Rebuild cost**: a corrupted or schema-changed read model is rebuilt by replaying the relevant Kafka topics from the beginning (or from a compacted snapshot), not by reading the write-side database directly — this is a deliberate constraint that keeps the pattern honest.

## When CQRS was rejected

Services like `auth-service`, `organization-service`, and `merchant-service` explicitly do **not** use CQRS — their query patterns are simple CRUD-shaped, and introducing a separate read model would add operational complexity (another datastore, another consumer, another consistency window) without a corresponding query-performance problem to justify it.

See also: [`docs/adr/0002-cqrs-adoption.md`](../docs/adr/0002-cqrs-adoption.md), [`event-driven-design.md`](event-driven-design.md).
