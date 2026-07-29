# Architecture overview

PesaGuard is a microservices platform for mobile money payment orchestration, ledgering, and real-time fraud detection, built around three architectural commitments: **database-per-service**, **event-driven integration by default**, and **a single public entry point (the gateway)**.

## Layers

1. **Edge**: the API gateway (`gateway/`) — the only component with a public-facing ingress. Terminates TLS, authenticates every request (JWT or API key), rate-limits, and routes to internal services over the cluster network.
2. **Domain services**: 30 services under `services/`, each a bounded context (see [Domain-Driven Design](../../architecture/domain-driven-design.md)) with its own PostgreSQL schema, API, and deployment lifecycle.
3. **Event backbone**: Kafka, carrying versioned domain events between services (see [Event-Driven Design](../../architecture/event-driven-design.md)).
4. **Shared infrastructure**: PostgreSQL, Redis, Kafka, OpenSearch, object storage — provisioned via Terraform (`infrastructure/terraform/`) and run on Kubernetes (`infrastructure/kubernetes/`, `infrastructure/helm/`).
5. **Cross-cutting libraries**: `shared/` (auth validation, kafka client, redis client, telemetry, middleware) consumed by every service to keep infrastructure concerns consistent without coupling business logic.

## Request lifecycle (synchronous)

```
Client → Gateway (authn/authz, rate limit, request ID) → Service (controller → service → repository → DB)
                                                              │
                                                              └─▶ publishes domain event → Kafka
```

## Request lifecycle (asynchronous)

```
Producer service → Kafka topic (schema-validated) → Consumer service(s) (idempotent handler) → local DB write / side effect
```

## Deployment topology

Every service is an independent container image, deployed via Helm chart, managed via Argo CD GitOps sync from this repository. Istio provides the service mesh: mTLS between all pods, and traffic policy (retries, circuit breaking, canary weighting) independent of application code. See [`../deployment/kubernetes-guide.md`](../deployment/kubernetes-guide.md).

## Observability

Every service exports Prometheus metrics (`/metrics`) and OpenTelemetry traces, correlated end-to-end via the gateway-issued `X-Request-ID` propagated through HTTP headers and Kafka message headers. Dashboards live in `monitoring/dashboards/`, alert rules in `monitoring/alerts/`, and SLOs in `monitoring/slo/`.

## Where to go next

- [C4 diagrams](../../architecture/) for progressively zoomed-in structural views
- [Domain model](domain-model.md) for the business entity relationships
- [Context map](context-map.md) for how bounded contexts relate to each other
- [Event storming](event-storming.md) for how the domain events were originally discovered
- [ADRs](../adr/) for the reasoning behind the major architectural decisions
