# Architecture Overview

TravelMate adopts a modular monorepo design to support a secure consumer platform, admin operations, mobile apps, and shared infrastructure.

## Principles

- Clear ownership of data domains across PostgreSQL, MongoDB, and Redis
- Privacy-first defaults with user consent and transparent controls
- Replaceable integration abstractions for auth, maps, storage, and payments
- Strong verification and moderation before exposure of sensitive product features

## System layers

1. Client applications: web, admin web, Android, iOS
2. API layer: FastAPI services with REST + WebSocket support
3. Shared platform services: matching, verification, media, notifications, moderation
4. Data layer: PostgreSQL + PostGIS, MongoDB, Redis
5. External providers: Supabase, Cloudflare R2, payment processors, AI providers

## Current foundation

This repository is intentionally the engineering baseline. It includes a working FastAPI health service, Vite web apps, Dockerized infrastructure, environment templates, and CI scaffolding, all organized for extension into the full production platform.
