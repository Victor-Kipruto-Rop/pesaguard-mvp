# Event-Driven Design in PesaGuard

## Why events

Payment processing is inherently multi-step and multi-party: a single STK push touches `mpesa-service`, `payment-service`, `transaction-service`, `ledger-service`, `fraud-service`, and `notification-service`. Chaining these synchronously would couple availability (if `notification-service` is down, payments would fail) and create a distributed monolith. PesaGuard instead treats state transitions as facts published to Kafka, consumed independently by every interested service.

## Event backbone

- **Broker**: Apache Kafka, provisioned via `infrastructure/kafka/`.
- **Schema governance**: Confluent Schema Registry, `BACKWARD` compatibility mode by default (see [`event-schemas/schema-registry-config.md`](../event-schemas/schema-registry-config.md)).
- **Topic naming**: `<domain>.<event>.v<version>`, e.g. `payment.completed.v1`, `fraud.flagged.v1`.
- **Partitioning key**: the aggregate ID relevant to ordering guarantees (e.g., `transaction_id` for transaction events) so all events for one entity land on the same partition and are processed in order.
- **Delivery semantics**: at-least-once. Consumers must be idempotent — see [`shared/kafka/`](../shared/README.md) for the idempotent-consumer helper used across services.

## Event catalog (representative)

| Event | Producer | Key consumers |
|---|---|---|
| `payment.initiated.v1` | `payment-service` | `fraud-service`, `analytics-service` |
| `payment.completed.v1` | `payment-service` | `ledger-service`, `notification-service`, `reconciliation-service` |
| `payment.failed.v1` | `payment-service` | `notification-service`, `analytics-service` |
| `transaction.created.v1` | `transaction-service` | `ledger-service`, `fraud-service` |
| `transaction.reversed.v1` | `transaction-service` | `ledger-service`, `audit-service` |
| `fraud.flagged.v1` | `fraud-service` | `transaction-service` (hold), `notification-service`, `audit-service` |
| `fraud.cleared.v1` | `fraud-service` | `transaction-service` (release hold) |
| `notification.sms.v1` / `notification.email.v1` | `notification-service` | `sms-service` / `email-service` |

Full JSON Schema definitions live in [`event-schemas/`](../event-schemas/); AsyncAPI documentation in [`api-specs/asyncapi/`](../api-specs/asyncapi/).

## Patterns in use

- **Choreography over orchestration** for straight-line flows (payment → ledger → notification): each service reacts to the previous service's event with no central coordinator.
- **Orchestration via `workflow-service`** for multi-step processes needing explicit compensation (e.g., a payment reversal that must undo a ledger entry, notify the customer, and update a merchant balance in a specific order) — implemented as sagas. See `workflow-service` docs.
- **Outbox pattern**: services write the domain state change and the outbound event in the same database transaction (an `outbox` table), with a separate relay process publishing to Kafka — avoiding the dual-write problem between PostgreSQL and Kafka.
- **Dead-letter topics**: `<topic>.dlq` for events that fail consumer processing after retry, monitored by `health-service` and surfaced in Grafana.

## Consistency model

PesaGuard is deliberately **eventually consistent** across service boundaries and **strongly consistent** within a single service's database transaction. A payment's ledger posting may lag its completion by milliseconds to low seconds under normal load; user-facing flows that need synchronous confirmation (e.g., "is this payment done yet?") poll `transaction-service`'s own state, which is updated synchronously within its own boundary.

See also: [`cqrs-design.md`](cqrs-design.md), [`docs/architecture/event-storming.md`](../docs/architecture/event-storming.md), [`docs/adr/0001-event-driven-architecture.md`](../docs/adr/0001-event-driven-architecture.md).
