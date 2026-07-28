# C4 Model — Level 2: Container Diagram

## Purpose

This view expands PesaGuard into its deployable units ("containers" in C4 terms): the gateway, the 30 microservices, datastores, and the event backbone. See [`c4-context.md`](c4-context.md) for the system-level view.

## Containers

| Container | Technology | Responsibility |
|---|---|---|
| API Gateway | FastAPI / Uvicorn | Single public entry point: JWT/API-key auth, rate limiting, request routing, response hardening |
| Domain services (×30) | FastAPI / Uvicorn, one per bounded context | See [service catalog](../README.md#service-catalog) |
| PostgreSQL (per service) | PostgreSQL 17 | System of record for each service's bounded context; no cross-service schema access |
| Redis | Redis 7 | Rate limiting, idempotency keys, caching, short-lived session state |
| Kafka | Apache Kafka + Confluent Schema Registry | Asynchronous domain event backbone between services |
| OpenSearch | OpenSearch | Full-text/faceted search (`search-service`), centralized log indexing |
| Object storage | S3-compatible | Document and file storage (`file-service`, `document-service`) |

## Interaction style

- **Synchronous (request/response)**: client → gateway → service, over HTTP/JSON, always through the gateway. Services never call each other synchronously across bounded contexts except through the gateway or well-defined internal client libraries in `shared/clients/`.
- **Asynchronous (event-driven)**: services publish domain events to Kafka on state transitions (e.g., `payment-service` publishes `payment.completed.v1`); interested services consume independently. This is the default integration style for anything that isn't a direct user-facing request — see [`event-driven-design.md`](event-driven-design.md).
- **Service mesh**: Istio provides mTLS between all containers inside the cluster and enforces network policy independent of application-layer auth.

## Data ownership

Each service owns its PostgreSQL schema exclusively. Cross-service reads happen either through the owning service's API or through denormalized read models built from consumed events (CQRS — see [`cqrs-design.md`](cqrs-design.md)), never through direct database access across service boundaries.

## Diagram

```
 [Merchant/Customer/Analyst]
            │
            ▼
     ┌─────────────┐
     │ API Gateway  │
     └──────┬───────┘
            │ HTTPS/JWT
   ┌────────┼─────────────────────────────┐
   ▼        ▼                             ▼
┌──────┐ ┌──────────┐   ...30 services...  ┌──────────┐
│ auth │ │ payment   │                      │ fraud     │
│ -svc │ │ -service  │                      │ -service  │
└───┬──┘ └────┬─────┘                      └────┬─────┘
    │         │  ▲ publish/consume               │
    ▼         ▼  │                                ▼
 ┌──────┐  ┌──────┐   ┌───────────────┐      ┌──────┐
 │Postgres│ │Postgres│  │ Kafka +        │◀────▶│Postgres│
 │(auth)  │ │(payment)│ │ Schema Registry │      │(fraud) │
 └──────┘  └──────┘   └───────────────┘      └──────┘
```

Related: [`c4-component.md`](c4-component.md) for internal service structure, [`domain-driven-design.md`](domain-driven-design.md) for how bounded contexts map to services.
