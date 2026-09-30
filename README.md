# TravelMate

TravelMate is a secure travel-dating-social platform designed for Indian-market launch with privacy-first defaults, strong verification, and scalable architecture.

## Repository structure

- `apps/web` – public-facing React + Vite web app
- `apps/admin-web` – separate admin React + Vite app
- `apps/android` – native Kotlin + Jetpack Compose foundation
- `apps/ios` – native SwiftUI foundation
- `services/api` – FastAPI backend and API contracts
- `packages/*` – shared types and contract libraries
- `infrastructure` – Docker, deployment, monitoring, environment configs
- `docs` – architecture, security, privacy, compliance, deployment, and DR guidance

## Core architecture principles

- Security-first design with least-privilege access
- Indian compliance readiness with explicit legal review required before production
- Supabase Auth abstraction for identity management
- PostgreSQL + PostGIS as primary relational source of truth
- MongoDB for high-volume flexible document data
- Redis for ephemeral state, queues, and realtime coordination
- Modular microservice-ready backend with a single API foundation
- Platform portability via abstractions for maps, payments, storage, and auth

## Quick start

1. Copy `.env.example` to `.env` and fill in your real local credentials.
2. Install workspace dependencies:
   ```bash
   npm install
   ```
3. Start infrastructure and services:
   ```bash
   docker compose -f docker-compose.dev.yml up -d
   ```
4. Start backend:
   ```bash
   uvicorn services.api.app.main:app --reload --host 0.0.0.0 --port 8000
   ```
5. Start web apps:
   ```bash
   npm run dev --workspace apps/web
   npm run dev --workspace apps/admin-web
   ```
6. Open Android Studio for the Kotlin app under `apps/android` and Xcode for the Swift app under `apps/ios`.

## Documentation

See the `docs/` tree for architecture, security, privacy, and compliance references.

## Production note

This project is intentionally a strong engineering foundation, not a finished consumer app. Legal counsel should validate compliance choices before production launch.
