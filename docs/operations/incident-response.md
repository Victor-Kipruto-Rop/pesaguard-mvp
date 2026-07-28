# Incident response

## Severity levels

| Severity | Definition | Examples | Response |
|---|---|---|---|
| Sev1 | Platform-wide or payment-critical outage; customer money movement is failing or at risk of being wrong | Gateway down, `payment-service` unable to reach any provider, ledger imbalance detected | Immediate page, incident commander assigned, status page updated within 15 min |
| Sev2 | Significant degradation, workaround exists, no fund-safety risk | `notification-service` down (payments still complete, notifications delayed), elevated latency on one service | Page during business hours, next-business-day otherwise; incident commander assigned |
| Sev3 | Minor, isolated, no customer impact | Non-critical dashboard broken, `search-service` index lag | Ticketed, handled in normal sprint work |

## Roles

- **Incident Commander (IC)**: coordinates response, owns communication, does not personally debug. First on-call engineer to acknowledge a Sev1/Sev2 page is IC until formally handed off.
- **Ops lead**: executes technical remediation (rollback, scaling, failover).
- **Comms lead** (Sev1 only): updates the internal stakeholder channel and, if merchant-facing, the status page.

## Immediate response (first 15 minutes)

1. Acknowledge the page; declare severity.
2. Open an incident channel; pin the relevant runbook (see [`../runbooks/`](../runbooks/)) and dashboards (`monitoring/dashboards/`).
3. For any suspected fund-safety issue (ledger imbalance, duplicate payment processing, incorrect settlement): **do not attempt a live data fix**. Freeze the affected write path if possible (feature flag via `feature-flag-service`, or scale the affected consumer to zero) and escalate to the ledger/payments on-call lead before any remediation touches data.
4. Identify blast radius using `X-Request-ID` correlation across gateway and service logs/traces.

## During the incident

- IC posts a status update at least every 30 minutes, even if the update is "still investigating."
- Mitigation (rollback, scale-up, circuit-break a downstream) takes priority over root-causing — restore service first, understand fully after.
- All commands run against production during the incident are pasted into the incident channel as they're run, for the postmortem record.

## Resolution and postmortem

- Incident is "resolved" when the customer-facing symptom is gone, not necessarily when the root cause is fixed.
- A blameless postmortem is required for every Sev1 and Sev2 within 5 business days: timeline, root cause, contributing factors, and concrete follow-up actions with owners and due dates.
- Follow-up actions are tracked to completion — an incident isn't closed until they are, or explicitly deprioritized with sign-off.

See also: [`oncall-guide.md`](oncall-guide.md), [`../runbooks/`](../runbooks/), [`capacity-planning.md`](capacity-planning.md).
