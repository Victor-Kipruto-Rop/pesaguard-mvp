# Kubernetes deployment guide

## Cluster topology

PesaGuard runs on a single EKS cluster per environment (dev, staging, production), provisioned via [`../../infrastructure/terraform/`](../../infrastructure/terraform). Each environment is a separate cluster, not a namespace split of a shared cluster, to keep blast radius and IAM boundaries clean between environments.

Within a cluster:

| Namespace | Contents |
|---|---|
| `pesaguard` | Gateway and all 30 domain services |
| `pesaguard-data` | Self-managed stateful components not covered by managed AWS services (if any) |
| `istio-system` | Service mesh control plane |
| `monitoring` | Prometheus, Grafana, Alertmanager |
| `vault` | HashiCorp Vault (secrets injection) |
| `argocd` | GitOps controller |

## Prerequisites

- `kubectl` configured against the target cluster context
- Helm 3.x
- Cluster already has: NGINX Ingress, Istio, Prometheus Operator CRDs, External Secrets Operator, cert-manager

## Deploying a service

Services are deployed via their Helm chart under [`../../infrastructure/helm/`](../../infrastructure/helm). Standard flow (handled automatically by Argo CD in staging/production; manual for local cluster testing):

```bash
helm upgrade --install <service-name> infrastructure/helm/<service-name> \
  --namespace pesaguard \
  --values infrastructure/helm/<service-name>/values-<env>.yaml
```

Before deploying the gateway specifically, read [`gateway-production-inputs.md`](gateway-production-inputs.md) — it requires external secrets and environment-specific Helm values that are not safe to default.

## Health and readiness

Every service exposes `GET /health`, `GET /live`, and `GET /ready`, wired to Kubernetes liveness/readiness probes in its Helm chart. `/ready` fails closed if the service's database connection pool or Redis connection is unavailable — traffic is not routed to a pod that can't serve real requests, even if the process itself is alive.

## Rollout strategy

- Default: rolling update, `maxUnavailable: 0`, `maxSurge: 1` — no reduction in serving capacity during a deploy.
- Payment-critical services (`payment-service`, `transaction-service`, `ledger-service`, `mpesa-service`, `airtel-money-service`) additionally use Istio traffic mirroring to a canary replica for a defined bake period before shifting production traffic, per [`release-process.md`](release-process.md).

## Networking

Istio enforces mTLS between all pods in `pesaguard` namespace (`PeerAuthentication: STRICT`). Only the gateway has an Ingress; all other services are `ClusterIP`-only and unreachable from outside the mesh. Network policies additionally restrict which services can reach which — see [`gateway-production-inputs.md`](gateway-production-inputs.md#networking) for the assumed topology.

## Rollback

```bash
helm rollback <service-name> <revision> --namespace pesaguard
```

Argo CD-managed environments roll back by reverting the relevant commit in this repository (GitOps: the cluster state always matches `main`, or a tagged release branch for production).

See also: [`helm-guide.md`](helm-guide.md), [`release-process.md`](release-process.md), [`../operations/incident-response.md`](../operations/incident-response.md).
