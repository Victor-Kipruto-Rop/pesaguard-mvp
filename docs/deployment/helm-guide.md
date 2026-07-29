# Helm chart guide

## Chart layout

Every service has its own chart under [`../../infrastructure/helm/<service-name>/`](../../infrastructure/helm), following a common structure so charts stay predictable across 30+ services:

```
infrastructure/helm/<service-name>/
├── Chart.yaml
├── values.yaml               # defaults (safe for local/dev)
├── values-staging.yaml        # staging overrides
├── values-production.yaml      # production overrides
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── hpa.yaml                # HorizontalPodAutoscaler
    ├── servicemonitor.yaml      # Prometheus Operator scrape config
    ├── networkpolicy.yaml
    └── externalsecret.yaml       # only if externalSecret.enabled
```

A shared library chart (`infrastructure/helm/_common/`) provides reusable template snippets (standard labels, probe definitions, resource block) that every service chart depends on — this keeps 30 charts consistent without 30 copies of boilerplate.

## Key values

| Value | Purpose | Default |
|---|---|---|
| `image.repository`, `image.tag` | Container image; tag is always an immutable digest or semver, never `latest`, in staging/production | — |
| `replicaCount` | Base replica count before HPA takes over | `2` |
| `autoscaling.minReplicas` / `maxReplicas` | HPA bounds | `2` / `10` |
| `resources.requests` / `resources.limits` | CPU/memory | Set per service based on load-tested baseline |
| `externalSecret.enabled` | Pull secrets via External Secrets Operator instead of a manually created `Secret` | `false` (dev), `true` (staging/production) |
| `env.*` | Non-secret environment configuration, service-specific `<SERVICE>_` prefix | — |

## Installing/upgrading

```bash
helm upgrade --install <service-name> infrastructure/helm/<service-name> \
  --namespace pesaguard \
  --values infrastructure/helm/<service-name>/values-<env>.yaml \
  --set image.tag=<git-sha-or-semver>
```

## Linting and testing a chart change

```bash
helm lint infrastructure/helm/<service-name>
helm template infrastructure/helm/<service-name> --values infrastructure/helm/<service-name>/values-staging.yaml | kubectl apply --dry-run=server -f -
```

Both are run in CI on any PR touching `infrastructure/helm/`.

## Adding a chart for a new service

Copy an existing chart with a similar profile (e.g., a stateless FastAPI service with no special networking needs), rename, and update `Chart.yaml`, `values.yaml` image repository, and any service-specific environment variables. Register the chart in Argo CD's application set (`infrastructure/argocd/`) so it's picked up by GitOps sync.

See also: [`kubernetes-guide.md`](kubernetes-guide.md), [`gateway-production-inputs.md`](gateway-production-inputs.md), [`../../infrastructure/helm/README.md`](../../infrastructure/helm/README.md).
