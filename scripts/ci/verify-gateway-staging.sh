#!/usr/bin/env bash
set -euo pipefail

: "${GATEWAY_BASE_URL:?Set GATEWAY_BASE_URL to the HTTPS staging gateway URL}"
: "${KUBE_CONTEXT:?Set KUBE_CONTEXT to the staging cluster context}"

kubectl --context "$KUBE_CONTEXT" -n pesaguard rollout status deployment/pesaguard-gateway --timeout=180s
curl --fail --silent --show-error --max-time 10 "$GATEWAY_BASE_URL/live" | grep -q 'alive'
curl --fail --silent --show-error --max-time 10 "$GATEWAY_BASE_URL/ready" | grep -q 'ready'
curl --fail --silent --show-error --max-time 10 "$GATEWAY_BASE_URL/metrics" | grep -q 'pesaguard_gateway_requests_total'
echo "Gateway staging verification passed."
