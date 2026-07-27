# Operational scripts

`ci/verify-gateway-staging.sh` is the gateway post-deploy smoke test. It is deliberately read-only and needs a valid Kubernetes context plus `GATEWAY_BASE_URL`.

Database scripts are operational entry points and must be run only through the approved CI/CD identity. Do not run backup, migration, seed, or image-push scripts from a developer workstation against production.
