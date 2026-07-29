# `payments` schema

Owning service: `payment-service`. See [`../../services/payment-service/docs/ARCHITECTURE.md`](../../services/payment-service/docs/ARCHITECTURE.md).

## Tables

### `payment_requests`

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID` | Primary key |
| `merchant_id` | `UUID` | Logical FK to `merchant-service`; indexed |
| `organization_id` | `UUID` | Tenant scope |
| `amount` | `NUMERIC(19,4)` | Never `FLOAT` |
| `currency` | `CHAR(3)` | ISO 4217, `KES` in practice |
| `idempotency_key` | `VARCHAR(255)` | See uniqueness constraint below |
| `status` | `VARCHAR(20)` | `pending`, `processing`, `completed`, `failed`, `reversed` |
| `provider` | `VARCHAR(20)` | `mpesa`, `airtel_money`, `bank` |
| `customer_msisdn_encrypted` | `BYTEA` | Field-level encrypted; masked on any read outside `payment-service`/`audit-service` |
| `created_at`, `updated_at`, `deleted_at` | `TIMESTAMPTZ` | Standard columns |

### `payment_attempts`

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID` | Primary key |
| `payment_request_id` | `UUID` | FK to `payment_requests.id` |
| `provider_reference` | `VARCHAR(255)` | e.g., M-Pesa `CheckoutRequestID` |
| `attempt_number` | `INTEGER` | Increments per retry within the bound of `PESAGUARD_UPSTREAM_MAX_RETRIES`-equivalent policy |
| `status` | `VARCHAR(20)` | `initiated`, `awaiting_callback`, `succeeded`, `timed_out`, `rejected` |
| `raw_provider_response` | `JSONB` | Stored for debugging/reconciliation; PII fields within it are masked before storage |

## Constraints

- `UNIQUE (merchant_id, idempotency_key)` on `payment_requests` — the core defense against duplicate charges from client retries; enforced at the database level, not just application logic (see [`../../docs/security/threat-model.md`](../../docs/security/threat-model.md)).
- `CHECK (amount > 0)` on `payment_requests`.
- `payment_requests.status` transitions are validated in `app/services/payment_business_rules.py`; the database does not enforce a state machine directly, but a `status_history` audit table (below) makes any out-of-band transition detectable.

### `payment_status_history`

Append-only log of every status transition, written in the same transaction as the status change itself:

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID` | Primary key |
| `payment_request_id` | `UUID` | FK |
| `from_status`, `to_status` | `VARCHAR(20)` | |
| `changed_at` | `TIMESTAMPTZ` | |
| `changed_by` | `VARCHAR(50)` | System actor or user ID |

## Indexes

- `payment_requests(merchant_id, created_at)` — supports merchant dashboard queries
- `payment_requests(idempotency_key)` — supports the uniqueness constraint and fast retry-detection lookups
- `payment_attempts(payment_request_id)`
- `payment_attempts(provider_reference)` — supports fast lookup on provider callback

## Relationship to `transaction`/`ledger` schemas

A `payment_requests` row reaching `completed` status publishes `payment.completed.v1`; `transaction-service` creates its own `transactions` row in response (see [`ledger_schema.md`](ledger_schema.md)) — there is no direct foreign key across these schemas, only the event contract (see [`../../docs/database/erd-overview.md`](../../docs/database/erd-overview.md#cross-schema-references)).

See also: [`../../architecture/domain-model.md`](../../architecture/domain-model.md), [`../../event-schemas/payment/`](../../event-schemas/payment).
