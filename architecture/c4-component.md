# C4 Model — Level 3: Component Diagram (representative service)

## Purpose

This view zooms into a single container — using `payment-service` as the representative example — to show its internal component structure. The same layering applies to all 30 services (see [`CONTRIBUTING.md`](../CONTRIBUTING.md#adding-or-changing-a-service)).

## Components

```
┌────────────────────────────────────────────────────────────────┐
│                        payment-service                          │
│                                                                  │
│  ┌───────────┐    ┌────────────┐    ┌───────────────┐          │
│  │ api/v1,v2  │───▶│ controllers │───▶│  services       │       │
│  │ (routers)  │    │ (HTTP glue) │    │  (business      │       │
│  └───────────┘    └────────────┘    │  logic +        │       │
│                                        │  business_rules) │       │
│                                        └───────┬──────────┘       │
│                                                 │                  │
│                       ┌─────────────────────────┼──────────┐      │
│                       ▼                         ▼          ▼      │
│              ┌────────────────┐      ┌──────────────┐ ┌────────┐ │
│              │ repositories     │◀────│ interfaces    │ │ cache   │ │
│              │ (data access)    │     │ (i_*_repo.py) │ │ (redis) │ │
│              └────────┬─────────┘      └──────────────┘ └────────┘ │
│                       ▼                                             │
│              ┌────────────────┐         ┌──────────────────┐        │
│              │ database/        │        │ events/            │       │
│              │ (SQLAlchemy,      │        │ (Kafka producers)   │       │
│              │  migrations)       │        └──────────────────┘       │
│              └────────────────┘                                       │
│                                                                        │
│  Cross-cutting: middleware/ (logging, rate limit, request ID),        │
│  dependencies/ (auth, db, pagination), telemetry/ (tracing, metrics), │
│  config/ (settings, logging_config)                                   │
└────────────────────────────────────────────────────────────────┘
```

## Component responsibilities

| Component | Responsibility | Depends on |
|---|---|---|
| `api/v{n}/` | Route definitions, versioned independently | `controllers/` |
| `controllers/` | Request parsing, response shaping — no business logic | `services/`, `schemas/` |
| `services/` | Business logic and rule enforcement (`*_business_rules.py`) | `repositories/` via `interfaces/` |
| `repositories/` | Data access, implements `interfaces/i_*_repository.py` | `database/` |
| `interfaces/` | Abstract contracts enabling repository/service substitution in tests | — |
| `database/` | SQLAlchemy models, session management, Alembic migrations | PostgreSQL |
| `schemas/` | Pydantic request/response/validation models | — |
| `serializers/` | Domain object → API representation mapping | `schemas/` |
| `dependencies/` | FastAPI dependency-injected auth, db session, pagination | `middleware/` |
| `middleware/` | Cross-cutting request handling (logging, rate limiting, request ID) | — |
| `telemetry/` | OpenTelemetry tracing spans, Prometheus metrics | — |
| `cache/` | Redis-backed read-through/write-through caching | Redis |
| `constants/`, `helpers/`, `types/` | Shared enums, pure functions, internal type definitions | — |

## Design rule

Controllers never talk to `database/` or `repositories/` directly — only through `services/`. This keeps business rules testable independent of HTTP and independent of the persistence technology, and is enforced in code review (see [`CONTRIBUTING.md`](../CONTRIBUTING.md#coding-standards)).
