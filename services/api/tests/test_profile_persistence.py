from __future__ import annotations

from fastapi.testclient import TestClient


def test_me_identity_is_created_idempotently(profile_api: tuple[TestClient, dict[str, str]]) -> None:
    client, _ = profile_api
    first = client.get("/api/v1/me")
    second = client.get("/api/v1/me")

    assert first.status_code == second.status_code == 200
    assert first.json()["user_id"] == second.json()["user_id"]
    assert first.json()["provider"] == "email"
    assert first.json()["account_status"] == "active"


def test_profile_create_and_read_persist_without_exposing_dob(profile_api: tuple[TestClient, dict[str, str]]) -> None:
    client, _ = profile_api
    response = client.post("/api/v1/profiles", json={
        "display_name": "Mira",
        "date_of_birth": "1995-04-17",
        "bio": "Walks, food, and old cities.",
        "gender_identity": "woman",
    })

    assert response.status_code == 200
    assert response.json()["display_name"] == "Mira"
    assert response.json()["completion_percentage"] > 0
    assert "date_of_birth" not in response.json()

    loaded = client.get("/api/v1/me/profile")
    assert loaded.status_code == 200
    assert loaded.json()["bio"] == "Walks, food, and old cities."
    assert loaded.json()["gender_identity"] == "woman"
    assert "date_of_birth" not in loaded.json()


def test_profile_put_updates_only_authenticated_users_own_profile(profile_api: tuple[TestClient, dict[str, str]]) -> None:
    client, identity = profile_api
    created = client.put("/api/v1/me/profile", json={
        "display_name": "Mira",
        "date_of_birth": "1995-04-17",
    })
    assert created.status_code == 200

    identity["user_id"] = "supabase-user-b"
    updated = client.put("/api/v1/me/profile", json={
        "display_name": "Another person",
        "date_of_birth": "1994-03-16",
        "user_id": "supabase-user-a",
    })
    assert updated.status_code == 200
    assert updated.json()["user_id"] != created.json()["user_id"]
    assert updated.json()["display_name"] == "Another person"


def test_profile_requires_server_side_age_validation(profile_api: tuple[TestClient, dict[str, str]]) -> None:
    client, _ = profile_api
    response = client.put("/api/v1/me/profile", json={
        "display_name": "Young Traveller",
        "date_of_birth": "2015-01-01",
    })
    assert response.status_code == 422
    assert "at least 18" in response.text


def test_preferences_round_trip_and_interest_catalog_validation(profile_api: tuple[TestClient, dict[str, str]]) -> None:
    client, _ = profile_api
    payload = {
        "dating_intentions": ["serious_relationship"],
        "dating_preferences": ["women", "non_binary"],
        "discovery_preferences": ["shared_interests"],
        "travel_intentions": ["travel_companion", "local_guide"],
        "languages": ["hi", "en"],
        "interests": ["food_walks", "heritage"],
        "minimum_age": 25,
        "maximum_age": 42,
    }
    saved = client.put("/api/v1/me/preferences", json=payload)
    assert saved.status_code == 200
    loaded = client.get("/api/v1/me/preferences")
    assert loaded.status_code == 200
    normalized = {**payload, "dating_preferences": sorted(payload["dating_preferences"]), "travel_intentions": sorted(payload["travel_intentions"]), "languages": sorted(payload["languages"])}
    assert loaded.json() == normalized

    invalid = client.put("/api/v1/me/preferences", json={**payload, "interests": ["not-in-catalog"]})
    assert invalid.status_code == 422


def test_privacy_round_trip_and_hidden_profile_is_not_public(profile_api: tuple[TestClient, dict[str, str]]) -> None:
    client, _ = profile_api
    client.put("/api/v1/me/profile", json={"display_name": "Private Traveller", "date_of_birth": "1995-04-17"})
    privacy = {
        "profile_visibility": "hidden",
        "discovery_visibility": False,
        "location_precision": "hidden",
        "allow_exact_location_sharing": False,
        "personalization_enabled": False,
        "communications_enabled": True,
    }
    assert client.put("/api/v1/me/privacy", json=privacy).json() == privacy
    assert client.get("/api/v1/me/privacy").json() == privacy
    profile_id = client.get("/api/v1/me/profile").json()["profile_id"]
    assert client.get(f"/api/v1/profiles/{profile_id}/public").status_code == 404


def test_public_profile_never_contains_email_or_date_of_birth(profile_api: tuple[TestClient, dict[str, str]]) -> None:
    client, _ = profile_api
    client.put("/api/v1/me/profile", json={"display_name": "Public Traveller", "date_of_birth": "1995-04-17", "bio": "Open to exploring."})
    client.put("/api/v1/me/privacy", json={"profile_visibility": "public", "discovery_visibility": True})
    profile_id = client.get("/api/v1/me/profile").json()["profile_id"]
    public = client.get(f"/api/v1/profiles/{profile_id}/public")

    assert public.status_code == 200
    assert public.json()["display_name"] == "Public Traveller"
    assert "email" not in public.json()
    assert "date_of_birth" not in public.json()
