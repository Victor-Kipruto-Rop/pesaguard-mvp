# ADR 0001: Adopt event-driven architecture as the default cross-service integration style

- **Status**: Accepted
- **Date**: 2025-08-12
- **Deciders**: Platform architecture group

## Context

PesaGuard's core payment flow spans at least six services (`mpesa-service`/`airtel-money-service` → `payment-service` → `transaction-service` → `ledger-service` → `fraud-service` → `notification-service`). An early prototype chained these as synchronous HTTP calls. Under load testing, a slow or unavailable `notification-service` degraded payment latency and, in one failure injection test, caused payment timeouts even though the payment itself had succeeded upstream. Availability of the whole chain was bounded by the least available service.

## Decision

Cross-service integration defaults to asynchronous, event-driven communication over Kafka, using versioned domain events as the published contract. Synchronous HTTP is reserved for: (a) the client-facing request/response through the gateway, and (b) narrow, well-justified internal calls where a caller genuinely cannot proceed without an immediate answer (e.g., `payment-service` calling `fraud-service`'s synchronous scoring endpoint for a pre-transaction decision).

## Consequences

**Positive:**
- Services fail independently; a downstream consumer outage does not block the producing service's core write path.
- New consumers (e.g., `analytics-service`) can be added without modifying producers.
- Natural audit trail: the event log is a durable record of what happened and when.

**Negative:**
- Eventual consistency must be designed for explicitly (see [`cqrs-design.md`](../../architecture/cqrs-design.md)) — clients cannot assume a downstream side effect has completed the instant the initiating request returns.
- Debugging a cross-service flow requires distributed tracing (correlation IDs propagated through Kafka headers) rather than a single stack trace.
- Consumers must be built idempotent from day one, since Kafka delivery is at-least-once.

## Alternatives considered

- **Synchronous orchestration with a saga coordinator for every flow** — rejected as the default because it reintroduces tight availability coupling for flows that don't need synchronous compensation; still used selectively via `workflow-service` for flows that do (see [`docs/adr/0003-kafka-as-backbone.md`](0003-kafka-as-backbone.md)).
- **Shared database with triggers** — rejected outright; violates database-per-service and creates schema coupling that blocks independent deployment.

Related: [`0003-kafka-as-backbone.md`](0003-kafka-as-backbone.md), [`../../architecture/event-driven-design.md`](../../architecture/event-driven-design.md).
