
# PesaGuard

**PesaGuard** is a cloud-native, event-driven mobile money platform that provides real-time payment orchestration, transaction ledgering, and fraud detection for mobile money rails in Kenya — including **M-Pesa** and **Airtel Money** — with first-class support for bank settlement and Central Bank of Kenya (CBK) regulatory reporting.

The platform is built as a set of 30 independently deployable microservices behind a single API gateway, communicating asynchronously over Kafka using versioned, schema-registered domain events, and backed by PostgreSQL, Redis, and an observability stack of Prometheus, Grafana, and OpenTelemetry.

[![CI](https://img.shields.io/badge/build-passing-brightgreen)](.github/PULL_REQUEST_TEMPLATE.md)
[![License](https://img.shields.io/badge/license-Proprietary-blue)](LICENSE)
[![Security](https://img.shields.io/badge/security-policy-orange)](SECURITY.md)

---

## Table of contents

- [Why PesaGuard](#why-pesaguard)
- [Architecture at a glance](#architecture-at-a-glance)
- [Service catalog](#service-catalog)
- [Tech stack](#tech-stack)
- [Getting started](#getting-started)
- [Repository layout](#repository-layout)
- [Configuration](#configuration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Compliance](#compliance)
- [Documentation index](#documentation-index)
- [Contributing](#contributing)

## Why PesaGuard

Mobile money moves over 60% of Kenya's GDP in transaction value annually, and the fraud surface — SIM-swap takeover, mule account laundering, agent-float manipulation, social-engineering-driven STK push abuse — moves just as fast as the rails themselves. PesaGuard exists to give fintechs, banks, and payment aggregators a single, auditable system of record for:

- **Payment orchestration** across mobile money and bank rails, with idempotent request handling and automatic reconciliation.
- **Real-time fraud scoring** on every transaction, using velocity checks, device/SIM correlation, and mule-account graph analysis.
- **Double-entry ledgering** that is immutable, reversible only via compensating entries, and reconcilable against provider settlement files.
- **Regulatory-grade audit and reporting**, mapped directly to Kenya Data Protection Act (2019) and CBK prudential guidelines.

## Architecture at a glance

```
                              ┌─────────────────┐
                              │   API Gateway    │  ← single public entry point
                              │  (FastAPI, JWT)  │    authN/Z, rate limiting,
                              └────────┬─────────┘    request signing, routing
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
┌───────▼────────┐           ┌─────────▼─────────┐          ┌─────────▼────────┐
│  Core Domain    │           │   Payments &       │          │  Risk & Trust    │
│  Services       │           │   Money Movement   │          │  Services        │
│                 │           │                    │          │                  │
│  auth-service   │           │  mpesa-service     │          │  fraud-service   │
│  organization-  │           │  airtel-money-svc  │          │  risk-service    │
│    service      │           │  bank-service      │          │  audit-service   │
│  role-service   │           │  payment-service   │          │                  │
│  permission-svc │           │  transaction-svc   │          └──────────────────┘
│  user-service   │           │  ledger-service    │
│  customer-svc   │           │  settlement-svc    │
│  merchant-svc   │           │  reconciliation-svc│
│  branch-service │           │  billing-service   │
└─────────────────┘           │  subscription-svc  │
                               └────────────────────┘
        ┌──────────────────────────────┬──────────────────────────────┐
        │                              │                              │
┌───────▼────────┐           ┌─────────▼─────────┐          ┌─────────▼────────┐
│ Platform &      │           │ Integration &      │          │  Insight &       │
│ Developer Exp.  │           │ Communication       │          │  Operations      │
│                 │           │                    │          │                  │
│  api-mgmt-svc   │           │  webhook-service    │          │  analytics-svc   │
│  developer-     │           │  integration-svc    │          │  report-service  │
│    platform     │           │  sms-service        │          │  search-service  │
│  sdk-service    │           │  email-service       │          │  ai-service      │
│  feature-flag   │           │  notification-svc    │          │  health-service  │
│  configuration  │           │  document-service     │          │  scheduler-svc   │
│  file-service   │           │                        │          │  workflow-svc    │
└─────────────────┘           └────────────────────────┘          └──────────────────┘
                                       │
                          ┌────────────┴────────────┐
                          │   Kafka event backbone    │
                          │  (schema-registry-backed) │
                          └────────────┬───────────────┘
                                       │
                     ┌─────────────────┼─────────────────┐
                     │                 │                 │
              ┌──────▼─────┐   ┌───────▼──────┐   ┌──────▼──────┐
              │ PostgreSQL  │   │    Redis      │   │  OpenSearch │
              │ (per-svc DB)│   │ (cache/queue) │   │  (search/   │
              │             │   │               │   │   logs)     │
              └─────────────┘   └───────────────┘   └─────────────┘
```

Every service owns its own schema (database-per-service), publishes state changes as versioned events (`payment.completed.v1`, `fraud.flagged.v1`, `transaction.reversed.v1`, ...) documented under [`event-schemas/`](event-schemas/), and exposes a versioned REST API documented under [`api-specs/openapi/`](api-specs/openapi/).

## Service catalog

| Domain | Service | Responsibility |
|---|---|---|
| Identity | `auth-service` | Registration, login, JWT issuance, sessions, password reset |
| Identity | `role-service`, `permission-service` | RBAC role and permission graph |
| Identity | `user-service`, `organization-service`, `branch-service` | Tenant, user, and org-unit management |
| Commerce | `customer-service`, `merchant-service` | Customer and merchant onboarding/KYC |
| Money movement | `mpesa-service`, `airtel-money-service`, `bank-service` | Provider-specific payment rail adapters |
| Money movement | `payment-service`, `transaction-service` | Payment orchestration and transaction lifecycle |
| Money movement | `ledger-service`, `settlement-service`, `reconciliation-service` | Double-entry ledger, settlement, and reconciliation |
| Money movement | `billing-service`, `subscription-service` | Merchant billing and subscription plans |
| Risk & trust | `fraud-service`, `risk-service` | Real-time fraud scoring and risk rules |
| Risk & trust | `audit-service` | Immutable audit trail across all services |
| Communication | `notification-service`, `sms-service`, `email-service` | Multi-channel outbound notifications |
| Communication | `webhook-service`, `integration-service` | Outbound webhooks and third-party integrations |
| Communication | `document-service` | Statement, receipt, and report document generation |
| Platform | `api-management-service`, `developer-platform`, `sdk-service` | Public API keys, developer portal, SDK distribution |
| Platform | `feature-flag-service`, `configuration-service` | Runtime feature flags and service configuration |
| Platform | `file-service`, `search-service` | Object storage and full-text/faceted search |
| Insight | `analytics-service`, `report-service`, `ai-service` | Metrics, regulatory reports, ML-assisted insight |
| Operations | `health-service`, `scheduler-service`, `workflow-service` | Health aggregation, cron jobs, saga/workflow orchestration |

Each service's docs live at `services/<name>/README.md`, `services/<name>/docs/API.md`, and `services/<name>/docs/ARCHITECTURE.md`.

## Tech stack

| Layer | Technology |
|---|---|
| Language / runtime | Python 3.13 |
| API framework | FastAPI, Uvicorn (ASGI) |
| Data access | SQLAlchemy 2.x (async), Alembic migrations |
| Datastore | PostgreSQL 17 (per-service schema), Redis 7 (cache, rate limiting, idempotency) |
| Messaging | Apache Kafka, Confluent Schema Registry (Avro/JSON Schema) |
| AuthN/Z | JWT (HS256 dev / RS256+JWKS prod), Argon2 password hashing, scope-based authorization |
| Search & logs | OpenSearch |
| Observability | Prometheus, Grafana, OpenTelemetry tracing |
| Infra as code | Terraform, Helm, Kustomize |
| Orchestration | Kubernetes, Istio (mTLS, traffic policy), Argo CD (GitOps) |
| Secrets | HashiCorp Vault |
| CI/CD | GitHub Actions (see `.github/`) |

## Getting started

### Prerequisites

- Python 3.13+
- Docker and Docker Compose
- `make`

### Run the gateway + core dependencies locally

```bash
git clone https://github.com/Victor-Kipruto-Rop/pesaguard-mvp.git
cd pesaguard-mvp
docker compose up --build
```

This starts PostgreSQL, Redis, and the API gateway on `http://localhost:8000`. Interactive API docs are available at `http://localhost:8000/docs` in non-production environments.

### Run an individual service

```bash
cd services/mpesa-service
python3.13 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8080
```

### Common tasks

```bash
make gateway-run    # run the API gateway with autoreload
make gateway-test    # run the gateway test suite
```

See each service's `Makefile` for service-scoped equivalents.

## Repository layout

```
pesaguard-mvp/
├── gateway/            # Public API gateway (FastAPI) — auth, rate limiting, routing
├── services/           # 30 domain microservices, each independently deployable
├── shared/             # Cross-service Python libraries (auth, kafka, redis, telemetry, ...)
├── libs/                # Generated protobuf/gRPC clients and shared common-py utilities
├── packages/            # Publishable packages: event schemas, Python SDK
├── event-schemas/        # Versioned JSON Schema/Avro contracts for Kafka events
├── api-specs/            # OpenAPI (REST) and AsyncAPI (event) specifications
├── database/              # Cross-service schema docs, migrations, seeds, ERDs
├── infrastructure/        # Terraform, Kubernetes, Helm, Istio, Argo CD, Vault
├── monitoring/            # Grafana dashboards, Prometheus alerts, SLOs
├── security/               # Security policies, compliance mappings, scan templates
├── docs/                    # Architecture decision records, runbooks, operational guides
├── architecture/             # C4 diagrams, DDD and event-driven design notes
├── tests/                     # Integration, load, performance, security, stress suites
└── scripts/, tools/            # Developer tooling and automation scripts
```

## Configuration

All services follow a consistent `<SERVICE>_` environment variable convention (the gateway uses `PESAGUARD_`; each service prefixes with its own domain, e.g. `MPESA_`, `FRAUD_`). Copy the relevant `.env.example` to `.env` before running a service locally. Never commit populated `.env` files — production configuration is injected via Vault-backed Kubernetes secrets. See [`docs/security/data-classification.md`](docs/security/data-classification.md) and [`security/secrets-management/rotation-schedule.md`](security/secrets-management/rotation-schedule.md).

## Testing

| Suite | Location | Command |
|---|---|---|
| Unit | `services/<name>/tests/unit`, `tests/unit/` | `pytest -q` |
| Integration | `tests/integration/` | `pytest tests/integration -q` |
| Load | `tests/load/locustfile.py` | `locust -f tests/load/locustfile.py` |
| Performance | `tests/performance/k6-payment-flow.js` | `k6 run tests/performance/k6-payment-flow.js` |
| Security (DAST) | `tests/security/zap-baseline-config.md` | see OWASP ZAP baseline config |
| Stress | `tests/stress/stress-scenarios.md` | scenario-driven chaos/load tests |

## Deployment

Deployment targets Kubernetes via Helm charts under [`infrastructure/helm/`](infrastructure/helm/README.md) and GitOps sync via Argo CD ([`infrastructure/argocd/`](infrastructure/argocd/)). See [`docs/deployment/kubernetes-guide.md`](docs/deployment/kubernetes-guide.md), [`docs/deployment/helm-guide.md`](docs/deployment/helm-guide.md), and [`docs/deployment/release-process.md`](docs/deployment/release-process.md) for the full release process, including canary rollout and rollback procedure.

## Compliance

PesaGuard's data handling, retention, and access-control design maps directly to:

- **Kenya Data Protection Act, 2019** — see [`security/policies/kenya-dpa-compliance.md`](security/policies/kenya-dpa-compliance.md)
- **Central Bank of Kenya (CBK) prudential and payment service provider guidelines** — see [`security/policies/cbk-compliance.md`](security/policies/cbk-compliance.md)
- Internal data classification and retention policy — see [`security/policies/data-retention-policy.md`](security/policies/data-retention-policy.md) and [`docs/security/data-classification.md`](docs/security/data-classification.md)

Report a security issue by following [`SECURITY.md`](SECURITY.md).

## Documentation index

- Architecture: [`docs/architecture/overview.md`](docs/architecture/overview.md), [C4 diagrams](architecture/)
- Architecture Decision Records: [`docs/adr/`](docs/adr/)
- Database: [`docs/database/erd-overview.md`](docs/database/erd-overview.md)
- Operations & runbooks: [`docs/operations/`](docs/operations/), [`docs/runbooks/`](docs/runbooks/)
- API versioning policy: [`docs/api/versioning-policy.md`](docs/api/versioning-policy.md)
- Threat model: [`docs/security/threat-model.md`](docs/security/threat-model.md)

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for branch conventions, commit style, and the PR checklist. All contributions are subject to the [security policy](SECURITY.md) and [code of conduct](CONTRIBUTING.md#code-of-conduct).

## License

Proprietary — see [`LICENSE`](LICENSE). All rights reserved by the PesaGuard project maintainers.

