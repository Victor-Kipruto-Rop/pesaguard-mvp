# Pesaguard Shared Library

This package provides advanced, production-oriented building blocks for the Pesaguard platform. It includes resilient authentication helpers, typed configuration access, HTTP connectivity primitives, monitoring utilities, validation routines, and shared string/date helpers designed for reuse across services.

## Highlights

- Strongly typed environment configuration
- JWT-like token issuance and verification with expiry handling
- Retry-enabled HTTP client with JSON support
- Health check registry for service diagnostics
- Phone normalization and validation utilities
- Reusable date, ID, and string helpers

## Testing

Run the shared test suite with:

```bash
pytest shared/tests
```
