# Runbook: payment-service

## Alerts covered

- Elevated `5xx` rate on `/api/v{1,2}/payments/*`
- Payment success rate drop (from `analytics-service` derived metric)
- Idempotency conflict rate spike
- Upstream (`mpesa-service`/`airtel-money-service`/`bank-service`) timeout rate spike as seen from `payment-service`

## Immediate checks (first 10 minutes)

1. Confirm `payment-service` `/ready` and replica count — rule out a service-level outage before investigating logic issues.
2. Check whether the issue is isolated to one provider (M-Pesa vs. Airtel vs. bank) — if so, this is likely an upstream provider incident, not a `payment-service` bug; check the provider's status page and `mpesa-service`/`airtel-money-service` logs for the actual upstream error.
3. Check the idempotency conflict rate: a spike usually means clients are retrying with a *new* idempotency key after a timeout instead of reusing the original — this is a client integration issue, not a `payment-service` bug, but confirm before ruling it out.

## Payment stuck in `pending`

1. Check `payment_attempts` for the request — is there a provider callback that hasn't been received? (Compare `checkout_request_id` against provider logs/dashboard if available.)
2. If the provider confirms completion but PesaGuard shows `pending`, check `webhook-service` and `mpesa-service`'s callback endpoint for delivery failures — the callback may not have reached PesaGuard.
3. **Never manually mark a payment as completed without confirming the actual provider-side outcome.** A payment shown as `completed` without a corresponding provider confirmation is a worse failure mode than a payment stuck in `pending` pending investigation.
4. If confirmed completed upstream but stuck internally, use the documented reconciliation replay (see `reconciliation-service` docs) rather than a manual database update — this preserves the audit trail and triggers the normal downstream events (ledger posting, notification).

## Suspected duplicate charge

1. This is treated as a **Sev1** regardless of count — escalate to the Payments on-call lead immediately per [`../operations/incident-response.md`](../operations/incident-response.md).
2. Do not attempt a live fix. Gather: idempotency key(s) used, `payment_attempt` records, and provider transaction references for all suspected duplicates.
3. Remediation (refund/reversal) goes through `transaction-service`'s reversal flow, never a direct database edit — see [`../../architecture/domain-model.md`](../../docs/architecture/domain-model.md#invariants-enforced-at-the-domain-layer).

## Elevated latency, provider-side

If a specific provider's response time has degraded (not down, just slow), check whether `payment-service`'s circuit breaker to that provider's adapter service has tripped as designed — if not and manual intervention is needed, prefer temporarily reducing the retry count for that provider (via `configuration-service`) over disabling the provider entirely, unless it's fully down.

## Rollback

Standard rollback per [`../deployment/kubernetes-guide.md#rollback`](../deployment/kubernetes-guide.md#rollback). Preserve Redis idempotency-key state across a rollback — do not flush Redis as part of remediation; in-flight idempotency records prevent duplicate processing during the rollback window itself.

See also: [`../operations/incident-response.md`](../operations/incident-response.md), [`../../services/payment-service/docs/ARCHITECTURE.md`](../../services/payment-service/docs/ARCHITECTURE.md).
