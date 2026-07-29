# Infrastructure backup policy

## Scope

Covers backup of infrastructure state and configuration outside the application databases: Terraform state, Kubernetes/Helm configuration, Vault secrets metadata, and configuration snapshots. For database backups specifically, see [`../database/backups/backup-policy.md`](../database/backups/backup-policy.md).

## What's backed up here

| Artifact | Location | Cadence | Retention |
|---|---|---|---|
| Terraform state | `infrastructure/terraform/` remote state (S3 + DynamoDB lock) | Versioned on every `apply` (S3 versioning) | Indefinite, pruned after 2 years of inactivity per resource |
| Kubernetes manifests / Helm values | This repository (`infrastructure/helm/`, `infrastructure/kubernetes/`) | Git-native — every commit is a backup | Full git history |
| Vault configuration (policies, auth methods, not secret values) | `infrastructure/vault/` | Versioned in git; Vault's own snapshot for the secret engine data | Vault snapshots: daily, 30-day retention |
| Grafana dashboards / alert rules | `monitoring/dashboards/`, `monitoring/alerts/` | Git-native | Full git history |
| Configuration service state (`configuration-service`, `feature-flag-service`) | Own PostgreSQL databases | Covered by [`../database/backups/backup-policy.md`](../database/backups/backup-policy.md) | Standard schedule |

`backups/database/` and `backups/configs/` are local staging directories used by backup automation scripts (`scripts/`) before artifacts are shipped to their durable S3 destination — they are not themselves the durable backup location and are not expected to persist.

## Why this is separate from database backups

Infrastructure-as-code is versioned in git, which is itself a form of backup, but git history alone doesn't cover live state (Terraform state file, Vault's actual secret engine contents, in-cluster resources created outside of a committed manifest). This policy exists to make sure state and configuration — not just the code that produces it — is recoverable independent of the database recovery process.

## Recovery scenario: full environment rebuild

In the event a whole environment needs to be rebuilt from scratch (e.g., catastrophic cluster loss):

1. Restore Terraform state from the latest S3 version, or re-`import` resources if state itself is unrecoverable.
2. Re-apply Terraform to recreate infrastructure.
3. Re-sync Argo CD against `main` (or the last known-good tagged release) to redeploy all services.
4. Restore Vault from its latest snapshot to recover secret engine configuration (actual secret values re-issue via normal dynamic-secret flows where possible, rather than restoring static secret values).
5. Restore application databases per [`../database/backups/backup-policy.md`](../database/backups/backup-policy.md).

This scenario is drilled at minimum annually as part of the broader disaster-recovery testing program.

See also: [`../database/backups/backup-policy.md`](../database/backups/backup-policy.md), [`../docs/runbooks/database-failover-runbook.md`](../docs/runbooks/database-failover-runbook.md).
