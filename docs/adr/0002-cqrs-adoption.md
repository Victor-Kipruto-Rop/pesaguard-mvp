# ADR 0002: Adopt CQRS selectively for analytics, search, and fraud-velocity read paths

- **Status**: Accepted
- **Date**: 2025-09-03
- **Deciders**: Platform architecture group, Fraud engineering

## Context

`analytics-service` and `report-service` originally queried `transaction-service`'s and `payment-service`'s production databases directly for aggregate reporting. This caused two problems: (1) reporting queries (multi-table joins over months of transaction history) competed for the same connection pool and I/O as the transactional write path, degrading payment latency during month-end reporting runs; (2) it created hidden schema coupling — a migration in `transaction-service` broke `analytics-service` queries with no compile-time or contract-level warning.

Separately, `fraud-service`'s velocity checks (transaction count/amount per customer over rolling windows) needed sub-10ms reads under peak load, which a relational aggregate query against the durable `FraudCase`/`Transaction` tables could not reliably guarantee.

## Decision

Adopt CQRS specifically for these three read paths, each with a purpose-built, denormalized read model populated asynchronously from Kafka events, decoupled from and never queried directly against another service's write-side database:

- `analytics-service` / `report-service`: star-schema-like PostgreSQL read replica, populated from `payment.*`, `transaction.*`, `fraud.*` events.
- `search-service`: OpenSearch index, populated from `customer.*`, `merchant.*`, `transaction.*` events.
- `fraud-service`: Redis-backed velocity counters, populated synchronously on transaction events with short TTLs.

CQRS is explicitly **not** adopted platform-wide — see [`../../architecture/cqrs-design.md`](../../architecture/cqrs-design.md#when-cqrs-was-rejected) for services where the added complexity wasn't justified.

## Consequences

**Positive:** reporting and search load no longer contends with transactional write paths; each read model is shaped for its actual query pattern rather than forced through a shared normalized schema.

**Negative:** read models can lag their source of truth by a few seconds; a schema or bug in a projection requires a replay from the event log to fix, which takes operational runbook discipline (see [`../runbooks/kafka-consumer-lag-runbook.md`](../runbooks/kafka-consumer-lag-runbook.md)).

## Alternatives considered

- **Read replicas of the same relational schema** — rejected for `search-service` (wrong query shape entirely) and only partially solves `analytics-service`'s problem, since the join-heavy queries would still be slow against a normalized schema even on a replica.

Related: [`../../architecture/cqrs-design.md`](../../architecture/cqrs-design.md), [`0001-event-driven-architecture.md`](0001-event-driven-architecture.md).
