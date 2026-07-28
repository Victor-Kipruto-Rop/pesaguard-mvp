# Security Policy

PesaGuard handles regulated financial transaction data, personal data subject to the Kenya Data Protection Act (2019), and payment credentials. We take security reports seriously and ask that you report responsibly, privately, and with enough detail to reproduce.

## Supported versions

| Version | Supported |
|---|---|
| 1.4.x | ✅ |
| 1.3.x | ✅ (security fixes only) |
| 1.2.x | ❌ |
| < 1.2 | ❌ |

Only the two most recent minor versions receive security patches. Upgrade before reporting an issue against an unsupported version.

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Email **security@pesaguard.io** (PGP key available on request) with:

1. Affected service(s) and version/commit.
2. Vulnerability class (e.g., authentication bypass, injection, IDOR, secrets exposure).
3. Reproduction steps or proof-of-concept — request/response captures welcome, but redact any real customer data, phone numbers, or account identifiers.
4. Impact assessment as you see it.

### What to expect

| Stage | Timeline |
|---|---|
| Acknowledgement | Within 2 business days |
| Initial triage and severity assignment (CVSS 3.1) | Within 5 business days |
| Fix for Critical/High severity | Target 14 days |
| Fix for Medium/Low severity | Target 45 days |
| Public disclosure | Coordinated with reporter, typically 90 days post-fix or on reporter's reasonable request |

We do not currently operate a paid bug bounty program, but we credit reporters (with permission) in release notes.

## Scope

**In scope:**
- All services under `services/`, the `gateway/`, and `shared/` libraries in this repository.
- Infrastructure-as-code under `infrastructure/` (misconfigurations that would be exploitable if deployed as committed).
- Event schema and API contract issues that allow data leakage across tenants/organizations.

**Out of scope:**
- Third-party dependencies with their own disclosure process (report upstream; let us know so we can track the CVE).
- Denial-of-service via sheer volume (rate limiting is a known, deliberately tunable control — see `docs/security/threat-model.md`).
- Findings requiring physical access to infrastructure or social engineering of staff.
- Missing security headers or best-practice deviations with no demonstrated exploitability, on non-production/example configuration.

## Security controls summary

- **AuthN**: JWT (RS256/JWKS in production; HS256 permitted only in local development), Argon2id password hashing, mandatory MFA for privileged roles (see `security/policies/access-control-policy.md`).
- **AuthZ**: scope- and role-based access control enforced at the gateway and re-validated per service (defense in depth) — see `role-service` / `permission-service`.
- **Transport**: TLS 1.2+ externally; mTLS between services via Istio inside the cluster.
- **Secrets**: HashiCorp Vault-backed injection; no secrets in source control, container images, or environment files committed to git. Rotation schedule in `security/secrets-management/rotation-schedule.md`.
- **Data protection**: field-level encryption for PII/PAN-adjacent data at rest, masked in logs and non-production environments — see `docs/security/data-classification.md`.
- **Auditability**: `audit-service` maintains an append-only, hash-chained log of privileged and financial actions.
- **Dependency scanning**: automated SCA on every PR; template and cadence in `security/scans/dependency-scan-report-template.md`.
- **Regulatory mapping**: see `security/policies/kenya-dpa-compliance.md` and `security/policies/cbk-compliance.md`.

## Coordinated disclosure

We ask reporters to give us a reasonable window to remediate before public disclosure, and we commit to keeping reporters informed of remediation progress throughout. Thank you for helping keep PesaGuard and the people who rely on it safe.

