# Docker Runtime Configuration

This directory is reserved for production-ready container configuration and deployment assets.

## Current development environment

The root `docker-compose.dev.yml` file provisions the following local services:

- PostgreSQL + PostGIS
- MongoDB
- Redis
- FastAPI backend
- React web app
- Admin web app

These services provide a realistic local development environment without locking the architecture to a single cloud platform.
