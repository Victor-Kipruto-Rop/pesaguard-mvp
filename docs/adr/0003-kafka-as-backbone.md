# ADR 0003: Apache Kafka as the sole event backbone

- **Status**: Accepted
- **Date**: 2025-08-20
- **Deciders**: Platform architecture group, Infrastructure

## Context

Having decided on event-driven integration as the default ([ADR 0001](0001-event-driven-architecture.md)), we needed a single messaging technology for the whole platform. Candidates evaluated: Apache Kafka (self-managed on MSK), RabbitMQ, AWS SNS/SQS, and NATS JetStream.

Requirements: ordered delivery per aggregate, replay capability for rebuilding CQRS read models ([ADR 0002](0002-cqrs-adoption.md)), schema governance to prevent producer/consumer drift across 30 independently deployed services, and throughput headroom for peak M-Pesa transaction volume (observed peaks around end-of-month salary disbursement periods).

## Decision

Standardize on Apache Kafka, provisioned via `infrastructure/kafka/` and Terraform-managed AWS MSK, with Confluent Schema Registry for contract governance ([`event-schemas/schema-registry-config.md`](../../event-schemas/schema-registry-config.md)) in `BACKWARD` compatibility mode.

Key reasons:
- **Log retention and replay** — SNS/SQS and most AMQP brokers don't retain and let you replay a durable log, which is required for rebuilding CQRS read models after a bug or schema change.
- **Partition-level ordering** — keying by aggregate ID (e.g., `transaction_id`) gives per-entity ordering guarantees without requiring a single global partition.
- **Schema Registry integration** — enforces that producers can't publish a breaking change without a compatibility check failing in CI, catching contract drift before it reaches a consumer.
- **Operational maturity of MSK** — reduces the operational burden of running Kafka ourselves while keeping the Kafka protocol (avoiding lock-in to a proprietary managed queue's semantics).

## Consequences

**Positive:** all 30 services share one mental model and one client library (`shared/kafka/`) for publishing and consuming; replay-based recovery is a first-class operational capability, not a special case.

**Negative:** Kafka has a steeper operational learning curve than SQS; consumer lag is a new failure mode every on-call engineer needs to understand (see [`../runbooks/kafka-consumer-lag-runbook.md`](../runbooks/kafka-consumer-lag-runbook.md)). Local development requires running Kafka (via `docker compose`), adding friction versus a fully managed cloud queue.

## Alternatives considered

- **AWS SNS/SQS**: simpler operationally, but no native replay and weaker ordering guarantees across fan-out consumers; would have blocked the CQRS read-model rebuild strategy.
- **RabbitMQ**: strong routing flexibility, but log retention/replay is not its core model and schema governance tooling is weaker than the Kafka ecosystem's.
- **NATS JetStream**: attractive lightweight footprint, but smaller ecosystem maturity for schema registry integration at the time of decision.

Related: [`0001-event-driven-architecture.md`](0001-event-driven-architecture.md), [`../../infrastructure/kafka/`](../../infrastructure/kafka).
