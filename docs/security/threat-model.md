# Threat model

## Method

STRIDE applied per bounded context, with additional focus on payment-fraud-specific threat classes given PesaGuard's domain. Reviewed at each major architecture change and at minimum annually.

## High-priority threats and mitigations

| Threat | Category | Mitigation |
|---|---|---|
| SIM-swap takeover used to intercept STK push/OTP | Spoofing | `fraud-service` SIM-swap correlation signal (telco feed + device-fingerprint velocity); step-up verification on high-risk transactions |
| Mule account layering (structuring transactions to evade detection) | Repudiation / fraud | `risk-service` graph-based mule account clustering across shared device/recipient signals |
| Replay of a captured payment request | Spoofing / tampering | Mandatory `Idempotency-Key`, short-lived JWTs, gateway-enforced request signing for API-key clients |
| Duplicate payment processing from client retry | Tampering (unintentional) | Idempotency key enforced at the database layer (unique constraint on `(merchant_id, idempotency_key)`), not just application logic |
| Privilege escalation via role/permission misconfiguration | Elevation of privilege | `role-service`/`permission-service` scope model reviewed in `security/policies/access-control-policy.md`; least-privilege default, no wildcard scopes in production |
| Cross-tenant data access (organization A reading organization B's data) | Information disclosure | `organization_id` enforced at the query layer in every repository, not just the API layer; tested explicitly in service integration tests |
| Compromised service credentials used for lateral movement | Elevation of privilege | Istio mTLS between all services; Vault-issued short-lived service credentials, no long-lived static service-to-service secrets |
| Kafka event tampering/injection | Tampering | Schema Registry validation rejects malformed events at the broker boundary; mTLS + ACLs on Kafka topics restrict which service identities can produce to which topics |
| Ledger entry tampering (post-hoc edit) | Tampering / repudiation | Ledger entries are immutable (no `UPDATE`/`DELETE` grant); corrections only via new balancing entries; `audit-service` hash-chains all privileged actions |
| Denial of service against the gateway | Denial of service | Redis-backed rate limiting, per-client and global; Istio circuit breaking on upstream calls |
| PII exposure in logs | Information disclosure | Structured logging with automatic masking of MSISDN, email, and other PII fields (see [`data-classification.md`](data-classification.md)); log access restricted and audited |

## Trust boundaries

```
[Internet] ──(TLS)── [Gateway] ──(mTLS, Istio mesh)── [Domain services] ──(mTLS)── [Datastores]
                                        │
                                  (mTLS + ACL) 
                                        ▼
                                     [Kafka]
```

The gateway is the only trust boundary crossing from untrusted (internet) to trusted (mesh) network. No domain service is reachable except through the mesh — see [`../deployment/kubernetes-guide.md#networking`](../deployment/kubernetes-guide.md#networking).

## Out of scope for this model

Physical security of cloud provider data centers (delegated to AWS's shared responsibility model) and endpoint security of engineer workstations (covered separately under corporate IT policy).

See also: [`compliance-mapping.md`](compliance-mapping.md), [`data-classification.md`](data-classification.md), [`../../SECURITY.md`](../../SECURITY.md).
