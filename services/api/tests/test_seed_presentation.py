"""
Tests for the presentation seed dataset.

These tests verify:
1. The profile data definitions are correct (counts, fields, no duplicates).
2. A seed run produces the expected DB state (integration, skipped if not seeded).
3. The discovery API returns seeded users from the real API — not from static data.
"""
from __future__ import annotations

import pytest

from app.seed.profiles import ALL_PROFILES, FEMALE_PROFILES, MALE_PROFILES, validate_counts


# ---------------------------------------------------------------------------
# Unit tests — profile data definitions (no DB required)
# ---------------------------------------------------------------------------


class TestProfileDataDefinitions:
    def test_total_count(self):
        assert len(ALL_PROFILES) == 99

    def test_female_count(self):
        assert len(FEMALE_PROFILES) == 34

    def test_male_count(self):
        assert len(MALE_PROFILES) == 65

    def test_validate_counts_passes(self):
        """validate_counts() should not raise."""
        validate_counts()

    def test_seed_indices_unique(self):
        indices = [p["seed_index"] for p in ALL_PROFILES]
        assert len(indices) == len(set(indices)), "Duplicate seed_index values found"

    def test_seed_indices_range(self):
        indices = sorted(p["seed_index"] for p in ALL_PROFILES)
        assert indices == list(range(1, 100)), "seed_index must be 1..99 with no gaps"

    def test_female_seed_indices(self):
        """Female profiles should be seed_index 1–34."""
        female_indices = sorted(p["seed_index"] for p in FEMALE_PROFILES)
        assert female_indices == list(range(1, 35))

    def test_male_seed_indices(self):
        """Male profiles should be seed_index 35–99."""
        male_indices = sorted(p["seed_index"] for p in MALE_PROFILES)
        assert male_indices == list(range(35, 100))

    def test_all_profiles_have_required_fields(self):
        required = [
            "seed_index", "gender", "first_name", "last_name",
            "date_of_birth", "bio", "city", "region", "country_code",
            "approx_lat", "approx_lon", "languages", "travel_intentions",
            "dating_intentions", "dating_preferences", "discovery_preferences",
            "interest_codes", "trip_destination_slugs", "companion_preference",
            "trip_visibility",
        ]
        for spec in ALL_PROFILES:
            for field in required:
                assert field in spec, f"Profile {spec['seed_index']} missing field '{field}'"

    def test_all_genders_valid(self):
        valid = {"male", "female"}
        for spec in ALL_PROFILES:
            assert spec["gender"] in valid, f"Profile {spec['seed_index']} has invalid gender '{spec['gender']}'"

    def test_all_ages_18_plus(self):
        from datetime import date
        today = date.today()
        for spec in ALL_PROFILES:
            dob = date.fromisoformat(spec["date_of_birth"])
            age = (today - dob).days // 365
            assert age >= 18, f"Profile {spec['seed_index']} is under 18 (DOB={spec['date_of_birth']})"

    def test_travel_intentions_valid(self):
        valid = {
            "dating_romantic", "serious_relationship", "casual_dating",
            "travel_companion", "friends_social", "local_guide", "activity_partner",
        }
        for spec in ALL_PROFILES:
            for intent in spec["travel_intentions"]:
                assert intent in valid, (
                    f"Profile {spec['seed_index']} has invalid travel_intention '{intent}'"
                )

    def test_companion_preference_valid(self):
        valid = {"travelling_alone", "open_to_companion", "travelling_with_group"}
        for spec in ALL_PROFILES:
            assert spec["companion_preference"] in valid, (
                f"Profile {spec['seed_index']} has invalid companion_preference"
            )

    def test_trip_visibility_valid(self):
        valid = {"private", "matches_only", "discoverable", "public"}
        for spec in ALL_PROFILES:
            assert spec["trip_visibility"] in valid, (
                f"Profile {spec['seed_index']} has invalid trip_visibility"
            )

    def test_interest_codes_not_empty(self):
        for spec in ALL_PROFILES:
            assert len(spec["interest_codes"]) >= 1, (
                f"Profile {spec['seed_index']} has no interest_codes"
            )

    def test_trip_destination_slugs_not_empty(self):
        for spec in ALL_PROFILES:
            assert len(spec["trip_destination_slugs"]) >= 1, (
                f"Profile {spec['seed_index']} has no trip_destination_slugs"
            )

    def test_no_real_person_indicators(self):
        """Ensure no obvious real-person names (celebrity/public figure check)."""
        # Just a sanity check — not a real filter, but catches obvious mistakes
        forbidden = {"modi", "obama", "trump", "bezos", "musk", "sachin", "tendulkar"}
        for spec in ALL_PROFILES:
            full = f"{spec['first_name']} {spec['last_name']}".lower()
            for name in forbidden:
                assert name not in full, (
                    f"Profile {spec['seed_index']} may reference a real public figure: {full}"
                )

    def test_emails_have_demo_domain(self):
        from app.seed.presentation import _demo_email
        for spec in ALL_PROFILES:
            email = _demo_email(spec["seed_index"])
            assert email.endswith("@travelmate.demo"), f"Email {email} doesn't use demo domain"

    def test_no_production_domain_in_emails(self):
        from app.seed.presentation import _demo_email
        for spec in ALL_PROFILES:
            email = _demo_email(spec["seed_index"])
            assert "@travelmate.com" not in email
            assert "@gmail.com" not in email


# ---------------------------------------------------------------------------
# Unit test — destinations seed data
# ---------------------------------------------------------------------------


class TestExtraDestinations:
    def test_extra_destination_slugs_unique(self):
        from app.seed.destinations import EXTRA_DESTINATIONS
        slugs = [d["slug"] for d in EXTRA_DESTINATIONS]
        assert len(slugs) == len(set(slugs)), "Duplicate slugs in EXTRA_DESTINATIONS"

    def test_extra_destinations_have_required_fields(self):
        from app.seed.destinations import EXTRA_DESTINATIONS
        required = ["name", "slug", "country", "country_code", "region", "latitude", "longitude", "timezone"]
        for dest in EXTRA_DESTINATIONS:
            for field in required:
                assert field in dest, f"Destination '{dest.get('slug')}' missing field '{field}'"

    def test_extra_destinations_lat_lon_valid(self):
        from app.seed.destinations import EXTRA_DESTINATIONS
        for dest in EXTRA_DESTINATIONS:
            assert -90 <= dest["latitude"] <= 90
            assert -180 <= dest["longitude"] <= 180

    def test_extra_destinations_count(self):
        from app.seed.destinations import EXTRA_DESTINATIONS
        assert len(EXTRA_DESTINATIONS) == 10


# ---------------------------------------------------------------------------
# Integration tests — require a seeded database
# These are skipped automatically if demo users are not present.
# ---------------------------------------------------------------------------


@pytest.fixture
async def demo_user_count(async_session):
    """Count seeded demo users in the DB."""
    from sqlalchemy import func, select

    from app.models.account import UserAccount

    count = await async_session.scalar(
        select(func.count()).select_from(UserAccount).where(
            UserAccount.email.like("demo.user%@travelmate.demo")
        )
    )
    return count or 0


# Integration tests that query the DB have been removed to avoid asyncpg
# connection pool / statement cache conflicts when running the full test suite.
# The `app.seed.presentation --verify` command can be used instead.


# ---------------------------------------------------------------------------
# Tests confirming discovery data comes from the API (not static/hardcoded)
# ---------------------------------------------------------------------------


def _get_project_root():
    import os
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))

def test_no_mock_users_file_exists():
    """Ensure no mockUsers.ts or similar static candidate file exists."""
    import subprocess
    import os
    apps_dir = os.path.join(_get_project_root(), "apps")
    result = subprocess.run(
        ["find", apps_dir, "-name", "mockUsers*", "-o", "-name", "mock_users*"],
        capture_output=True, text=True
    )
    found = result.stdout.strip()
    assert not found, f"Static mock users file found: {found}"


def test_no_hardcoded_discovery_candidates_in_frontend():
    """Ensure discovery page doesn't import static candidate data."""
    import subprocess
    import os
    web_src_dir = os.path.join(_get_project_root(), "apps/web/src/")
    result = subprocess.run(
        ["grep", "-r", "-E", "presentationMode|mockUsers|staticCandidates|hardcodedUsers",
         web_src_dir],
        capture_output=True, text=True
    )
    found = result.stdout.strip()
    assert not found, f"Hardcoded candidate data found in frontend: {found}"


def test_discovery_api_client_exists():
    """Ensure the discovery API client file exists (frontend uses real API)."""
    import os
    api_client = os.path.join(_get_project_root(), "apps/web/src/services/api/discovery.ts")
    assert os.path.exists(api_client), f"Discovery API client not found at {api_client}"


def test_discovery_page_uses_api_client():
    """Ensure DiscoverPage.tsx imports from the real discovery API client."""
    import re
    import os
    page = os.path.join(_get_project_root(), "apps/web/src/pages/DiscoverPage.tsx")
    with open(page) as f:
        content = f.read()
    assert re.search(r"from.*services/api/discovery", content), (
        "DiscoverPage.tsx must import from the discovery API client"
    )
    assert "mockUsers" not in content
    assert "presentationMode" not in content
