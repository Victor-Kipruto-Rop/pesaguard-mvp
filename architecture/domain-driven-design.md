# Domain-Driven Design in PesaGuard

## Bounded contexts

Each of the 30 services in `services/` is a bounded context with its own ubiquitous language, data model, and database schema. Boundaries were drawn along transactional consistency needs, not organizational convenience — a service exists where strong consistency (a single ACID transaction) is required, and events carry state across the boundary everywhere else.

| Bounded context | Aggregate roots | Owning service |
|---|---|---|
| Identity & access | `User`, `Role`, `Permission`, `Session` | `auth-service`, `role-service`, `permission-service` |
| Organization | `Organization`, `Branch`, `Membership` | `organization-service`, `branch-service` |
| Payments | `PaymentRequest`, `PaymentAttempt` | `payment-service` |
| Money rails | `MpesaTransaction`, `AirtelTransaction`, `BankTransfer` | `mpesa-service`, `airtel-money-service`, `bank-service` |
| Transactions | `Transaction`, `TransactionReversal` | `transaction-service` |
| Ledger | `LedgerEntry`, `LedgerAccount` | `ledger-service` |
| Settlement | `SettlementBatch`, `SettlementLine` | `settlement-service`, `reconciliation-service` |
| Fraud & risk | `FraudCase`, `RiskScore`, `RiskRule` | `fraud-service`, `risk-service` |
| Audit | `AuditEntry` | `audit-service` |

## Strategic design: context mapping

Relationships between contexts follow these patterns (see [`docs/architecture/context-map.md`](../docs/architecture/context-map.md) for the full map):

- **Customer/Supplier**: `payment-service` is a customer of `mpesa-service`/`airtel-money-service`/`bank-service` — the rail services define the contract, payment orchestration adapts to it.
- **Conformist**: `mpesa-service` conforms to the external Safaricom Daraja API shape internally, translating to PesaGuard's canonical `PaymentRequest` only at its boundary (anti-corruption layer in `app/helpers/mpesa_helpers.py`).
- **Published Language**: all cross-context integration beyond direct request/response uses the versioned event schemas in `event-schemas/` as the shared contract — no context reaches into another's database.
- **Shared Kernel**: `shared/` contains only technical concerns (auth validation, telemetry, kafka client wrappers) — never domain model code, to avoid coupling business logic across contexts.

## Tactical design inside a context

Within each service:

- **Aggregate root** — the entity that owns transactional consistency (e.g., `PaymentRequest` owns its `PaymentAttempt` children; you cannot modify an attempt except through the request).
- **Repository** — one per aggregate root, defined by an `interfaces/i_*_repository.py` contract and implemented in `repositories/`.
- **Domain services** (`app/services/*_business_rules.py`) — logic that doesn't naturally belong to a single aggregate (e.g., idempotency-key conflict resolution).
- **Value objects** — immutable, defined in `app/types/`, e.g., `Money`, `PhoneNumber`, `MSISDN`.

## Anti-patterns avoided

- No "anemic domain model" — business rules live in `services/`, not scattered across controllers.
- No shared database across bounded contexts, even for convenience joins — cross-context data needs are served by consuming published events into a local read model.
- No god aggregate — `Transaction` does not reach into `LedgerEntry` internals; it publishes `transaction.created.v1` and `ledger-service` reacts.

See also: [`event-driven-design.md`](event-driven-design.md), [`cqrs-design.md`](cqrs-design.md), [`docs/architecture/domain-model.md`](../docs/architecture/domain-model.md).
