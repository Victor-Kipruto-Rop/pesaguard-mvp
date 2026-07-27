# Deployments

The gateway Helm chart is in `deployments/helm/pesaguard`. It is the application deployment source; the Kubernetes base folder contains supplemental namespace and network-policy controls. Apply the optional ServiceMonitor only where the Prometheus Operator is installed.

Use staging first, run `scripts/ci/verify-gateway-staging.sh`, and promote the same immutable image digest to production. Production values must be supplied through a protected GitOps or CI/CD environment, never committed as secrets.
