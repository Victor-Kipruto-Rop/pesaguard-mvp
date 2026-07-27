# API gateway runbook

## Alerts

Page the owning team for sustained 5xx responses, readiness failures, elevated upstream circuit openings, Redis connection failures, authentication error spikes, or p95 latency above the service objective. Use request IDs to correlate gateway logs with downstream traces.

## Immediate response

1. Confirm the gateway `/live` and `/ready` probes and replica count.
2. Check Redis availability before changing rate-limit or idempotency controls. Do not disable them during a payment incident.
3. Inspect upstream-specific error/latency metrics to identify the affected service.
4. If a circuit is open, fix the downstream dependency; it will automatically probe again after its configured reset period.
5. For payment retries, preserve the original `Idempotency-Key`. Never advise a client to generate a new key after an uncertain outcome.

## Escalation and recovery

Rotate compromised keys through the identity platform/secret manager, revoke affected API keys, and retain audit logs. A rollback must use an immutable signed image and must retain the same gateway configuration and Redis data until payment reconciliation confirms no in-flight idempotency records are needed.
