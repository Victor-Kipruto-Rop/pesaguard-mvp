# Contributing to PesaGuard

Thanks for your interest in improving PesaGuard. This document covers the workflow, standards, and checks your change needs to pass before merge.

## Table of contents

- [Code of conduct](#code-of-conduct)
- [Ways to contribute](#ways-to-contribute)
- [Development setup](#development-setup)
- [Branching and commits](#branching-and-commits)
- [Coding standards](#coding-standards)
- [Adding or changing a service](#adding-or-changing-a-service)
- [Database migrations](#database-migrations)
- [Event schema changes](#event-schema-changes)
- [Testing requirements](#testing-requirements)
- [Pull request checklist](#pull-request-checklist)
- [Review process](#review-process)

## Code of conduct

Be direct, be respectful, and assume good faith. Disagreements about technical approach are welcome in review; personal attacks are not. Report conduct concerns to the maintainers listed in `CODEOWNERS`.

## Ways to contribute

- **Bug reports** — use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md). Include the service name, environment, and a minimal reproduction.
- **Feature requests** — use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md). Explain the problem before proposing a solution.
- **Documentation** — docs live next to the code they describe (`services/<name>/README.md`, `docs/API.md`, `docs/ARCHITECTURE.md`). Fixes are always welcome.
- **Code** — see below.

## Development setup

```bash
git clone https://github.com/Victor-Kipruto-Rop/pesaguard-mvp.git
cd pesaguard-mvp
docker compose up --build   # postgres, redis, gateway
```

To work on a single service:

```bash
cd services/<service-name>
python3.13 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8080
```

## Branching and commits

- Branch from `main`: `feat/<short-description>`, `fix/<short-description>`, `chore/<short-description>`, `docs/<short-description>`.
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/): `feat(fraud-service): add SIM-swap correlation signal`.
- Keep commits scoped to one logical change. Squash noisy WIP commits before opening a PR.
- Reference the issue number in the PR description, not the commit message (`Closes #123`).

## Coding standards

- **Python 3.13**, type-hinted, formatted with `black` and linted with `ruff`. Run both before committing.
- **Layering**: each service follows `api → controllers → services → repositories → database`, with `interfaces/` defining repository/service contracts for testability. Don't call `database/` directly from `controllers/`.
- **Schemas**: request/response validation lives in `app/schemas/`; internal domain shape lives in `app/types/`. Don't reuse a Pydantic request schema as a response schema.
- **Config**: all environment variables are read once in `app/config/settings.py` via a typed settings object — never call `os.environ` elsewhere in application code.
- **Errors**: raise domain-specific exceptions from `app/exceptions/` (or `shared/exceptions/` for cross-service errors); let a single exception handler map them to HTTP responses. Don't catch-and-swallow.
- **Logging**: use the structured logger from `app/config/logging_config.py`. Never log secrets, full card/account numbers, or unmasked phone numbers — see `docs/security/data-classification.md`.

## Adding or changing a service

New services should mirror the existing layout (see any service under `services/` as a template):

```
services/<name>/
├── app/
│   ├── api/v1/, api/v2/       # versioned routers
│   ├── controllers/            # HTTP-facing handlers
│   ├── services/                # business logic
│   ├── repositories/             # data access, behind interfaces/
│   ├── schemas/                   # request/response models
│   ├── database/migrations/        # Alembic
│   └── ...
├── tests/{unit,integration,security,performance}/
├── docs/{API.md,ARCHITECTURE.md,README.md}
├── requirements.txt
└── README.md
```

Register the new service's base URL with the gateway (`PESAGUARD_<SERVICE>_SERVICE_URL`) and add its route prefix in `gateway/app/routes/`.

## Database migrations

- Use Alembic; generate with `alembic revision --autogenerate -m "<description>"` from within the service directory, then **review the generated migration by hand**.
- Migrations must be reversible (`downgrade()` implemented) unless the change is a documented, irreversible data cleanup.
- Never edit a migration that has been merged to `main`; write a new one.
- Add or update the relevant schema doc under `database/schemas/`.

## Event schema changes

- Event contracts live in `event-schemas/<domain>/<event>.v<N>.json` and are mirrored in `api-specs/asyncapi/`.
- Changes are **additive-only** within a version: new optional fields are fine; removing or retyping a field requires a new version (`payment.completed.v2`) with both versions published during a deprecation window.
- Update `event-schemas/schema-registry-config.md` compatibility mode expectations if a breaking change is unavoidable.

## Testing requirements

A PR must include or update tests appropriate to its change:

| Change type | Required tests |
|---|---|
| New endpoint | Unit tests for controller/service, integration test through the gateway |
| Bug fix | Regression test that fails without the fix |
| Migration | Migration applies cleanly against a seeded test database |
| Event producer/consumer change | Contract test against the schema in `event-schemas/` |

Run the full local suite before opening a PR:

```bash
pytest -q                                  # unit + integration for the touched service
cd gateway && pytest tests                  # gateway regression
```

## Pull request checklist

- [ ] Tests added/updated and passing locally
- [ ] `black` and `ruff` clean
- [ ] Relevant docs updated (`README.md`, `docs/API.md`, `docs/ARCHITECTURE.md`, or `database/schemas/`)
- [ ] No secrets, tokens, or `.env` files committed
- [ ] Breaking API or event changes are versioned, not in-place
- [ ] Linked issue referenced in the PR description

Use the [pull request template](.github/PULL_REQUEST_TEMPLATE.md) — it's applied automatically.

## Review process

- At least one approval from a `CODEOWNERS` entry for the touched path is required to merge.
- CI (lint, unit, integration, and security scan) must be green.
- Changes touching `shared/`, `gateway/`, `database/migrations/`, or `security/` require review from a maintainer with cross-service context, since they affect every service.
