from __future__ import annotations

from datetime import date
from typing import Any

from fastapi.testclient import TestClient

from app.core.security import get_current_user
from app.main import app
from app.services.location_privacy import approximate_coordinates, bounding_box, haversine_distance_km
from app.services.travel_dates import is_date_overlap


def _request_as(client: TestClient, role: str, permissions: list[str], user_id: str = "custom-user-1"):
    async def current_user() -> dict[str, Any]:
        return {
            "user_id": user_id,
            "email": f"{role}@travelmate.test",
            "role": role,
            "permissions": permissions,
            "claims": {},
        }

    app.dependency_overrides[get_current_user] = current_user


# 1. Date Overlap Utility Unit Tests
def test_date_overlap_utility():
    # Identical ranges
    assert is_date_overlap(date(2026, 12, 10), date(2026, 12, 15), date(2026, 12, 10), date(2026, 12, 15)) is True
    # Boundary overlap (day 15 matches day 15)
    assert is_date_overlap(date(2026, 12, 10), date(2026, 12, 15), date(2026, 12, 15), date(2026, 12, 20)) is True
    # Enclosed range
    assert is_date_overlap(date(2026, 12, 1), date(2026, 12, 31), date(2026, 12, 10), date(2026, 12, 15)) is True
    # Partial overlap
    assert is_date_overlap(date(2026, 12, 10), date(2026, 12, 20), date(2026, 12, 15), date(2026, 12, 25)) is True
    # Non-overlapping before
    assert is_date_overlap(date(2026, 12, 1), date(2026, 12, 5), date(2026, 12, 10), date(2026, 12, 15)) is False
    # Non-overlapping after
    assert is_date_overlap(date(2026, 12, 20), date(2026, 12, 25), date(2026, 12, 10), date(2026, 12, 15)) is False


# 2. Location Privacy Utility Unit Tests
def test_location_privacy_utility():
    # Mumbai coordinates
    lat, lon = 18.9220, 72.8347
    # Haversine distance between Mumbai and Pune (~120 km)
    pune_lat, pune_lon = 18.5204, 73.8567
    dist = haversine_distance_km(lat, lon, pune_lat, pune_lon)
    assert 110.0 <= dist <= 135.0

    # Approximate coordinates fuzzing
    approx_lat, approx_lon = approximate_coordinates(lat, lon, precision_mode="approximate", fuzz_radius_km=5.0)
    # Never return identical raw floats
    assert (approx_lat, approx_lon) != (lat, lon)
    # But distance to approximate point should be within reasonable radius
    fuzz_dist = haversine_distance_km(lat, lon, approx_lat, approx_lon)
    assert fuzz_dist <= 10.0

    # Exact mode returns rounded coordinates
    exact_lat, exact_lon = approximate_coordinates(lat, lon, precision_mode="exact")
    assert round(exact_lat, 4) == round(lat, 4)
    assert round(exact_lon, 4) == round(lon, 4)

    # Bounding box bounds
    min_lat, max_lat, min_lon, max_lon = bounding_box(lat, lon, 50.0)
    assert min_lat < lat < max_lat
    assert min_lon < lon < max_lon


# 3. Destinations Seed and Search Tests
def test_destinations_seed_and_search(profile_api: tuple[TestClient, dict[str, str]]):
    client, _ = profile_api

    # Initial request seeds default destinations
    response = client.get("/api/v1/destinations")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 10
    names = [d["name"] for d in data["items"]]
    assert "Goa" in names
    assert "Mumbai" in names
    assert "Bengaluru" in names
    assert "Paris" in names

    # Search by alias "bombay" -> returns Mumbai
    resp_alias = client.get("/api/v1/destinations?q=bombay")
    assert resp_alias.status_code == 200
    alias_items = resp_alias.json()["items"]
    assert any(d["name"] == "Mumbai" for d in alias_items)

    # Search by alias "bangalore" -> returns Bengaluru
    resp_blr = client.get("/api/v1/destinations/search?q=bangalore")
    assert resp_blr.status_code == 200
    assert any(d["name"] == "Bengaluru" for d in resp_blr.json()["items"])

    # Lookup by slug
    resp_slug = client.get("/api/v1/destinations/goa")
    assert resp_slug.status_code == 200
    assert resp_slug.json()["slug"] == "goa"
    assert resp_slug.json()["country_code"] == "IND"


# 4. Nearby Destinations Geospatial Query
def test_destinations_nearby_geospatial(profile_api: tuple[TestClient, dict[str, str]]):
    client, _ = profile_api

    # Coordinates near Panaji, Goa
    resp_nearby = client.get("/api/v1/destinations/nearby?lat=15.5&lon=73.8&radius_km=150")
    assert resp_nearby.status_code == 200
    items = resp_nearby.json()["items"]
    assert len(items) >= 1
    # Goa should be the first closest destination
    assert items[0]["destination"]["name"] == "Goa"
    assert items[0]["distance_km"] < 20.0


# 5. Admin Destination CRUD and Duplicate Prevention
def test_admin_destination_crud(profile_api: tuple[TestClient, dict[str, str]]):
    client, identity = profile_api

    # Regular user cannot create destination (403)
    create_payload = {
        "name": "Kyoto",
        "slug": "kyoto",
        "country": "Japan",
        "country_code": "JPN",
        "region": "Kansai",
        "city": "Kyoto",
        "description": "Historic imperial capital of Japan.",
        "latitude": 35.0116,
        "longitude": 135.7681,
        "timezone": "Asia/Tokyo",
        "category": "heritage",
        "status": "active",
        "aliases": ["heian-kyo"],
    }
    resp_unauth = client.post("/api/v1/admin/destinations", json=create_payload)
    assert resp_unauth.status_code == 403

    # As travel_admin with travel.manage
    _request_as(client, role="travel_admin", permissions=["travel.read", "travel.manage"])
    resp_create = client.post("/api/v1/admin/destinations", json=create_payload)
    assert resp_create.status_code == 201
    dest = resp_create.json()
    assert dest["slug"] == "kyoto"
    assert "heian-kyo" in dest["aliases"]

    # Duplicate slug rejected with 409
    resp_dup = client.post("/api/v1/admin/destinations", json=create_payload)
    assert resp_dup.status_code == 409

    # Update destination
    dest_id = dest["id"]
    resp_update = client.patch(f"/api/v1/admin/destinations/{dest_id}", json={"description": "Updated ancient capital."})
    assert resp_update.status_code == 200
    assert resp_update.json()["description"] == "Updated ancient capital."

    # Restore identity
    _request_as(client, role="user", permissions=["profile.read", "profile.write"], user_id=identity["user_id"])


# 6. Trip Creation and Validation Tests
def test_trip_creation_validation(profile_api: tuple[TestClient, dict[str, str]]):
    client, identity = profile_api
    _request_as(client, role="user", permissions=["profile.read", "profile.write"], user_id=identity["user_id"])

    # Ensure Goa exists
    dest_res = client.get("/api/v1/destinations/goa")
    goa_id = dest_res.json()["id"]

    # Valid Trip Creation
    trip_payload = {
        "destination_id": goa_id,
        "title": "Sunsets & Seafood in North Goa",
        "description": "Planning a beach hopping and photography trip.",
        "start_date": "2026-11-10",
        "end_date": "2026-11-18",
        "visibility": "discoverable",
        "companion_preference": "open_to_companion",
        "party_size": 2,
        "intents": ["travel_companion", "activity_partner"],
    }
    resp_create = client.post("/api/v1/me/trips", json=trip_payload)
    assert resp_create.status_code == 201
    trip = resp_create.json()
    assert trip["title"] == "Sunsets & Seafood in North Goa"
    assert trip["status"] == "planned"
    assert trip["destination"]["name"] == "Goa"
    assert "travel_companion" in trip["intents"]

    # Date validation: start_date > end_date returns 422
    invalid_dates = {**trip_payload, "start_date": "2026-11-20", "end_date": "2026-11-10"}
    resp_invalid = client.post("/api/v1/me/trips", json=invalid_dates)
    assert resp_invalid.status_code == 422

    # Invalid destination returns 400
    invalid_dest = {**trip_payload, "destination_id": "non-existent-destination-uuid"}
    resp_bad_dest = client.post("/api/v1/me/trips", json=invalid_dest)
    assert resp_bad_dest.status_code == 400


# 7. Trip CRUD and Status Transitions
def test_trip_crud_and_status_transitions(profile_api: tuple[TestClient, dict[str, str]]):
    client, identity = profile_api
    _request_as(client, role="user", permissions=["profile.read", "profile.write"], user_id=identity["user_id"])

    dest_res = client.get("/api/v1/destinations/mumbai")
    mumbai_id = dest_res.json()["id"]

    # Create trip
    trip_payload = {
        "destination_id": mumbai_id,
        "title": "Heritage Walk in South Mumbai",
        "description": "Art deco buildings and street food.",
        "start_date": "2026-12-01",
        "end_date": "2026-12-05",
        "visibility": "discoverable",
        "companion_preference": "open_to_companion",
        "party_size": 1,
        "intents": ["local_guide"],
    }
    trip_id = client.post("/api/v1/me/trips", json=trip_payload).json()["id"]

    # Get my trips
    my_trips = client.get("/api/v1/me/trips").json()
    assert any(t["id"] == trip_id for t in my_trips["items"])

    # Update trip details
    patch_res = client.patch(f"/api/v1/me/trips/{trip_id}", json={"party_size": 3, "status": "active"})
    assert patch_res.status_code == 200
    assert patch_res.json()["party_size"] == 3
    assert patch_res.json()["status"] == "active"

    # Transition active -> completed -> archived (valid)
    assert client.patch(f"/api/v1/me/trips/{trip_id}", json={"status": "completed"}).status_code == 200
    assert client.patch(f"/api/v1/me/trips/{trip_id}", json={"status": "archived"}).status_code == 200

    # Invalid transition: archived -> active is rejected (400)
    assert client.patch(f"/api/v1/me/trips/{trip_id}", json={"status": "active"}).status_code == 400

    # Delete trip
    del_res = client.delete(f"/api/v1/me/trips/{trip_id}")
    assert del_res.status_code == 200
    assert del_res.json()["ok"] is True

    # 404 after deletion
    assert client.get(f"/api/v1/me/trips/{trip_id}").status_code == 404


# 8. Trip Ownership and IDOR Protection
def test_trip_ownership_idor_protection(profile_api: tuple[TestClient, dict[str, str]]):
    client, _ = profile_api

    # User A creates a trip
    _request_as(client, role="user", permissions=["profile.read", "profile.write"], user_id="user-alpha-id")
    dest_id = client.get("/api/v1/destinations/paris").json()["id"]
    trip_id = client.post(
        "/api/v1/me/trips",
        json={
            "destination_id": dest_id,
            "title": "User Alpha's Paris Itinerary",
            "start_date": "2026-10-15",
            "end_date": "2026-10-20",
            "visibility": "private",
            "companion_preference": "travelling_alone",
            "party_size": 1,
            "intents": ["local_guide"],
        },
    ).json()["id"]

    # User B attempts to access/modify/delete User A's private trip
    _request_as(client, role="user", permissions=["profile.read", "profile.write"], user_id="user-bravo-id")

    # Access via /me returns 404
    assert client.get(f"/api/v1/me/trips/{trip_id}").status_code == 404
    # Access via public /trips returns 404 because visibility is private
    assert client.get(f"/api/v1/trips/{trip_id}").status_code == 404
    # Modification attempt returns 404
    assert client.patch(f"/api/v1/me/trips/{trip_id}", json={"title": "Hacked Title"}).status_code == 404
    # Deletion attempt returns 404
    assert client.delete(f"/api/v1/me/trips/{trip_id}").status_code == 404


# 9. Public Trip Discovery and Privacy Filtering
def test_public_trip_discovery_and_privacy(profile_api: tuple[TestClient, dict[str, str]]):
    client, _ = profile_api

    _request_as(client, role="user", permissions=["profile.read", "profile.write"], user_id="user-traveler-1")
    dest_id = client.get("/api/v1/destinations/jaipur").json()["id"]

    # Create Discoverable Trip
    disc_trip_id = client.post(
        "/api/v1/me/trips",
        json={
            "destination_id": dest_id,
            "title": "Discoverable Jaipur Fort Tour",
            "start_date": "2026-12-10",
            "end_date": "2026-12-15",
            "visibility": "discoverable",
            "companion_preference": "open_to_companion",
            "party_size": 2,
            "intents": ["travel_companion"],
        },
    ).json()["id"]

    # Create Private Trip
    priv_trip_id = client.post(
        "/api/v1/me/trips",
        json={
            "destination_id": dest_id,
            "title": "Secret Solo Retreat",
            "start_date": "2026-12-10",
            "end_date": "2026-12-15",
            "visibility": "private",
            "companion_preference": "travelling_alone",
            "party_size": 1,
            "intents": [],
        },
    ).json()["id"]

    # Public discovery should include discoverable trip, but NEVER private trip
    public_res = client.get("/api/v1/trips").json()
    disc_ids = [t["id"] for t in public_res["items"]]
    assert disc_trip_id in disc_ids
    assert priv_trip_id not in disc_ids

    # Query with date overlap matching [2026-12-12, 2026-12-18]
    overlap_res = client.get(f"/api/v1/trips?destination_id={dest_id}&start_date=2026-12-12&end_date=2026-12-18").json()
    assert any(t["id"] == disc_trip_id for t in overlap_res["items"])

    # Query with non-overlapping dates [2026-12-20, 2026-12-25]
    non_overlap_res = client.get(f"/api/v1/trips?destination_id={dest_id}&start_date=2026-12-20&end_date=2026-12-25").json()
    assert not any(t["id"] == disc_trip_id for t in non_overlap_res["items"])


# 10. User Location Privacy and Consent
def test_user_location_privacy(profile_api: tuple[TestClient, dict[str, str]]):
    client, identity = profile_api
    _request_as(client, role="user", permissions=["profile.read", "profile.write"], user_id=identity["user_id"])

    # Set location with approximate sharing mode
    loc_payload = {
        "latitude": 15.4989,
        "longitude": 73.8278,
        "precision": "approximate",
        "sharing_mode": "approximate",
        "source": "browser",
        "city": "Panaji",
        "region": "Goa",
        "country_code": "IND",
    }
    resp_set = client.put("/api/v1/me/location", json=loc_payload)
    assert resp_set.status_code == 200
    loc_data = resp_set.json()
    # In approximate mode, exact coordinates are hidden/None
    assert loc_data["latitude"] is None
    assert loc_data["longitude"] is None
    # Approximate coordinates are populated
    assert loc_data["approx_latitude"] is not None
    assert loc_data["approx_longitude"] is not None

    # Update with explicit_share
    resp_explicit = client.put("/api/v1/me/location", json={**loc_payload, "sharing_mode": "explicit_share"})
    assert resp_explicit.status_code == 200
    loc_explicit = resp_explicit.json()
    assert loc_explicit["latitude"] == 15.4989
    assert loc_explicit["longitude"] == 73.8278

    # Delete location
    resp_del = client.delete("/api/v1/me/location")
    assert resp_del.status_code == 200
    assert resp_del.json()["ok"] is True
    assert client.get("/api/v1/me/location").json() is None


# 11. Admin Trips Review and Permissions
def test_admin_trip_management(profile_api: tuple[TestClient, dict[str, str]]):
    client, _ = profile_api

    # Regular user cannot access /admin/trips
    _request_as(client, role="user", permissions=["profile.read"], user_id="normal-user")
    assert client.get("/api/v1/admin/trips").status_code == 403

    # Travel admin with travel.read can view admin trips
    _request_as(client, role="travel_admin", permissions=["travel.read", "travel.manage"], user_id="travel-admin-1")
    resp_admin = client.get("/api/v1/admin/trips")
    assert resp_admin.status_code == 200
    assert "items" in resp_admin.json()
    assert "total" in resp_admin.json()
