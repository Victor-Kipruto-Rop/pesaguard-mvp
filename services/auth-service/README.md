# PesaGuard Authentication & Identity Service

This service provides the core authentication, authorization, session, organization, and audit primitives for the PesaGuard platform.

## Features

- User registration, login, logout, refresh, and password reset
- Argon2 password hashing and JWT issuance
- Organization creation with memberships and roles
- SQLAlchemy models and SQLite-backed development persistence
- FastAPI routes for auth and organizations

## Running locally

```bash
cd services/auth-service
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Testing

```bash
pytest -q tests/test_auth_flow.py
```
# PesaGuard Authentication Service

The authentication service issues development HS256 access/refresh tokens compatible with the API gateway: every token carries `sub`, `aud`, `iss`, `exp`, `type`, and a space-delimited `scope` claim. In production, use the gateway's OIDC/JWKS configuration rather than exposing symmetric signing material across services.

Copy `.env.example` to `.env` for local use. The gateway and auth service must share `SECRET_KEY`/`PESAGUARD_JWT_SECRET` only in local HS256 development; production must use an external asymmetric identity provider.
