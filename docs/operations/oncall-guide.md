# On-call guide

## Rotation structure

| Rotation | Coverage | Owns |
|---|---|---|
| Platform/Gateway | 24/7, weekly | Gateway, `shared/`, Kafka, Redis, PostgreSQL infrastructure |
| Payments | 24/7, weekly | `payment-service`, `mpesa-service`, `airtel-money-service`, `bank-service`, `transaction-service`, `ledger-service`, `settlement-service`, `reconciliation-service` |
| Risk & Trust | Business hours + Sev1 page, weekly | `fraud-service`, `risk-service`, `audit-service` |
| Platform Services | Business hours + Sev1 page, weekly | Remaining services (identity, communication, insight, platform) |

Payments carries a dedicated 24/7 rotation separate from general Platform because fund-movement incidents have a fundamentally different risk profile (see [`incident-response.md`](incident-response.md#immediate-response-first-15-minutes)) and need someone with ledger/reconciliation context immediately, not just infrastructure context.

## Being on call

- Acknowledge a page within 5 minutes (24/7 rotations) or 15 minutes (business-hours rotations).
- Keep a laptop and stable connection available for the full rotation window.
- If you can't resolve or mitigate within 30 minutes, escalate — paging a second engineer early is always the right call, not a failure.

## Escalation path

1. Primary on-call (per rotation table above)
2. Secondary on-call for the same rotation
3. Engineering lead for the affected domain
4. Incident Commander pool (any Sev1) — see [`incident-response.md`](incident-response.md#roles)

## Handoff

At the end of a rotation, the outgoing on-call briefs the incoming on-call on: any open incidents, any suppressed/silenced alerts and why, any deploys in flight, and any "watch this" items (e.g., a metric trending toward threshold but not yet alerting).

## Alert quality bar

An alert that pages someone must be actionable — if an alert fires and the response is always "nothing to do," it should be turned into a dashboard panel, not a page. Alert definitions live in `monitoring/alerts/`; propose changes via PR, reviewed by the owning rotation's lead.

## Runbooks

Every alert that can page should link to a runbook. Current runbooks: [`../runbooks/database-failover-runbook.md`](../runbooks/database-failover-runbook.md), [`../runbooks/kafka-consumer-lag-runbook.md`](../runbooks/kafka-consumer-lag-runbook.md), [`../runbooks/payment-service-runbook.md`](../runbooks/payment-service-runbook.md), [`gateway-runbook.md`](gateway-runbook.md). If you resolve a page without an existing runbook, write one.

See also: [`incident-response.md`](incident-response.md), [`capacity-planning.md`](capacity-planning.md).
