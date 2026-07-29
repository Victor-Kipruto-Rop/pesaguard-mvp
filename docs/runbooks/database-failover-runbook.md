# Runbook: PostgreSQL failover

## Trigger

Pages when: primary instance health check fails for a service's RDS/Aurora PostgreSQL cluster, replication lag exceeds threshold, or `/ready` probes across a service's replicas start failing with database connection errors simultaneously.

## Immediate checks (first 5 minutes)

1. Confirm scope: one service's database, or a shared-cluster-wide event (check RDS/Aurora console or `terraform state` for the affected instance).
2. Check whether this is a **managed automatic failover** already in progress (Aurora typically fails over in under 30 seconds) — if so, verify the application layer recovers on its own via connection pool retry before intervening manually.
3. Check the affected service's `/ready` endpoint and connection pool metrics (`monitoring/dashboards/`) to confirm actual impact versus a transient blip.

## If automatic failover does not resolve it

1. Confirm the new primary (if Aurora already promoted a replica) is healthy and accepting writes: `psql` connectivity check + `pg_is_in_recovery()` returns `false` on the intended primary.
2. Update the service's connection string / endpoint if it isn't using the cluster's writer endpoint (all services should use the writer endpoint, not a pinned instance — verify in `app/config/settings.py` if this recurs).
3. Restart affected service pods only if connection pools are holding stale connections to the old primary after the endpoint has recovered (`kubectl rollout restart deployment/<service>`).

## If no automatic replica is available (rare — indicates a bigger issue)

1. Escalate immediately to the Platform on-call lead — this is a Sev1.
2. Do not attempt a manual point-in-time restore without a second engineer confirming the target recovery point; a wrong restore point on a payments-adjacent database is worse than extended downtime.
3. Once a replacement primary is available, run the service's Alembic migration check (`alembic current`) before allowing traffic back, to confirm schema state matches expectations.

## For payment-critical services specifically

`payment-service`, `transaction-service`, `ledger-service`: after any failover, before declaring the incident resolved, verify no in-flight transaction was left in an ambiguous state — cross-check the last N minutes of `transaction.created.v1`/`payment.completed.v1` events against ledger postings via `reconciliation-service`'s ad-hoc reconciliation job. Do not skip this step even under time pressure; an undetected ledger gap is a worse outcome than a longer incident.

## Postmortem inputs

Capture: time to automatic failover (if any), time to detection, time to full recovery, and whether the reconciliation cross-check found any discrepancy.

See also: [`../operations/incident-response.md`](../operations/incident-response.md), [`../../database/backups/backup-policy.md`](../../database/backups/backup-policy.md).
