# Domain model

## Core entities and relationships

```
Organization 1──* Branch
Organization 1──* Membership *──1 User
User *──* Role *──* Permission

Merchant 1──* PaymentRequest 1──* PaymentAttempt
PaymentAttempt 1──1 MpesaTransaction | AirtelTransaction | BankTransfer

PaymentRequest 1──1 Transaction
Transaction 1──* LedgerEntry
Transaction 0..1──1 TransactionReversal

Transaction 0..1──1 FraudCase
FraudCase *──1 RiskScore

SettlementBatch 1──* SettlementLine *──1 Transaction

AuditEntry *──1 (any aggregate, by entity_type + entity_id)
```

## Entity summary

| Entity | Owning service | Key attributes |
|---|---|---|
| `Organization` | `organization-service` | name, KRA PIN, tier, status |
| `Branch` | `branch-service` | organization_id, till/paybill number |
| `User` | `user-service` | email, phone (MSISDN, masked at rest), status |
| `Role` / `Permission` | `role-service` / `permission-service` | scope, resource, action |
| `Merchant` | `merchant-service` | organization_id, settlement account, KYC status |
| `PaymentRequest` | `payment-service` | amount, currency, idempotency_key, status |
| `PaymentAttempt` | `payment-service` | payment_request_id, provider, provider_reference |
| `MpesaTransaction` | `mpesa-service` | MpesaReceiptNumber, phone (masked), checkout_request_id |
| `Transaction` | `transaction-service` | payment_request_id, amount, direction, status |
| `TransactionReversal` | `transaction-service` | original_transaction_id, reason, compensating_entries |
| `LedgerEntry` | `ledger-service` | account_id, debit/credit, amount, transaction_id |
| `FraudCase` | `fraud-service` | transaction_id, signals[], decision, reviewed_by |
| `RiskScore` | `risk-service` | subject_type, subject_id, score, model_version |
| `SettlementBatch` | `settlement-service` | provider, period, total_amount, status |
| `AuditEntry` | `audit-service` | actor, action, entity_type, entity_id, prev_hash |

## Invariants enforced at the domain layer

- A `PaymentRequest` cannot transition from `completed` back to `pending` — only forward or into `reversed` via a `TransactionReversal`.
- Every `LedgerEntry` batch for a `Transaction` must balance (sum of debits = sum of credits), enforced as a database constraint in `ledger-service` (see [`../../database/schemas/ledger_schema.md`](../../database/schemas/ledger_schema.md)).
- A `Transaction` with an open `FraudCase` cannot settle until the case is `cleared` or explicitly overridden by an authorized compliance role.
- `AuditEntry` records are append-only and hash-chained; no service has an `UPDATE`/`DELETE` grant on the audit table.

See also: [Domain-Driven Design](../../architecture/domain-driven-design.md), [Database ERD overview](../database/erd-overview.md).
