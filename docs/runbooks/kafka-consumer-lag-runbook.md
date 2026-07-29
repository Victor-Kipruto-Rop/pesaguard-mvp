# Runbook: Kafka consumer lag

## Trigger

Pages when consumer group lag for a topic exceeds threshold for a sustained period (thresholds vary by topic criticality — see `monitoring/alerts/`). Most common on `payment.completed.v1`, `transaction.created.v1`, and `fraud.flagged.v1` consumer groups given their downstream fan-out.

## Immediate checks (first 5 minutes)

1. Identify the lagging consumer group and topic from the alert; confirm current lag and trend (growing vs. stable-but-elevated vs. recovering) in the Kafka dashboard (`monitoring/dashboards/`).
2. Determine cause category:
   - **Consumer down or crash-looping**: check pod status (`kubectl get pods -n pesaguard -l app=<service>`), recent deploys, and error logs.
   - **Consumer slow (processing bottleneck)**: check per-message processing latency in the service's traces — often a downstream call (database, another service) that's slow, not Kafka itself.
   - **Producer burst**: check producer-side throughput — a legitimate traffic spike (e.g., month-end) growing lag faster than steady-state consumer throughput can drain.
   - **Under-partitioned topic**: consumer group has more instances than partitions, so added replicas can't help — check partition count vs. consumer instance count.

## Remediation by cause

- **Consumer down**: restart/redeploy; if crash-looping from a bad deploy, roll back per [`../deployment/kubernetes-guide.md#rollback`](../deployment/kubernetes-guide.md#rollback).
- **Consumer slow**: scale out consumer replicas (bounded by partition count — see under-partitioned case below) and identify/fix the downstream bottleneck; consider temporarily disabling non-critical synchronous side effects inside the consumer if they're the bottleneck.
- **Producer burst**: usually self-resolving once burst subsides if consumer throughput exceeds steady-state production rate; monitor rather than intervene unless lag is still growing after 15 minutes.
- **Under-partitioned topic**: increasing partition count on an existing topic is possible but changes key-to-partition mapping for future messages (ordering guarantee per key is preserved going forward, not retroactively) — requires sign-off from the topic's owning service lead before changing in production; plan the change for a low-traffic window.

## Special handling for fraud-relevant topics

If `fraud.flagged.v1` consumer lag is growing, `transaction-service`'s hold logic may be delayed — meaning a transaction that should be held could complete before the flag is processed. Escalate to the Risk & Trust on-call immediately in this specific case, even if lag would otherwise be "just monitor" for a less time-sensitive topic; consider a temporary synchronous fraud-check fallback if configured (see `fraud-service` docs) while the consumer recovers.

## Verification

Lag trending back to near-zero and staying there for 15+ minutes before considering the incident resolved. Check for any dead-lettered messages (`<topic>.dlq`) that need manual reprocessing once the root cause is fixed.

See also: [`../../architecture/event-driven-design.md`](../../architecture/event-driven-design.md), [`../operations/incident-response.md`](../operations/incident-response.md).
