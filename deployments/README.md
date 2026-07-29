# Deployments

The gateway Helm chart is in `deployments/helm/pesaguard`. It is the application deployment source; the Kubernetes base folder contains supplemental namespace and network-policy controls. Apply the optional ServiceMonitor only where the Prometheus Operator is installed.

The repository now includes mTLS deployment assets for:
- Docker Compose: [docker-compose.mtls.yml](docker-compose.mtls.yml)
- Kubernetes: [kubernetes/base](kubernetes/base)
- NGINX: [nginx/gateway-mtls.conf](nginx/gateway-mtls.conf)
- Envoy: [envoy/gateway-mtls.yaml](envoy/gateway-mtls.yaml)

The Compose file mounts the generated PKI material directly from the repository PKI tree. The proxy configs expect the following files to be available in the container filesystem:
- /etc/nginx/certs/gateway.crt
- /etc/nginx/certs/gateway.key
- /etc/nginx/certs/ca.crt
- /etc/pesaguard/tls/ca.crt
- /etc/pesaguard/tls/gateway.crt
- /etc/pesaguard/tls/gateway.key
- /etc/pesaguard/tls/client.crt
- /etc/pesaguard/tls/client.key

Use staging first, run `scripts/ci/verify-gateway-staging.sh`, and promote the same immutable image digest to production. Production values must be supplied through a protected GitOps or CI/CD environment, never committed as secrets.
