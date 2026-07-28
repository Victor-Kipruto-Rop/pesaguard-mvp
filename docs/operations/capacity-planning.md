# Capacity planning

## Traffic pattern

Mobile money traffic in Kenya is strongly periodic: end-of-month salary disbursement periods (last 2 business days and first 3 business days of each month) drive peaks of roughly 4-6x average daily transaction volume, concentrated in `mpesa-service`, `payment-service`, `transaction-service`, `ledger-service`, and `fraud-service`. Public holidays and the run-up to school-fee payment deadlines produce secondary, smaller peaks.

## Planning approach

1. **Baseline from `analytics-service`**: rolling 90-day transaction volume, broken down by hour-of-day and day-of-month, is the source baseline — not gut-feel estimates.
2. **Peak multiplier**: capacity is provisioned for 1.5x the highest observed end-of-month peak, not the average — the payment-critical path must not degrade during the periods that matter most to customers.
3. **Load testing validates the plan**: before month-end, `tests/load/locustfile.py` and `tests/performance/k6-payment-flow.js` are run against staging at the planned peak multiplier as a release gate (see [`../deployment/release-process.md`](../deployment/release-process.md)).

## Autoscaling configuration

- Payment-critical services scale on a blended CPU + request-latency HPA metric, `minReplicas` set to comfortably absorb a sudden 2x spike without waiting for scale-up (scale-up lag is a known limitation of pure CPU-based HPA).
- Kafka consumer services additionally scale on **consumer lag** (via KEDA), since a CPU-idle consumer can still be falling behind if per-message processing is I/O-bound.
- Database connection pools are sized per-service against the *maximum* replica count, not the baseline, to avoid pool exhaustion during a scale-up event — see the per-service `docs/ARCHITECTURE.md` for pool sizing.

## Datastore capacity

- **PostgreSQL**: vertical headroom reviewed quarterly against `pg_stat_statements` and connection saturation; read replicas added for services with growing read-heavy load (`analytics-service`, `report-service`) rather than scaling the primary.
- **Kafka**: partition count set to comfortably exceed the maximum expected consumer parallelism per topic; under-partitioning is the most common cause of consumer-side bottlenecks and is far more disruptive to fix later than over-provisioning slightly upfront.
- **Redis**: sized for the fraud-velocity working set (see [`../../architecture/cqrs-design.md`](../../architecture/cqrs-design.md)) plus rate-limiting/idempotency-key volume at peak, with eviction policy `volatile-lru` so TTL'd keys are reclaimed first.

## Review cadence

Capacity is reviewed quarterly and ahead of any known high-traffic event (e.g., a new large merchant integration going live). Findings and actions are logged alongside the relevant `monitoring/slo/` document.

See also: [`oncall-guide.md`](oncall-guide.md), [`../../monitoring/README.md`](../../monitoring/README.md).
