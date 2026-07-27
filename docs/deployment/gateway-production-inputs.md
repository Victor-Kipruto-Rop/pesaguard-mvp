# Gateway production inputs

Before applying the chart, create an external secret named `pesaguard-gateway-secrets` in the `pesaguard` namespace. It must provide the gateway's private configuration, including downstream service credentials and any secret-store injected values. Alternatively, enable `externalSecret.enabled` and configure an installed External Secrets Operator `ClusterSecretStore` plus its data mappings.

Set the following non-secret Helm values per environment: immutable container image tag, ingress hostname/TLS secret, Redis endpoint, OIDC issuer/audience/JWKS URL, downstream internal URLs, trusted ingress proxy CIDRs, OpenTelemetry collector endpoint, resource sizing, and autoscaling limits.

The supplied network policy assumes NGINX Ingress is in the `ingress-nginx` namespace and internal services use ports 8080, 6379, 5432, or 443. Review and adapt those policies before applying them in a cluster with a different topology.

`gateway-service-monitor.yaml` is optional and requires the Prometheus Operator CRD. Apply it only in clusters where that operator is installed.

Run `scripts/ci/verify-gateway-staging.sh` after a staging rollout. It is read-only except for Kubernetes rollout-status polling and requires `GATEWAY_BASE_URL` and `KUBE_CONTEXT`.
