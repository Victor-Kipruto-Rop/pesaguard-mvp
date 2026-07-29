#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PKI_DIR="$ROOT_DIR/security/pki"
OUT_DIR="$ROOT_DIR/deployments/local-mtls"

mkdir -p "$OUT_DIR/certs" "$OUT_DIR/client" "$OUT_DIR/ca" "$OUT_DIR/nginx" "$OUT_DIR/envoy"

cp "$PKI_DIR/certs/gateway/gateway.crt" "$OUT_DIR/certs/gateway.crt"
cp "$PKI_DIR/private/gateway/gateway.key" "$OUT_DIR/certs/gateway.key"
cp "$PKI_DIR/chains/ca-bundle.pem" "$OUT_DIR/ca/ca.crt"
cp "$PKI_DIR/clients/gateway-client/gateway-client.crt" "$OUT_DIR/client/client.crt"
cp "$PKI_DIR/private/gateway-client/gateway-client.key" "$OUT_DIR/client/client.key"
cp "$ROOT_DIR/deployments/nginx/gateway-mtls.conf" "$OUT_DIR/nginx/gateway-mtls.conf"
cp "$ROOT_DIR/deployments/envoy/gateway-mtls.yaml" "$OUT_DIR/envoy/gateway-mtls.yaml"
cp "$ROOT_DIR/deployments/docker-compose.mtls.yml" "$OUT_DIR/docker-compose.mtls.yml"

cat > "$OUT_DIR/README.md" <<EOF
# Local mTLS deployment bundle

This directory contains a staged copy of the generated PKI material and deployment examples for local testing.

Contents:
- certs/gateway.crt
- certs/gateway.key
- ca/ca.crt
- client/client.crt
- client/client.key
- nginx/gateway-mtls.conf
- envoy/gateway-mtls.yaml
- docker-compose.mtls.yml
EOF

echo "[mtls] staged deployment assets to $OUT_DIR"
