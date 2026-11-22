# Security notes

CyberWatch is a portfolio/demo application. It is not hardened for internet-facing or multi-tenant deployment.

## Current controls

- Request payloads are validated with Pydantic.
- CSV uploads are limited to 5 MB and 1,000 rows.
- API requests are rate-limited per client IP in a single process.
- Write-request audit metadata is stored in SQLite; request bodies, credentials and client IP addresses are not stored in the audit table.
- Audit history is capped at the latest 10,000 entries.
- SQLite event and alert data persist across local restarts.

## Important limitations

- There is no user authentication, authorization or tenant isolation.
- The in-memory rate limiter is not shared across workers or replicas and should not be treated as a distributed abuse control.
- WebSocket connections are unauthenticated.
- The local SQLite database is not encrypted by the application.
- The default CORS allowlist is intended for localhost development.
- TLS termination, secrets management, backup/restore, retention policy and operational monitoring are deployment responsibilities.

## Safe usage

1. Run locally or in a private development environment.
2. Use the bundled synthetic sample events or sanitized logs only.
3. Do not expose the API or WebSocket endpoint directly to the public internet.
4. Before production use, add identity and role-based authorization, TLS, distributed rate limiting, network controls, database encryption/managed storage, audit retention policy and a security review.
5. Review the model card before interpreting anomaly scores as security findings.

Report suspected vulnerabilities through the repository's GitHub Security Advisories rather than posting exploit details in public issues.
