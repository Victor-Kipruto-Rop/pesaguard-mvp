# `auth` schema

Owning service: `auth-service`. See [`../../services/auth-service/docs/ARCHITECTURE.md`](../../services/auth-service/docs/ARCHITECTURE.md) for the service's internal structure.

## Tables

### `users`

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID` | Primary key |
| `email` | `VARCHAR(255)` | Unique, case-insensitive index |
| `phone_number` | `VARCHAR(20)` | Encrypted at application layer; masked on read outside owning context |
| `password_hash` | `VARCHAR(255)` | Argon2id |
| `status` | `VARCHAR(20)` | `active`, `suspended`, `pending_verification` |
| `mfa_enabled` | `BOOLEAN` | Default `false`; enforced `true` for privileged roles at the application layer |
| `organization_id` | `UUID` | Logical FK to `organization-service` |
| `created_at`, `updated_at`, `deleted_at` | `TIMESTAMPTZ` | Standard columns |

### `sessions`

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID` | Primary key |
| `user_id` | `UUID` | FK to `users.id` |
| `refresh_token_hash` | `VARCHAR(255)` | Never store the raw refresh token |
| `expires_at` | `TIMESTAMPTZ` | Refresh token replay window — 15 minutes past issuance for the *previous* token once rotated |
| `revoked_at` | `TIMESTAMPTZ NULL` | Set on logout or forced revocation |
| `device_fingerprint` | `VARCHAR(255)` | Consumed by `fraud-service` for device-velocity signals |

### `roles` / `user_roles`

| Column | Type | Notes |
|---|---|---|
| `roles.id` | `UUID` | Primary key |
| `roles.name` | `VARCHAR(100)` | Unique within `organization_id` |
| `user_roles.user_id`, `user_roles.role_id` | `UUID` | Composite unique key |

Fine-grained permission definitions live in the `permission-service`-owned schema, referenced logically by `role_id`.

### `organizations` (mirror)

`auth-service` maintains a minimal read-mirror of `organization_id → status` (populated from `organization.created.v1`/`organization.status_changed.v1` events) so that token issuance can check org status without a synchronous call to `organization-service` on every login — a small, deliberate CQRS-style read model (see [`../../architecture/cqrs-design.md`](../../architecture/cqrs-design.md)).

### `password_reset_tokens`

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID` | Primary key |
| `user_id` | `UUID` | FK to `users.id` |
| `token_hash` | `VARCHAR(255)` | Single-use, hashed |
| `expires_at` | `TIMESTAMPTZ` | 15-minute validity |
| `used_at` | `TIMESTAMPTZ NULL` | Set on consumption; a used token cannot be reused |

## Indexes

- `users(email)` — unique, case-insensitive (`lower(email)`)
- `users(organization_id)`
- `sessions(user_id, expires_at)` — supports active-session lookups
- `user_roles(user_id, role_id)` — composite unique

## Constraints

- `sessions.expires_at` must be greater than `sessions.created_at` (check constraint)
- `users.status = 'active'` required before a session can be created (enforced in application logic, not a DB trigger, to keep the status transition rules centralized in `services/`)

See also: [`../../docs/database/schema-conventions.md`](../../docs/database/schema-conventions.md), [`../../services/auth-service/docs/API.md`](../../services/auth-service/docs/API.md).
