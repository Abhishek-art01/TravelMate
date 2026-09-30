# Database and schema foundation

The TravelMate backend includes a SQLAlchemy model foundation intended for PostgreSQL/PostGIS deployment with future migration-based evolution.

## Core entities

- `users`
- `user_accounts`
- `profiles`
- `user_sessions`
- `verification_records`
- `audit_logs`

## Security model

- `users` stores the core account identity and account status.
- `user_accounts` records provider identity and provider metadata from verified login events.
- `user_sessions` stores session metadata such as device/platform and revocation state without storing raw secrets.
- `verification_records` keeps verification state separate from authentication state.
- `audit_logs` records security-sensitive actions without logging credentials, tokens, or raw documents.

## Migration approach

The project includes Alembic configuration and a baseline migration to preserve a clean database schema history while enabling incremental security and compliance changes.
