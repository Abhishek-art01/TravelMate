from __future__ import annotations

from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_current_user
from app.main import app
from app.services.matching_engine import (
    CandidateContext,
    ViewerContext,
    compute_match_score,
)


# 1. Matching Engine Unit Tests
def test_matching_engine_high_compatibility():
    viewer = ViewerContext(
        user_id="user-1",
        age=25,
        trip_destinations={"dest-paris"},
        trip_countries={"FR"},
        trip_dates=[(date(2026, 7, 1), date(2026, 7, 10))],
        trip_intents={"travel_companion"},
        travel_intentions={"travel_companion"},
        interests={"art_design", "photography", "food_walks"},
        languages={"en", "fr"},
    )
    candidate = CandidateContext(
        user_id="user-2",
        display_name="Amelie",
        age=24,
        profile_completion=100,
        trip_destinations={"dest-paris"},
        trip_destination_names={"dest-paris": "Paris, France"},
        trip_countries={"FR"},
        trip_dates=[(date(2026, 7, 3), date(2026, 7, 8))],  # 6 days overlap
        trip_intents={"travel_companion"},
        companion_preferences={"open_to_companion"},
        travel_intentions={"travel_companion"},
        interests={"art_design", "food_walks"},
        languages={"fr", "es"},
    )

    result = compute_match_score(viewer, candidate)
    # Destination (30) + Dates (20) + Intent (15) + Interests (6) + Language (5) + Companion (5) + Completeness (5) = 86
    assert result.score >= 80
    assert any("Paris" in r for r in result.reasons)
    assert any("overlap" in r.lower() for r in result.reasons)
    assert any("intent" in r.lower() for r in result.reasons)
    assert any("interests" in r.lower() for r in result.reasons)
    assert any("language" in r.lower() for r in result.reasons)


def test_matching_engine_country_fallback_and_no_dates():
    viewer = ViewerContext(
        user_id="user-1",
        age=30,
        trip_destinations={"dest-tokyo"},
        trip_countries={"JP"},
        trip_dates=[(date(2026, 9, 1), date(2026, 9, 10))],
    )
    candidate = CandidateContext(
        user_id="user-2",
        display_name="Kenji",
        age=32,
        trip_destinations={"dest-kyoto"},  # Different city, same country JP
        trip_destination_names={"dest-kyoto": "Kyoto, Japan"},
        trip_countries={"JP"},
        trip_dates=[(date(2026, 10, 1), date(2026, 10, 10))],  # No date overlap
    )

    result = compute_match_score(viewer, candidate)
    assert 15 <= result.score < 30
    assert any("country" in r.lower() for r in result.reasons)
    assert not any("dates overlap" in r.lower() for r in result.reasons)


# 2. Integration Tests via profile_api
def _setup_user(
    client: TestClient,
    identity: dict[str, Any],
    auth_id: str,
    display_name: str,
    dob: str,
    gender: str = "other",
) -> str:
    identity["user_id"] = auth_id
    identity["email"] = f"{auth_id}@travelmate.test"
    identity["role"] = "user"
    identity["permissions"] = ["profile.read", "profile.write"]
    resp = client.put(
        "/api/v1/me/profile",
        json={
            "display_name": display_name,
            "date_of_birth": dob,
            "bio": f"Bio of {display_name}",
            "gender_identity": gender,
            "profile_visibility": "public",
            "discovery_visibility": True,
        },
    )
    assert resp.status_code == 200
    return resp.json()["user_id"]


def test_discovery_filtering_and_hard_filters(profile_api):
    client, identity = profile_api

    # Viewer: Alice (age 26)
    alice_id = _setup_user(client, identity, "auth-alice", "Alice", "2000-01-01", "female")

    # Candidate 1: Bob (age 28, public, discoverable)
    bob_id = _setup_user(client, identity, "auth-bob", "Bob", "1998-05-10", "male")

    # Candidate 2: Charlie (age 24, discoverable=False)
    charlie_id = _setup_user(client, identity, "auth-charlie", "Charlie", "2002-03-15", "male")
    identity["user_id"] = "auth-charlie"
    client.put("/api/v1/me/profile", json={"discovery_visibility": False})

    # Discovery list for Alice
    identity["user_id"] = "auth-alice"
    resp = client.get("/api/v1/discovery")
    assert resp.status_code == 200
    data = resp.json()
    item_ids = [item["id"] for item in data["items"]]

    # Alice must not see herself
    assert alice_id not in item_ids
    # Bob is eligible and discoverable
    assert bob_id in item_ids
    # Charlie turned off discovery visibility, so must not appear
    assert charlie_id not in item_ids


def test_bidirectional_block_exclusion(profile_api):
    client, identity = profile_api

    # Setup User A and User B
    user_a_id = _setup_user(client, identity, "auth-user-a", "User A", "1995-01-01")
    user_b_id = _setup_user(client, identity, "auth-user-b", "User B", "1996-01-01")

    # Before block: User A sees User B
    identity["user_id"] = "auth-user-a"
    resp = client.get("/api/v1/discovery")
    assert resp.status_code == 200
    assert any(c["id"] == user_b_id for c in resp.json()["items"])

    # User A blocks User B
    block_resp = client.post(f"/api/v1/me/blocks/{user_b_id}", json={"reason": "Inappropriate"})
    assert block_resp.status_code == 201

    # Now User A must NOT see User B in discovery
    resp_a = client.get("/api/v1/discovery")
    assert not any(c["id"] == user_b_id for c in resp_a.json()["items"])

    # And User A cannot view User B detail -> 404
    detail_a = client.get(f"/api/v1/discovery/{user_b_id}")
    assert detail_a.status_code == 404

    # Crucial Bidirectional check: User B must ALSO NOT see User A in discovery!
    identity["user_id"] = "auth-user-b"
    resp_b = client.get("/api/v1/discovery")
    assert not any(c["id"] == user_a_id for c in resp_b.json()["items"])

    # And User B cannot view User A detail -> 404
    detail_b = client.get(f"/api/v1/discovery/{user_a_id}")
    assert detail_b.status_code == 404

    # Unblock
    identity["user_id"] = "auth-user-a"
    unblock_resp = client.delete(f"/api/v1/me/blocks/{user_b_id}")
    assert unblock_resp.status_code == 204

    # After unblock: visible again
    resp_after = client.get("/api/v1/discovery")
    assert any(c["id"] == user_b_id for c in resp_after.json()["items"])


def test_discovery_interactions_and_mutual_match(profile_api):
    client, identity = profile_api

    s1_id = _setup_user(client, identity, "auth-swiper-1", "Swiper One", "1997-02-02")
    s2_id = _setup_user(client, identity, "auth-swiper-2", "Swiper Two", "1998-03-03")

    # Swiper 1 likes Swiper 2
    identity["user_id"] = "auth-swiper-1"
    like_1 = client.post(f"/api/v1/discovery/{s2_id}/interaction", json={"interaction_type": "like"})
    assert like_1.status_code == 201
    assert like_1.json()["is_match"] is False

    # After Swiper 1 liked Swiper 2, Swiper 2 should not appear again in Swiper 1's discovery feed
    feed_1 = client.get("/api/v1/discovery")
    assert not any(c["id"] == s2_id for c in feed_1.json()["items"])

    # Swiper 2 likes Swiper 1 -> Mutual Match!
    identity["user_id"] = "auth-swiper-2"
    like_2 = client.post(f"/api/v1/discovery/{s1_id}/interaction", json={"interaction_type": "like"})
    assert like_2.status_code == 201
    assert like_2.json()["is_match"] is True


def test_cannot_interact_or_block_or_report_self(profile_api):
    client, identity = profile_api
    self_id = _setup_user(client, identity, "auth-self", "Self User", "1995-05-05")

    identity["user_id"] = "auth-self"

    # Cannot interact with self
    resp_interact = client.post(f"/api/v1/discovery/{self_id}/interaction", json={"interaction_type": "like"})
    assert resp_interact.status_code == 400

    # Cannot block self
    resp_block = client.post(f"/api/v1/me/blocks/{self_id}", json={"reason": "Self"})
    assert resp_block.status_code == 400

    # Cannot report self
    resp_report = client.post(
        "/api/v1/reports",
        json={"reported_id": self_id, "reason": "harassment", "details": "myself"},
    )
    assert resp_report.status_code == 400


def test_reports_and_admin_moderation_queue(profile_api):
    client, identity = profile_api

    reporter_id = _setup_user(client, identity, "auth-reporter", "Reporter User", "1994-04-04")
    bad_actor_id = _setup_user(client, identity, "auth-bad-actor", "Bad Actor", "1993-03-03")

    # Reporter submits report against bad actor
    identity["user_id"] = "auth-reporter"
    rep_resp = client.post(
        "/api/v1/reports",
        json={
            "reported_id": bad_actor_id,
            "reason": "inappropriate_content",
            "details": "Inappropriate bio and spam links",
        },
    )
    assert rep_resp.status_code == 201
    report_id = rep_resp.json()["id"]
    assert rep_resp.json()["status"] == "pending"

    # Non-admin cannot view admin reports
    unauth_list = client.get("/api/v1/admin/reports")
    assert unauth_list.status_code == 403

    # Admin with moderation.read views reports
    identity["user_id"] = "auth-mod-1"
    identity["role"] = "moderator"
    identity["permissions"] = ["moderation.read", "moderation.action"]
    admin_list = client.get("/api/v1/admin/reports")
    assert admin_list.status_code == 200
    reports = admin_list.json()["items"]
    assert any(r["id"] == report_id for r in reports)

    # Admin actions the report
    patch_resp = client.patch(
        f"/api/v1/admin/reports/{report_id}",
        json={"status": "actioned", "resolution_notes": "Profile flagged and warned."},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "actioned"
    assert patch_resp.json()["resolution_notes"] == "Profile flagged and warned."


def test_cursor_pagination(profile_api):
    client, identity = profile_api

    viewer_id = _setup_user(client, identity, "auth-viewer", "Viewer", "1995-01-01")
    for i in range(1, 6):
        _setup_user(client, identity, f"auth-candidate-{i}", f"Candidate {i}", f"199{i}-01-01")

    identity["user_id"] = "auth-viewer"

    # Fetch page 1 with limit=2
    page1 = client.get("/api/v1/discovery?limit=2")
    assert page1.status_code == 200
    p1_data = page1.json()
    assert len(p1_data["items"]) == 2
    assert p1_data["next_cursor"] is not None

    # Fetch page 2 with next_cursor
    cursor = p1_data["next_cursor"]
    page2 = client.get(f"/api/v1/discovery?limit=2&cursor={cursor}")
    assert page2.status_code == 200
    p2_data = page2.json()
    assert len(p2_data["items"]) == 2

    # Verify no item duplication across pages
    p1_ids = {c["id"] for c in p1_data["items"]}
    p2_ids = {c["id"] for c in p2_data["items"]}
    assert p1_ids.isdisjoint(p2_ids)

    # Invalid cursor returns 400
    bad_page = client.get("/api/v1/discovery?cursor=invalid_base64_garbage!!!")
    assert bad_page.status_code == 400
    assert bad_page.json()["error"]["code"] == "INVALID_CURSOR"
