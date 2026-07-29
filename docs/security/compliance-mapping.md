# Compliance mapping

## Purpose

Maps regulatory and standards obligations to the specific PesaGuard controls that satisfy them, so an auditor or new team member can trace "why does this control exist" back to its source requirement.

## Kenya Data Protection Act, 2019 (KDPA)

| KDPA requirement | PesaGuard control |
|---|---|
| Lawful basis and purpose limitation for processing personal data | Data collection scoped to KYC/AML and payment-processing purpose only; documented per-service in `docs/ARCHITECTURE.md` |
| Data minimization | Restricted-classification fields masked by default (see [`data-classification.md`](data-classification.md)) |
| Security safeguards proportionate to risk | Field-level encryption, mTLS, RBAC, audit logging (see [`threat-model.md`](threat-model.md)) |
| Data subject access/deletion rights | `user-service` and `customer-service` expose data export/erasure workflows subject to financial-record retention overrides (see [`../../security/policies/data-retention-policy.md`](../../security/policies/data-retention-policy.md)) |
| Data breach notification | Covered under [`../../SECURITY.md`](../../SECURITY.md) disclosure process and [`../operations/incident-response.md`](../operations/incident-response.md) Sev1 escalation |
| Data Protection Impact Assessment for high-risk processing | Required before any new fraud-scoring signal that processes behavioral/biometric-adjacent data goes to production |

Full policy detail: [`../../security/policies/kenya-dpa-compliance.md`](../../security/policies/kenya-dpa-compliance.md).

## Central Bank of Kenya (CBK) requirements

| CBK area | PesaGuard control |
|---|---|
| Payment Service Provider prudential requirements | Ledger immutability and reconciliation (see [`../architecture/domain-model.md`](../architecture/domain-model.md#invariants-enforced-at-the-domain-layer)) |
| Transaction record retention | Minimum retention period enforced in `database/backups/backup-policy.md` and `security/policies/data-retention-policy.md` |
| AML/CFT transaction monitoring | `fraud-service` and `risk-service` real-time scoring; suspicious activity case workflow via `audit-service` |
| Regulatory reporting | `report-service` scheduled CBK submission templates |
| Incident/outage reporting obligations | `../operations/incident-response.md` Sev1 process includes regulatory notification as a comms-lead responsibility for fund-affecting incidents |

Full policy detail: [`../../security/policies/cbk-compliance.md`](../../security/policies/cbk-compliance.md).

## PCI-adjacent posture

PesaGuard does not store card PANs, CVVs, or PINs — mobile money and bank rail providers handle credential entry natively, keeping PesaGuard largely out of PCI DSS cardholder-data-environment scope for those flows. Where bank card settlement is involved (`bank-service`), tokenized references only are stored; see `services/bank-service/docs/ARCHITECTURE.md`.

## Audit evidence

`audit-service`'s hash-chained log, combined with `security/scans/dependency-scan-report-template.md` scan history and `docs/deployment/release-process.md` release gate records, forms the primary evidence trail for both internal and external audits.

See also: [`threat-model.md`](threat-model.md), [`data-classification.md`](data-classification.md).
