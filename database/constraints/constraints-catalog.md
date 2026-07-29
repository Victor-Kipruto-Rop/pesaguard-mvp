# Database constraints catalog

## Purpose

Documents non-obvious or business-critical constraints enforced at the database layer across services — the ones that exist specifically to make an invalid financial or security state impossible to persist, not just discouraged by application logic. Straightforward `NOT NULL`/`UNIQUE` constraints are omitted here; see each service's `docs/ARCHITECTURE.md` for the full schema.

## Ledger (`ledger-service`)

| Constraint | Enforces |
|---|---|
| `CHECK (balanced_batch_sum(transaction_id) = 0)` (via trigger) | Every ledger entry batch for a transaction has debits summing to credits — a structurally unbalanced posting cannot commit |
| No `UPDATE`/`DELETE` grant on `ledger_entries` for any application role | Immutability — corrections happen only via new compensating entries |
| `CHECK (amount > 0)` on `ledger_entries.amount`, direction carried by `entry_type` (`debit`/`credit`) | Prevents sign-convention bugs from producing an incorrect balance |

## Payments (`payment-service`)

| Constraint | Enforces |
|---|---|
| `UNIQUE (merchant_id, idempotency_key)` on `payment_requests` | Duplicate submission with the same idempotency key cannot create a second payment request, even under concurrent requests (backed by an advisory lock at the application layer for the check-then-insert race) |
| `CHECK (amount > 0)` on `payment_requests.amount` | No zero or negative payment requests |
| `CHECK (status IN ('pending','processing','completed','failed','reversed'))` | Status is a closed set, changes go through application-validated transitions only |

## Transactions (`transaction-service`)

| Constraint | Enforces |
|---|---|
| `FOREIGN KEY (original_transaction_id) REFERENCES transactions(id)` on `transaction_reversals`, `ON DELETE RESTRICT` | A reversed transaction's original record cannot be deleted while a reversal references it |
| `CHECK (reversed_at IS NULL OR status = 'reversed')` | A transaction can't be marked reversed without a timestamp, or have a timestamp without the status |

## Auth (`auth-service`)

| Constraint | Enforces |
|---|---|
| `CHECK (expires_at > created_at)` on `sessions` | A session cannot be created already expired |
| `UNIQUE (lower(email))` on `users` | Case-insensitive email uniqueness |

## Audit (`audit-service`)

| Constraint | Enforces |
|---|---|
| No `UPDATE`/`DELETE` grant on `audit_entries` for any application role | Append-only log — see [`../../docs/security/threat-model.md`](../../docs/security/threat-model.md) |
| `CHECK (hash = compute_hash(prev_hash, payload))` (via trigger, see [`../functions/functions-catalog.md`](../functions/functions-catalog.md)) | Hash-chain integrity — a tampered entry breaks the chain verifiably |

## Fraud (`fraud-service`)

| Constraint | Enforces |
|---|---|
| `CHECK (decision IN ('flagged','cleared','confirmed_fraud'))` on `fraud_cases` | Closed decision set |
| A `transaction` with an open `fraud_case` cannot transition to `settled` in `settlement-service` (cross-service, enforced via event consumption, not a DB constraint — see [`../../architecture/domain-driven-design.md`](../../architecture/domain-driven-design.md)) | Documented here because it's the logical equivalent of a constraint, even though it can't be a literal foreign-key check across service boundaries |

See also: [`../../docs/database/schema-conventions.md`](../../docs/database/schema-conventions.md), [`../functions/functions-catalog.md`](../functions/functions-catalog.md).
