"""
TravelMate Presentation Dataset Seed — main CLI entry point.

Usage:
    python -m app.seed.presentation [--seed] [--verify] [--cleanup] [--force]

Flags:
    --seed     Create the 99 demo users (default action when no flag given)
    --verify   Verify that the expected demo users and counts are present
    --cleanup  Remove all demo users created by this seed
    --force    Override production-environment safety check (DANGEROUS)

Environment safety:
    Refuses to run in ENVIRONMENT=production unless --force is passed.

Demo email pattern:
    demo.user{NNN}@travelmate.demo   (001–099)

Demo password:
    Configured via SEED_DEMO_PASSWORD env var.
    If not set, a random secure password is generated and printed once
    at the end of the seed run (it is NOT stored anywhere).

Idempotency:
    Running --seed twice is safe.  Existing demo users are detected by email
    and skipped.  Destination upsert is always safe.

Cleanup:
    --cleanup deletes auth users and all DB records for demo emails.
"""
from __future__ import annotations

import asyncio
import os
import secrets
import sys
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import delete, select, text

from app.config import get_settings
from app.db.session import AsyncSessionLocal
from app.models.account import UserAccount
from app.models.interest import Interest, UserInterest
from app.models.location import UserLocation
from app.models.media import MediaAsset
from app.models.preferences import UserPreferenceOption, UserPreferences
from app.models.profile import UserProfile
from app.models.trip import Trip, TripIntent
from app.models.user import User
from app.seed.destinations import upsert_destinations
from app.seed.media import create_avatar_media_asset
from app.seed.profiles import ALL_PROFILES, PersonSpec, validate_counts
from app.seed.supabase_admin import SupabaseAdminClient

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEMO_EMAIL_DOMAIN = "travelmate.demo"
SEED_MARKER_PREFIX = "demo.user"  # all seeded accounts start with this


def _demo_email(seed_index: int) -> str:
    return f"demo.user{seed_index:03d}@{DEMO_EMAIL_DOMAIN}"


def _demo_username(spec: PersonSpec) -> str:
    return f"{spec['first_name'].lower()}{spec['last_name'].lower()}{spec['seed_index']}"


# ---------------------------------------------------------------------------
# Safety check
# ---------------------------------------------------------------------------
def _check_environment(force: bool) -> None:
    settings = get_settings()
    env = settings.app_environment.lower()
    if env == "production" and not force:
        print(
            "ERROR: Refusing to seed presentation data in production environment.\n"
            "       Set ENVIRONMENT=development or pass --force to override.",
            file=sys.stderr,
        )
        sys.exit(1)
    if env == "production" and force:
        print(
            "WARNING: --force passed in production environment. Proceeding anyway.",
            file=sys.stderr,
        )


# ---------------------------------------------------------------------------
# Trip date helpers
# ---------------------------------------------------------------------------
def _trip_dates(seed_index: int) -> tuple[date, date]:
    """Return deterministic future trip dates based on seed_index."""
    today = datetime.now(UTC).date()
    offset_days = 30 + (seed_index * 11 % 180)  # 30–210 days out
    duration_days = 5 + (seed_index * 7 % 20)   # 5–24 day trip
    start = today + timedelta(days=offset_days)
    end = start + timedelta(days=duration_days)
    return start, end


# ---------------------------------------------------------------------------
# Profile completion score helper (mirrors profile_completion.py)
# ---------------------------------------------------------------------------
def _compute_completion(spec: PersonSpec, has_media: bool) -> int:
    score = 0
    if spec.get("first_name"):
        score += 15
    if spec.get("bio"):
        score += 15
    if spec.get("date_of_birth"):
        score += 10
    if spec.get("gender"):
        score += 10
    if spec.get("travel_intentions"):
        score += 15
    if spec.get("languages"):
        score += 10
    if spec.get("interest_codes"):
        score += 10
    if has_media:
        score += 10
    if spec.get("dating_intentions"):
        score += 5
    return min(score, 100)


# ---------------------------------------------------------------------------
# Core seeding logic for a single user
# ---------------------------------------------------------------------------
async def _seed_one_user(
    session,
    supabase: SupabaseAdminClient,
    spec: PersonSpec,
    password: str,
    dest_slug_to_id: dict[str, str],
    interest_code_to_id: dict[str, str],
) -> bool:
    """
    Create one demo user.  Returns True if created, False if already existed.
    """
    email = _demo_email(spec["seed_index"])
    now_str = datetime.now(UTC).isoformat()

    # --- Check if DB user already exists ---
    existing_account = await session.scalar(
        select(UserAccount).where(UserAccount.email == email)
    )
    if existing_account:
        print(f"  SKIP  [{spec['seed_index']:03d}] {email} — already seeded")
        return False

    # --- Create Supabase auth user ---
    supabase_user = supabase.find_user_by_email(email)
    if supabase_user is None:
        display_name = f"{spec['first_name']} {spec['last_name']}"
        supabase_user = supabase.create_user(email, password, display_name)
    supabase_uid: str = supabase_user["id"]

    user_id = str(__import__("uuid").uuid4())

    # --- User row ---
    user = User(
        id=user_id,
        auth_provider_user_id=supabase_uid,
        account_status="active",
        created_at=now_str,
        updated_at=now_str,
        is_verified=False,
    )
    session.add(user)
    await session.flush()  # ensure User PK exists before FK children

    # --- UserAccount row ---
    account = UserAccount(
        id=str(__import__("uuid").uuid4()),
        user_id=user_id,
        provider="supabase",
        provider_subject=supabase_uid,
        email=email,
        email_verified=True,
        created_at=now_str,
        updated_at=now_str,
    )
    session.add(account)

    # --- UserProfile ---
    dob = spec["date_of_birth"]
    profile = UserProfile(
        id=str(__import__("uuid").uuid4()),
        user_id=user_id,
        display_name=f"{spec['first_name']} {spec['last_name']}",
        bio=spec["bio"],
        date_of_birth=dob,
        gender_identity=spec["gender"],
        profile_visibility="public",
        discovery_visibility=True,
        profile_status="complete",
        profile_completion=0,  # will update after media
        created_at=now_str,
        updated_at=now_str,
    )
    session.add(profile)

    # --- UserPreferences ---
    prefs = UserPreferences(
        id=str(__import__("uuid").uuid4()),
        user_id=user_id,
        minimum_age=18,
        maximum_age=None,
    )
    session.add(prefs)

    # --- UserPreferenceOptions ---
    pref_rows: list[UserPreferenceOption] = []
    category_values = [
        ("travel_intention", spec["travel_intentions"]),
        ("dating_intention", spec["dating_intentions"]),
        ("dating_preference", spec["dating_preferences"]),
        ("discovery_preference", spec["discovery_preferences"]),
        ("language", spec["languages"]),
    ]
    for cat, values in category_values:
        for val in values:
            pref_rows.append(
                UserPreferenceOption(
                    id=str(__import__("uuid").uuid4()),
                    user_id=user_id,
                    category=cat,
                    value=val,
                )
            )
    session.add_all(pref_rows)

    # --- UserInterests ---
    interest_rows: list[UserInterest] = []
    for code in spec["interest_codes"]:
        iid = interest_code_to_id.get(code)
        if iid:
            interest_rows.append(UserInterest(user_id=user_id, interest_id=iid))
    session.add_all(interest_rows)

    # --- UserLocation ---
    location = UserLocation(
        id=str(__import__("uuid").uuid4()),
        user_id=user_id,
        latitude=None,
        longitude=None,
        approx_latitude=spec["approx_lat"],
        approx_longitude=spec["approx_lon"],
        precision="city",
        sharing_mode="approximate",
        source="manual",
        city=spec["city"],
        region=spec["region"],
        country_code=spec["country_code"],
    )
    session.add(location)

    # --- Trips ---
    start_date, end_date = _trip_dates(spec["seed_index"])
    companion_pref = spec.get("companion_preference", "open_to_companion")
    visibility = spec.get("trip_visibility", "discoverable")

    for i, slug in enumerate(spec["trip_destination_slugs"]):
        dest_id = dest_slug_to_id.get(slug)
        if not dest_id:
            print(f"  WARN  destination slug '{slug}' not found — skipping trip")
            continue
        # Stagger trip dates slightly for multiple trips
        t_start = start_date + timedelta(days=i * 45)
        t_end = end_date + timedelta(days=i * 45)
        # Make second trip of each user private (realistic mix)
        trip_vis = "private" if i > 0 and i % 3 == 0 else visibility

        trip_id = str(__import__("uuid").uuid4())
        trip = Trip(
            id=trip_id,
            user_id=user_id,
            destination_id=dest_id,
            title=f"{spec['first_name']}'s trip to {slug.replace('-', ' ').title()}",
            description=f"Demo trip created by presentation seed.",
            start_date=t_start,
            end_date=t_end,
            status="planned",
            visibility=trip_vis,
            companion_preference=companion_pref,
            party_size=1,
        )
        session.add(trip)

        # TripIntents
        for intent_val in spec["travel_intentions"]:
            session.add(
                TripIntent(
                    id=str(__import__("uuid").uuid4()),
                    trip_id=trip_id,
                    intent=intent_val,
                )
            )

    # --- Commit everything except media ---
    await session.commit()

    # --- Media (avatar image) ---
    try:
        asset = await create_avatar_media_asset(
            session,
            user_id=user_id,
            seed_index=spec["seed_index"],
            first_name=spec["first_name"],
            last_name=spec["last_name"],
            gender=spec["gender"],
        )
        await session.commit()
        has_media = True
    except Exception as exc:
        print(f"  WARN  media upload failed for {email}: {exc}")
        has_media = False

    # --- Update profile_completion ---
    completion = _compute_completion(spec, has_media)
    await session.execute(
        text("UPDATE profiles SET profile_completion = :score WHERE user_id = :uid"),
        {"score": completion, "uid": user_id},
    )
    await session.commit()

    print(f"  OK    [{spec['seed_index']:03d}] {email}  ({spec['gender']}, completion={completion}%)")
    return True


# ---------------------------------------------------------------------------
# --seed
# ---------------------------------------------------------------------------
async def _run_seed(password: str, force: bool) -> None:
    _check_environment(force)
    validate_counts()

    print("=== TravelMate Presentation Seed ===")
    print(f"Target: {len(ALL_PROFILES)} users (34 female, 65 male)")
    print()

    supabase = SupabaseAdminClient()

    async with AsyncSessionLocal() as session:
        # 1. Upsert destinations
        print("→ Upserting destinations...")
        dest_slug_to_id = await upsert_destinations(session)
        print(f"  Destinations available: {len(dest_slug_to_id)}")

        # 2. Load interest catalog
        interest_rows = (await session.execute(select(Interest).where(Interest.active == True))).scalars().all()  # noqa: E712
        interest_code_to_id = {i.code: i.id for i in interest_rows}
        print(f"  Interests available: {len(interest_code_to_id)}")
        print()

        # 3. Seed each user
        created = 0
        skipped = 0
        for spec in ALL_PROFILES:
            ok = await _seed_one_user(
                session, supabase, spec, password,
                dest_slug_to_id, interest_code_to_id,
            )
            if ok:
                created += 1
            else:
                skipped += 1

    print()
    print("=== Seed Complete ===")
    print(f"  Created: {created}")
    print(f"  Skipped: {skipped} (already existed)")
    print()
    if created > 0:
        print("IMPORTANT: Demo user password is the value of SEED_DEMO_PASSWORD.")
        print("           Keep it out of git. Do not share publicly.")


# ---------------------------------------------------------------------------
# --verify
# ---------------------------------------------------------------------------
async def _run_verify() -> None:
    print("=== Verifying Presentation Dataset ===")
    async with AsyncSessionLocal() as session:
        # Count demo accounts
        rows = (await session.execute(
            select(UserAccount).where(
                UserAccount.email.like(f"demo.user%@{DEMO_EMAIL_DOMAIN}")
            )
        )).scalars().all()

        found_emails = {r.email for r in rows}
        expected_emails = {_demo_email(i) for i in range(1, 100)}
        missing = expected_emails - found_emails
        extra = found_emails - expected_emails

        # Count by gender
        female_count = 0
        male_count = 0
        for spec in ALL_PROFILES:
            if _demo_email(spec["seed_index"]) in found_emails:
                if spec["gender"] == "female":
                    female_count += 1
                else:
                    male_count += 1

        print(f"  Expected: 99 users (34 female, 65 male)")
        print(f"  Found:    {len(found_emails)} users ({female_count} female, {male_count} male)")

        if missing:
            print(f"\n  MISSING ({len(missing)}):")
            for e in sorted(missing):
                print(f"    - {e}")
        if extra:
            print(f"\n  EXTRA ({len(extra)}):")
            for e in sorted(extra):
                print(f"    + {e}")

        if not missing and not extra and female_count == 34 and male_count == 65:
            print("\n  ✓ Verification PASSED")
        else:
            print("\n  ✗ Verification FAILED")
            sys.exit(1)


# ---------------------------------------------------------------------------
# --cleanup
# ---------------------------------------------------------------------------
async def _run_cleanup(force: bool) -> None:
    _check_environment(force)
    print("=== Cleaning Up Presentation Dataset ===")
    supabase = SupabaseAdminClient()

    async with AsyncSessionLocal() as session:
        # Find all demo accounts
        accounts = (await session.execute(
            select(UserAccount).where(
                UserAccount.email.like(f"demo.user%@{DEMO_EMAIL_DOMAIN}")
            )
        )).scalars().all()

        if not accounts:
            print("  Nothing to clean up.")
            return

        user_ids = [a.user_id for a in accounts]
        supabase_uids = []

        # Gather supabase UIDs
        users = (await session.execute(
            select(User).where(User.id.in_(user_ids))
        )).scalars().all()
        for u in users:
            if u.auth_provider_user_id:
                supabase_uids.append(u.auth_provider_user_id)

        print(f"  Removing {len(user_ids)} demo users from DB...")

        # Delete in dependency order
        for uid in user_ids:
            await session.execute(delete(TripIntent).where(
                TripIntent.trip_id.in_(
                    select(Trip.id).where(Trip.user_id == uid)
                )
            ))
        await session.execute(delete(Trip).where(Trip.user_id.in_(user_ids)))
        await session.execute(delete(MediaAsset).where(MediaAsset.user_id.in_(user_ids)))
        await session.execute(delete(UserInterest).where(UserInterest.user_id.in_(user_ids)))
        await session.execute(delete(UserPreferenceOption).where(UserPreferenceOption.user_id.in_(user_ids)))
        await session.execute(delete(UserPreferences).where(UserPreferences.user_id.in_(user_ids)))
        await session.execute(delete(UserLocation).where(UserLocation.user_id.in_(user_ids)))
        await session.execute(delete(UserProfile).where(UserProfile.user_id.in_(user_ids)))
        await session.execute(delete(UserAccount).where(UserAccount.user_id.in_(user_ids)))
        await session.execute(delete(User).where(User.id.in_(user_ids)))
        await session.commit()

        print(f"  Removing {len(supabase_uids)} Supabase auth users...")
        for uid in supabase_uids:
            try:
                supabase.delete_user(uid)
            except Exception as exc:
                print(f"  WARN  could not delete Supabase user {uid}: {exc}")

    print("  Cleanup complete.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="TravelMate presentation dataset seed")
    parser.add_argument("--seed", action="store_true", help="Seed the 99 demo users")
    parser.add_argument("--verify", action="store_true", help="Verify seeded data")
    parser.add_argument("--cleanup", action="store_true", help="Remove all demo users")
    parser.add_argument("--force", action="store_true", help="Override production safety check")
    args = parser.parse_args()

    # Default action is --seed if nothing specified
    if not any([args.seed, args.verify, args.cleanup]):
        args.seed = True

    if args.verify:
        asyncio.run(_run_verify())
    elif args.cleanup:
        asyncio.run(_run_cleanup(force=args.force))
    elif args.seed:
        # Resolve demo password
        password = os.environ.get("SEED_DEMO_PASSWORD", "")
        if not password:
            password = secrets.token_urlsafe(16)
            print(f"[seed] No SEED_DEMO_PASSWORD set — generated: {password}")
            print("[seed] Store this securely. It will not be shown again.")
            print()
        asyncio.run(_run_seed(password=password, force=args.force))


if __name__ == "__main__":
    main()
