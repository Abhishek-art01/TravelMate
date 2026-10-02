# Presentation Dataset — Development Guide

This document explains how to populate TravelMate with 99 realistic synthetic user profiles for development, staging, and product demonstrations.

> [!IMPORTANT]
> This dataset is **synthetic and for non-production environments only**.
> The seed command refuses to run when `APP_ENVIRONMENT=production` unless you explicitly pass `--force`.

---

## Overview

The presentation dataset creates:

| Group  | Count |
|--------|-------|
| Female | 34    |
| Male   | 65    |
| **Total** | **99** |

Each user is a realistic, fully fictional synthetic identity — not a real person, not a celebrity.

Each user has:
- A **Supabase Auth** account (real, email-confirmed)
- A **local User + UserAccount** row linked via `auth_provider_user_id`
- A **UserProfile** (`profile_visibility=public`, `discovery_visibility=true`)
- **Preferences** (travel intention, dating intention, dating preference, discovery preference, languages)
- **Interests** (from the existing catalog: food_walks, hiking, photography, etc.)
- **A UserLocation** (approximate city-level coordinates)
- **1–2 Trips** (with `TripIntent`s, mostly `discoverable` visibility)
- **A synthetic avatar** — a coloured initial-circle JPEG uploaded to R2 and stored as an approved `MediaAsset`

---

## Quick Start

### 1. Run the seed

```bash
cd services/api
SEED_DEMO_PASSWORD=YourDemoPassword123 python -m app.seed.presentation --seed
```

If `SEED_DEMO_PASSWORD` is not set, a secure random password is generated and printed **once** to stdout. Store it securely — it is not saved anywhere.

### 2. Verify

```bash
python -m app.seed.presentation --verify
```

Expected output:
```
Expected: 99 users (34 female, 65 male)
Found:    99 users (34 female, 65 male)
✓ Verification PASSED
```

### 3. Clean up

```bash
python -m app.seed.presentation --cleanup
```

This removes all demo users from the DB **and** from Supabase Auth.

---

## Environment Safety

The seed checks `app_environment` (configured via `APP_ENVIRONMENT` env var, defaults to `development`).

| Environment | Behaviour |
|-------------|-----------|
| `development` / `staging` | Runs normally |
| `production` | **Refuses** unless `--force` is passed |

```bash
# Production override (use with extreme caution)
python -m app.seed.presentation --seed --force
```

---

## Demo Credentials

| Field | Value |
|-------|-------|
| Email pattern | `demo.user001@travelmate.demo` … `demo.user099@travelmate.demo` |
| Password | Value of `SEED_DEMO_PASSWORD` env var at seed time |

> [!CAUTION]
> Never commit `SEED_DEMO_PASSWORD` to git. Never put credentials in source code.

---

## Idempotency

Running `--seed` twice is safe. Each user is looked up by email before creation:
- If the DB account already exists → **skipped**
- If the Supabase auth user already exists (but DB account is missing) → reuses the existing Supabase UID

---

## Architecture

The seed lives in `services/api/app/seed/`:

```
app/seed/
├── __init__.py
├── presentation.py      ← CLI entry point (--seed / --verify / --cleanup)
├── supabase_admin.py    ← httpx wrapper for Supabase Auth Admin API
├── destinations.py      ← upserts 10 additional destinations
├── profiles.py          ← 99 synthetic PersonSpec definitions
└── media.py             ← PIL avatar generator + direct R2 upload
```

### Media strategy

The normal upload flow (presigned URL → client upload → complete) is bypassed for seeding. Instead:

1. A JPEG avatar is generated in-memory using Pillow (no real photos, no copyright risk)
2. The image is uploaded directly to R2 using `boto3`
3. A `MediaAsset` record is created with `processing_status="ready"` and `moderation_status="approved"`

This is correct for seed data — it mirrors what the moderation approval step would do for a real user.

> [!NOTE]
> Profile photo display and identity verification are **separate systems**. Demo users are NOT marked as government-ID verified. The `is_verified` flag is `false` on all demo users.

---

## Destinations

The seed upserts 10 additional destinations on top of the 12 seeded in Phase 6:

| Destination | Country |
|-------------|---------|
| Dubai | UAE |
| Singapore | Singapore |
| Bali | Indonesia |
| London | UK |
| Udaipur | India |
| Rishikesh | India |
| Hyderabad | India |
| Chennai | India |
| Kolkata | India |
| Kashmir | India |

---

## Discovery Flow

> [!IMPORTANT]
> Demo users appear in the discovery API via the **existing matching engine** — not through any special frontend condition, static data file, or mock API.

The frontend `DiscoverPage.tsx` calls `GET /api/v1/discovery` exactly as it would for real users. No `if (presentationMode)` blocks exist anywhere.

---

## Tests

```bash
# Run seed-specific tests (no DB required for unit tests)
cd services/api
pytest tests/test_seed_presentation.py -v
```

Integration tests are skipped automatically if the seed hasn't been run.

---

## Removing Specific Users

To remove all demo data:

```bash
python -m app.seed.presentation --cleanup
```

To remove a single user manually, use the Admin panel or delete by email via Supabase dashboard + the DB.

---

## Git Safety

The following must never be committed:
- `SEED_DEMO_PASSWORD` values
- Generated seed-report files with passwords
- Supabase service-role keys

The `.gitignore` already excludes `.env` files.
