# Changelog

All notable changes to PesaGuard are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versioning follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `ai-service` groundwork for ML-assisted fraud triage summaries.
- `search-service` OpenSearch-backed transaction and merchant search.

### Changed
- Gateway upstream retry policy tuned to 2 retries with jittered backoff on `503`/`504` only.

### Security
- Rotated default development JWT signing material; production now enforces RS256/JWKS exclusively (see `docs/security/threat-model.md`).

---

## [1.4.0] — 2026-06-15

### Added
- `reconciliation-service`: automated end-of-day settlement reconciliation against M-Pesa and Airtel Money statement files, with variance flagging into `fraud-service`.
- `webhook-service`: HMAC-signed outbound webhook delivery with exponential backoff and dead-letter queue.
- Event schema `transaction.reversed.v1` for compensating-entry reversal flows.

### Changed
- `ledger-service` double-entry postings now require a balanced batch (sum of debits = sum of credits) enforced at the database constraint layer, not just application logic.
- Gateway rate limiting moved from in-memory to Redis-backed sliding window for multi-replica correctness.

### Fixed
- `payment-service`: idempotency key collisions under concurrent STK push retries resolved with an advisory lock on `(merchant_id, idempotency_key)`.

---

## [1.3.0] — 2026-04-02

### Added
- `fraud-service`: SIM-swap correlation signal, combining telco SIM-swap events with device-fingerprint change velocity.
- `risk-service`: mule-account graph analysis using shared-device and shared-recipient clustering.
- `audit-service`: immutable, append-only audit log with cryptographic chaining (each entry hashes the previous entry).

### Changed
- All services migrated database access to SQLAlchemy 2.x async engine.
- Kafka consumer groups renamed to `<service>.<environment>` for clearer multi-tenant isolation in shared clusters.

---

## [1.2.0] — 2026-02-10

### Added
- `bank-service`: bank settlement rail adapter alongside existing mobile money adapters.
- `analytics-service` and `report-service` split out of a single monolithic reporting service for independent scaling.
- CBK regulatory report templates under `security/policies/cbk-compliance.md`.

### Changed
- API gateway now issues correlation IDs (`X-Request-ID`) propagated through all downstream service calls and into Kafka event headers for end-to-end tracing.

### Deprecated
- `/api/v0/*` legacy routes; scheduled for removal in `2.0.0`. See `docs/api/versioning-policy.md`.

---

## [1.1.0] — 2025-12-05

### Added
- `airtel-money-service` as a second mobile money rail alongside `mpesa-service`.
- `notification-service` multi-channel fan-out (SMS via `sms-service`, email via `email-service`).
- Argo CD GitOps sync for all Kubernetes manifests.

### Fixed
- `auth-service`: refresh token replay window narrowed from 24h to 15 minutes after a security review.

---

## [1.0.0] — 2025-10-01

### Added
- Initial production release: `auth-service`, `organization-service`, `mpesa-service`, `payment-service`, `transaction-service`, `ledger-service`, `fraud-service`, `audit-service`, and the API gateway.
- Kafka event backbone with Confluent Schema Registry for `payment.*`, `transaction.*`, and `fraud.*` domain events.
- Terraform-managed AWS infrastructure (VPC, EKS, RDS PostgreSQL, MSK Kafka, ElastiCache Redis).
- Prometheus/Grafana observability stack and baseline SLOs (see `monitoring/slo/`).

[Unreleased]: https://github.com/Victor-Kipruto-Rop/pesaguard-mvp/compare/v1.4.0...HEAD
[1.4.0]: https://github.com/Victor-Kipruto-Rop/pesaguard-mvp/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/Victor-Kipruto-Rop/pesaguard-mvp/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/Victor-Kipruto-Rop/pesaguard-mvp/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/Victor-Kipruto-Rop/pesaguard-mvp/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/Victor-Kipruto-Rop/pesaguard-mvp/releases/tag/v1.0.0

