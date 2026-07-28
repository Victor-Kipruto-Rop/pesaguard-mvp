# Context map

This maps the relationship *type* between bounded contexts (see [Domain-Driven Design](../../architecture/domain-driven-design.md) for definitions).

| Upstream context | Downstream context | Relationship | Integration mechanism |
|---|---|---|---|
| `mpesa-service` | `payment-service` | Conformist / Anti-corruption layer | `payment.initiated.v1` event + synchronous callback ingestion |
| `airtel-money-service` | `payment-service` | Conformist / Anti-corruption layer | Event + synchronous callback ingestion |
| `bank-service` | `settlement-service` | Customer/Supplier | `settlement.*` events |
| `payment-service` | `transaction-service` | Partnership (co-evolve) | `payment.completed.v1`, `payment.failed.v1` |
| `transaction-service` | `ledger-service` | Customer/Supplier | `transaction.created.v1`, `transaction.reversed.v1` |
| `transaction-service` | `fraud-service` | Customer/Supplier | `transaction.created.v1` (async) + synchronous pre-transaction score call |
| `fraud-service` | `transaction-service` | Customer/Supplier | `fraud.flagged.v1` (hold), `fraud.cleared.v1` (release) |
| `auth-service` | *all services* | Open Host Service | JWT with scope claims, validated locally by each service via `shared/authentication/` |
| `role-service` / `permission-service` | *all services* | Open Host Service | Scope definitions consumed at token-issuance and request-authorization time |
| `organization-service` | `merchant-service`, `branch-service`, `user-service` | Shared Kernel (tenant identity only) | `organization_id` foreign key convention, no shared tables |
| `audit-service` | *all services* | Published Language | Every privileged/financial action publishes to a common `audit.action.v1` event shape |
| `notification-service` | `sms-service`, `email-service` | Customer/Supplier | `notification.sms.v1`, `notification.email.v1` |
| `analytics-service`, `report-service`, `search-service` | *upstream domain services* | Conformist (read-only consumer) | Consume events only; never write back upstream |

## Anti-corruption layers

External provider integrations (`mpesa-service`, `airtel-money-service`, `bank-service`) each maintain an anti-corruption layer in `app/helpers/` that translates provider-specific payloads (Safaricom Daraja's STK push callback shape, Airtel's webhook format) into PesaGuard's canonical `PaymentAttempt` representation before anything crosses into `payment-service`. This keeps provider API churn from leaking into the core domain model.

## Shared kernel discipline

The only genuinely shared code across contexts lives in `shared/` and is deliberately limited to technical, not domain, concerns: authentication token validation, Kafka producer/consumer wrappers, Redis client, telemetry instrumentation, and common exception/response shapes. No context imports another context's domain model types directly.

See also: [Domain model](domain-model.md), [Event-Driven Design](../../architecture/event-driven-design.md).
