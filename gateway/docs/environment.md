# Environment configuration

Copy `.env.example` to `.env` only for local development. The `PESAGUARD_` prefix maps directly to typed `Settings` fields. List settings use JSON arrays. Production configuration must use a 32+ character JWT secret, explicit CORS origins, and explicit trusted hosts.
