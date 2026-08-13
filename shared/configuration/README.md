# PesaGuard Shared Configuration Module

This package provides an enterprise-grade configuration platform for every PesaGuard service. It is designed for fail-fast startup, strong validation, immutable settings, safe secret handling, and future extension to remote configuration stores.

## Architecture Overview

- `constants.py` — environment names, reserved settings keys, secret field markers, and defaults.
- `base.py` — shared `ConfigBase` and common Pydantic settings behavior.
- `environment.py` — environment detection and profile selection.
- `config.py` — complete application configuration object for gateway, API, DB, Redis, security, telemetry, and more.
- `loader.py` — file-based loading, hierarchical merge logic, and environment override support.
- `factory.py` — cached singleton configuration factory with registry and reload support.
- `manager.py` — high-level orchestration layer for services.
- `interfaces.py` — provider and hook abstractions for extensibility.
- `profiles/` — environment-specific defaults for development, testing, staging, and production.
- `schemas/` — strongly typed domain configuration components.
- `validators/` — domain-specific validation helpers.
- `utils/` — environment loading, secret masking, and file helpers.
- `exceptions/` — configuration-specific exception hierarchy.

## Capabilities

- Strong typing with `pydantic` and `pydantic-settings`
- Nested configuration domains for database, cache, security, monitoring, telemetry, email, notifications, storage, and feature flags
- Environment override support through `PESAGUARD_*` variables
- Validation of URLs, ports, timeouts, secrets, environment names, and feature flags
- Secret masking and safe export for structured logging and observability
- Singleton configuration registry with lazy loading and reload support
- Future-friendly interfaces for external secret providers and remote configuration stores

## Usage

```python
from shared.configuration import ConfigurationManager, get_configuration

config = get_configuration()
print(config.database.url)

manager = ConfigurationManager()
print(manager.export(mask_secrets=True))
```

## Environment Variables

- `PESAGUARD_ENVIRONMENT` — deployment environment name
- `PESAGUARD_CONFIG_PATH` — optional path to an explicit config file
- `PESAGUARD_CONFIG_VERSION` — optional schema version
- `PESAGUARD_*` — environment variables override nested configuration keys

## Validation Guide

- Configuration is validated on load and startup.
- Fail-fast behavior is preferred for invalid secrets, malformed URLs, or unsupported environments.
- Secret values are masked before serialization or export.

## Best Practices

- Do not read `os.environ` directly in services; use the shared configuration layer.
- Keep secrets in dedicated secret storage and provide them through env variables or secret hooks.
- Validate configuration during application startup and fail fast on invalid input.
- Use profile defaults for local development and testing, but override with environment-specific configuration in production.

## Supported Environments

- `development`
- `testing`
- `staging`
- `production`

## Extensibility

Add new domain settings to `schemas/` and expose them through `AppConfig`. The manager and interfaces provide a clean extension point for future remote configuration integrations and external secret providers.
