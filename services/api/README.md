# TravelMate API Service

This service provides the FastAPI foundation for the TravelMate platform.

## Required runtime

Use Python 3.12 for local development.

## Quick start

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Included foundation

- FastAPI app bootstrap
- health and readiness endpoints
- environment-based configuration
- Supabase auth abstraction boundary
- security helper boundary
- OpenAPI-ready API contract
- `/api/v1/admin/access` for backend-authoritative admin permission discovery
- `/api/v1/admin/system` protected by `system.manage`

Admin access discovery requires at least one configured administrative permission and returns only effective permission names. Other admin datasets and actions are not connected yet; Admin Web must not simulate them.
