# Backend architecture

TravelMate uses a modular backend foundation for a secure, compliance-aware API layer.

## Components

- FastAPI application entry point with security headers and CORS configuration
- Supabase JWT verification backed by JWKS and cached public keys
- centralized authorization and permission enforcement
- profile, user, verification, and session domain boundaries
- database models designed for Postgres/PostGIS and future SQLAlchemy migration work

## Design decisions

- Authenticated identity is derived from the verified token subject, not client input.
- Authentication and authorization are separated from admin-only endpoint logic.
- Security-sensitive state like verification and account status remains controlled server-side.
- Audit-friendly event logging and least-privilege checks are part of the platform foundation.
