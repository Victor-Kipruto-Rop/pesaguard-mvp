# Release process

## Branching and environments

- `main` deploys continuously to **staging** via Argo CD on every merge.
- Production releases are cut from `main` as an annotated tag (`vX.Y.Z`) once staging validation passes; Argo CD's production application tracks the tag, not `main` directly.

## Release checklist

1. **Merge freeze window opens** for the release branch — only fixes for release-blocking issues merge during this window.
2. **Staging soak**: the release candidate runs in staging for a minimum bake period (24h for a minor/patch release, 72h for a release touching `payment-service`, `transaction-service`, `ledger-service`, or `fraud-service`).
3. **Automated gates**, all required green: unit + integration test suites, [`../../tests/security/zap-baseline-config.md`](../../tests/security/zap-baseline-config.md) DAST scan, dependency scan ([`../../security/scans/dependency-scan-report-template.md`](../../security/scans/dependency-scan-report-template.md)), and load test against staging ([`../../tests/load/locustfile.py`](../../tests/load/locustfile.py)) at 1.5x expected peak.
4. **Tag the release**: `git tag -a vX.Y.Z -m "..."`, update [`CHANGELOG.md`](../../CHANGELOG.md).
5. **Canary rollout to production**: for payment-critical services, Istio shifts 5% → 25% → 50% → 100% of traffic over a defined bake period, with automatic rollback if error rate or p95 latency exceeds threshold at any stage.
6. **Non-payment-critical services** deploy directly via rolling update (see [`kubernetes-guide.md`](kubernetes-guide.md#rollout-strategy)) — canary is reserved for services on the money-movement critical path.
7. **Post-release verification**: run `scripts/ci/verify-gateway-staging.sh`-equivalent smoke checks against production; confirm dashboards in `monitoring/dashboards/` show nominal error rate and latency.

## Rollback triggers

Any of the following triggers an immediate rollback per [`kubernetes-guide.md#rollback`](kubernetes-guide.md#rollback):

- Error rate exceeds SLO threshold for the affected service (see `monitoring/slo/`)
- Payment success rate drops below baseline by more than 2 percentage points
- A `Sev1`/`Sev2` incident is opened referencing the release (see [`../operations/incident-response.md`](../operations/incident-response.md))

## Hotfixes

A hotfix branches from the last production tag, not from `main`, to avoid pulling in unrelated unreleased changes. It follows the same automated gates but with an abbreviated (4h minimum) staging soak for `Sev1`-triggered fixes, requiring sign-off from a second engineer.

## Communication

Release notes are published to `CHANGELOG.md` and, for merchant-facing API changes, surfaced through `developer-platform`. Internal stakeholders (Ops, Compliance) are notified via the on-call channel referenced in [`../operations/oncall-guide.md`](../operations/oncall-guide.md).

See also: [`kubernetes-guide.md`](kubernetes-guide.md), [`helm-guide.md`](helm-guide.md).
