# Database backup policy

## Scope

Covers PostgreSQL backup strategy for every service's per-service database (see [`../../docs/database/schema-conventions.md`](../../docs/database/schema-conventions.md) for the database-per-service model). For general infrastructure/config backups, see [`../../backups/backup-policy.md`](../../backups/backup-policy.md).

## Backup types and cadence

| Type | Cadence | Retention | Mechanism |
|---|---|---|---|
| Automated snapshot | Daily | 35 days | RDS/Aurora automated snapshots |
| Continuous (point-in-time recovery) | Continuous, 5-minute granularity | 7 days rolling | RDS/Aurora transaction log shipping |
| Pre-migration snapshot | Before every schema migration deploy | 30 days | Triggered by CI/CD pipeline before Alembic `upgrade` runs |
| Long-term archival snapshot | Monthly | 7 years (payments/ledger schemas), 1 year (others) | Exported to S3, encrypted, lifecycle-policy managed |

Payment-critical schemas (`payments`, `ledger`, `transaction`) use the full 7-year archival retention to satisfy CBK record-keeping requirements (see [`../../security/policies/cbk-compliance.md`](../../security/policies/cbk-compliance.md)); non-financial schemas use the shorter default.

## Restore testing

- Automated monthly restore drill: a snapshot is restored to an isolated environment and validated against a checksum/row-count baseline, without human intervention, with alerting on failure.
- A full manual disaster-recovery drill (restore + application reconnection + smoke test) is run quarterly for `payments`, `ledger`, and `auth` schemas specifically, given their criticality.

## Recovery point and time objectives

| Schema class | RPO | RTO |
|---|---|---|
| Payment-critical (`payments`, `ledger`, `transaction`, `auth`) | 5 minutes | 1 hour |
| Standard | 24 hours | 4 hours |

## Encryption

All backups (automated snapshots, PITR logs, and archival exports) are encrypted at rest using the same KMS-managed keys as the source database — a backup is never a lower-security copy of the data than the original.

## Access

Snapshot restore and archival export access is restricted to the Platform on-call rotation and requires two-person authorization for any restore against a production-equivalent target, logged via `audit-service`. Routine automated restore-drills run under a scoped, non-human service identity.

## Failure procedure

If an automated snapshot fails, `health-service` alerts the Platform on-call rotation immediately (not batched into a daily digest) — a missed backup window is treated as an operational incident, not a low-priority ticket, given the RPO commitments above.

See also: [`../../docs/runbooks/database-failover-runbook.md`](../../docs/runbooks/database-failover-runbook.md), [`../../security/policies/data-retention-policy.md`](../../security/policies/data-retention-policy.md).
