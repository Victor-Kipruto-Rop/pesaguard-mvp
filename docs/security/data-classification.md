# Data classification

## Classification levels

| Level | Definition | Examples |
|---|---|---|
| **Restricted** | Regulated financial/personal data; unauthorized disclosure has legal and customer-harm consequences | MSISDN (phone number), national ID number, bank account number, ledger balances, fraud case details |
| **Confidential** | Internal business data; disclosure harms the business but isn't independently regulated | Merchant pricing tiers, internal risk scores, API keys/secrets |
| **Internal** | Not for external release, low individual harm if disclosed | Service configuration, internal architecture docs |
| **Public** | Safe for external release | API documentation, marketing content |

## Handling rules by level

### Restricted

- **Encrypted at rest**: field-level encryption (application-layer, via `shared/cryptography/`) for MSISDN, national ID, and bank account fields, in addition to database-level encryption at rest.
- **Masked by default**: any restricted field returned by an API or written to a log is masked (e.g., `2547XXXXX123`) unless the caller has an explicit, audited "reveal" scope, and the reveal action itself is logged by `audit-service`.
- **Never in logs unmasked**: enforced by the shared structured logging library (`shared/logging/`), which masks known-sensitive field names automatically — do not bypass this by logging raw request/response bodies.
- **Retention**: governed by [`../../security/policies/data-retention-policy.md`](../../security/policies/data-retention-policy.md) and Kenya DPA requirements — see [`../../security/policies/kenya-dpa-compliance.md`](../../security/policies/kenya-dpa-compliance.md).
- **Access**: role- and scope-gated (see [`../../security/policies/access-control-policy.md`](../../security/policies/access-control-policy.md)); every access to restricted data by a human user is audit-logged, not just writes.

### Confidential

- Encrypted at rest (database-level), not necessarily field-level.
- Accessible to authenticated internal services and roles without the additional "reveal" audit step required for Restricted data.

### Internal / Public

- Standard access control (authenticated users for Internal; no restriction for Public); no special encryption requirement beyond transport TLS.

## Data flow implications

- Kafka events carrying Restricted fields (e.g., `payment.completed.v1` includes a masked MSISDN reference, not the raw number) are still transport-encrypted (mTLS) and access-controlled via Kafka ACLs, but event payloads themselves avoid carrying unmasked Restricted data where the consuming service doesn't need it — consumers that need the real value resolve it via a scoped call to the owning service instead.
- Non-production environments (staging, local dev) never contain real customer Restricted data — seed data is synthetic (`database/seeds/`), and any data-refresh-from-production process (if one exists) must anonymize Restricted fields first.

## Ownership

Each service's `docs/ARCHITECTURE.md` documents which classification level applies to each of its data fields. When adding a new field that could be Restricted or Confidential, default to the stricter classification and get explicit sign-off to downgrade it.

See also: [`threat-model.md`](threat-model.md), [`compliance-mapping.md`](compliance-mapping.md).
