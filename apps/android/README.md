# TravelMate Android

This folder contains the native Android foundation for the TravelMate app using Kotlin and Jetpack Compose.

## Structure

- `app/` – application module with Compose UI scaffolding
- `settings.gradle.kts` – project config
- `build.gradle.kts` – plugin versions and project-level config

## Notes

- The app is intentionally scaffolded as a secure foundation for authentication, profile, trip, discovery, and chat flows.
- Android Studio can open this folder directly.
- Production deployment should add signing config, Firebase integration, and secure auth/network handling.
