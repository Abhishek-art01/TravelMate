from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.core.security import get_current_user
from app.core.verification_dependencies import get_verification_service
from app.main import app
from app.services.verification_provider import MockVerificationProvider, NotConfiguredVerificationProvider
from app.services.verification_service import VerificationService
from app.services.verification_storage import MemoryVerificationStorage


@pytest.fixture
def verification_setup(
    profile_api: tuple[TestClient, dict[str, str]],
) -> Iterator[tuple[TestClient, dict[str, str], VerificationService, MockVerificationProvider, MemoryVerificationStorage]]:
    client, identity = profile_api
    storage = MemoryVerificationStorage()
    provider = MockVerificationProvider(webhook_secret="test-webhook-secret-999")
    settings = Settings(
        verification_provider="mock",
        verification_webhook_secret="test-webhook-secret-999",
        verification_max_attempts=3,
        verification_signed_url_ttl_seconds=120,
    )
    service = VerificationService(provider=provider, storage=storage, settings=settings)

    app.dependency_overrides[get_verification_service] = lambda: service
    try:
        yield client, identity, service, provider, storage
    finally:
        app.dependency_overrides.pop(get_verification_service, None)


def _request_as(client: TestClient, role: str, permissions: list[str], user_id: str = "admin-user-1"):
    async def current_user() -> dict[str, Any]:
        return {
            "user_id": user_id,
            "email": f"{role}@travelmate.test",
            "role": role,
            "permissions": permissions,
            "claims": {},
        }

    app.dependency_overrides[get_current_user] = current_user


def test_verification_overview_returns_independent_channels(
    verification_setup: tuple[TestClient, dict[str, str], VerificationService, MockVerificationProvider, MemoryVerificationStorage],
) -> None:
    client, _identity, _, _, _ = verification_setup

    response = client.get("/api/v1/me/verification/status")
    assert response.status_code == 200
    data = response.json()

    me_res = client.get("/api/v1/me")
    local_user_id = me_res.json()["user_id"]
    assert data["user_id"] == local_user_id
    assert "checks" in data
    assert set(data["checks"].keys()) == {"email", "social", "selfie", "government_id", "video"}
    assert data["checks"]["email"]["type"] == "email"
    assert data["checks"]["government_id"]["status"] == "not_started"
    assert data["checks"]["selfie"]["status"] == "not_started"
    assert data["checks"]["video"]["status"] == "not_started"

    # Backward compatible endpoint
    legacy_res = client.get("/api/v1/verification/status")
    assert legacy_res.status_code == 200
    assert legacy_res.json()["verification_status"] == data["verification_status"]


def test_user_cannot_mark_self_verified(
    verification_setup: tuple[TestClient, dict[str, str], VerificationService, MockVerificationProvider, MemoryVerificationStorage],
) -> None:
    client, _, _, _, _ = verification_setup

    # User attempting to post directly to approve or mark verified
    res = client.post("/api/v1/verification/verified", json={"verified": True})
    assert res.status_code == 404

    # User attempting admin approve endpoint
    res2 = client.post("/api/v1/admin/verification/case-123/approve", json={"reason": "Self approved"})
    assert res2.status_code == 403


def test_unconfigured_provider_fails_safely(
    profile_api: tuple[TestClient, dict[str, str]],
) -> None:
    client, _, = profile_api
    storage = MemoryVerificationStorage()
    provider = NotConfiguredVerificationProvider()
    settings = Settings(verification_provider="not_configured")
    service = VerificationService(provider=provider, storage=storage, settings=settings)

    app.dependency_overrides[get_verification_service] = lambda: service
    try:
        response = client.post("/api/v1/me/verification/government_id/start")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "VERIFICATION_PROVIDER_NOT_CONFIGURED"
    finally:
        app.dependency_overrides.pop(get_verification_service, None)


def test_verification_flow_with_mock_provider_and_storage(
    verification_setup: tuple[TestClient, dict[str, str], VerificationService, MockVerificationProvider, MemoryVerificationStorage],
) -> None:
    client, _identity, _, _, storage = verification_setup

    # 1. Start verification session
    start_res = client.post("/api/v1/me/verification/government_id/start")
    assert start_res.status_code == 200
    start_data = start_res.json()
    verification_id = start_data["verification_id"]
    assert start_data["verification_type"] == "government_id"
    assert start_data["status"] == "pending"
    assert start_data["attempt_number"] == 1
    assert "https://verify.mock-provider.invalid" in start_data["session_url"]

    # 2. Request private media upload
    media_req_res = client.post(
        f"/api/v1/me/verification/{verification_id}/media",
        json={"media_type": "document_front", "mime_type": "image/jpeg", "size_bytes": 102400},
    )
    assert media_req_res.status_code == 200
    media_data = media_req_res.json()
    media_id = media_data["media_id"]
    upload_url = media_data["upload_url"]
    object_key = upload_url.split("/upload/")[1].split("?")[0]
    assert object_key.startswith("verification/")
    assert f"/{verification_id}/{media_id}.jpg" in object_key

    # Simulate object in storage
    storage.objects[object_key] = ("image/jpeg", b"sample-id-bytes" * 10)

    # 3. Complete media upload
    complete_res = client.post(f"/api/v1/me/verification/{verification_id}/media/{media_id}/complete")
    assert complete_res.status_code == 200
    assert complete_res.json()["media_id"] == media_id

    # 4. Submit verification
    submit_res = client.post(f"/api/v1/me/verification/{verification_id}/submit")
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == "submitted"
    assert submit_res.json()["submitted_at"] is not None


def test_concurrent_start_and_attempt_limits(
    verification_setup: tuple[TestClient, dict[str, str], VerificationService, MockVerificationProvider, MemoryVerificationStorage],
) -> None:
    client, _, _, _, _ = verification_setup

    # Start attempt 1
    res1 = client.post("/api/v1/me/verification/selfie/start")
    assert res1.status_code == 200
    vid1 = res1.json()["verification_id"]

    # Cannot start another while attempt 1 is active (pending)
    res_conflict = client.post("/api/v1/me/verification/selfie/start")
    assert res_conflict.status_code == 409
    assert res_conflict.json()["error"]["code"] == "VERIFICATION_ALREADY_ACTIVE"

    # Cancel attempt 1 so attempt 2 can start
    cancel_res = client.post(f"/api/v1/me/verification/{vid1}/cancel")
    assert cancel_res.status_code == 200

    # Start attempt 2
    res2 = client.post("/api/v1/me/verification/selfie/start")
    assert res2.status_code == 200
    assert res2.json()["attempt_number"] == 2
    client.post(f"/api/v1/me/verification/{vid1}/cancel")

    # Start attempt 3
    res3 = client.post("/api/v1/me/verification/selfie/start")
    assert res3.status_code == 200
    assert res3.json()["attempt_number"] == 3
    client.post(f"/api/v1/me/verification/{vid1}/cancel")

    # Attempt 4 should hit the limit (max 3)
    res4 = client.post("/api/v1/me/verification/selfie/start")
    assert res4.status_code == 429
    assert res4.json()["error"]["code"] == "VERIFICATION_LIMIT_REACHED"


def test_user_cannot_access_another_users_verification(
    verification_setup: tuple[TestClient, dict[str, str], VerificationService, MockVerificationProvider, MemoryVerificationStorage],
) -> None:
    client, _, _, _, _ = verification_setup

    # User 1 starts verification
    start_res = client.post("/api/v1/me/verification/government_id/start")
    verification_id = start_res.json()["verification_id"]

    # Switch identity to User 2
    async def user_two() -> dict[str, Any]:
        return {"user_id": "supabase-user-b", "email": "other@travelmate.test", "role": "user", "claims": {}}

    app.dependency_overrides[get_current_user] = user_two
    try:
        # User 2 tries to view User 1's verification case
        res = client.get(f"/api/v1/me/verification/{verification_id}")
        assert res.status_code == 404

        # User 2 tries to submit User 1's verification
        res_sub = client.post(f"/api/v1/me/verification/{verification_id}/submit")
        assert res_sub.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_rbac_support_and_moderator_cannot_access_verification(
    verification_setup: tuple[TestClient, dict[str, str], VerificationService, MockVerificationProvider, MemoryVerificationStorage],
) -> None:
    client, _, _, _, _ = verification_setup

    # 1. Test Support Role
    _request_as(client, role="support", permissions=["support.read", "support.manage", "users.read"])
    queue_res = client.get("/api/v1/admin/verification")
    assert queue_res.status_code == 403

    media_res = client.get("/api/v1/admin/verification/case-1/media/media-1/url")
    assert media_res.status_code == 403

    # 2. Test Moderator Role
    _request_as(client, role="moderator", permissions=["profile.read", "profile.write", "moderation.read"])
    queue_res2 = client.get("/api/v1/admin/verification")
    assert queue_res2.status_code == 403


def test_admin_verification_queue_and_review_workflow(
    verification_setup: tuple[TestClient, dict[str, str], VerificationService, MockVerificationProvider, MemoryVerificationStorage],
) -> None:
    client, _identity, _, _, storage = verification_setup

    # User starts and submits verification
    start_res = client.post("/api/v1/me/verification/government_id/start")
    vid = start_res.json()["verification_id"]
    media_res = client.post(
        f"/api/v1/me/verification/{vid}/media",
        json={"media_type": "document_front", "mime_type": "image/jpeg", "size_bytes": 50000},
    )
    media_id = media_res.json()["media_id"]
    upload_url = media_res.json()["upload_url"]
    object_key = upload_url.split("/upload/")[1].split("?")[0]
    storage.objects[object_key] = ("image/jpeg", b"mock-id-document")

    client.post(f"/api/v1/me/verification/{vid}/submit")

    # Switch to Verification Admin
    _request_as(
        client,
        role="verification_admin",
        permissions=["verification.read", "verification.review", "verification.approve", "verification.reject", "verification.media.read"],
    )

    # 1. Admin lists queue
    queue_res = client.get("/api/v1/admin/verification")
    assert queue_res.status_code == 200
    queue_data = queue_res.json()
    assert queue_data["total"] >= 1
    case = next(item for item in queue_data["items"] if item["id"] == vid)
    assert case["status"] == "submitted"
    assert case["verification_type"] == "government_id"

    # 2. Admin views case detail (does not pre-generate media URLs)
    detail_res = client.get(f"/api/v1/admin/verification/{vid}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert len(detail["media"]) == 1
    assert detail["media"][0]["media_id"] == media_id
    assert "download_url" not in detail["media"][0]  # Safe response: no permanent/automatic URL

    # 3. Start review
    review_res = client.post(f"/api/v1/admin/verification/{vid}/review")
    assert review_res.status_code == 200
    assert review_res.json()["status"] == "in_review"

    # 4. View secure media with explicit verification.media.read
    url_res = client.get(f"/api/v1/admin/verification/{vid}/media/{media_id}/url")
    assert url_res.status_code == 200
    assert "download_url" in url_res.json()
    assert url_res.json()["expires_at"] is not None

    # 5. Approve case
    approve_res = client.post(f"/api/v1/admin/verification/{vid}/approve", json={"reason": "Valid Aadhaar ID."})
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "verified"


def test_admin_media_access_requires_explicit_permission(
    verification_setup: tuple[TestClient, dict[str, str], VerificationService, MockVerificationProvider, MemoryVerificationStorage],
) -> None:
    client, _identity, _, _, storage = verification_setup

    start_res = client.post("/api/v1/me/verification/government_id/start")
    vid = start_res.json()["verification_id"]
    media_res = client.post(
        f"/api/v1/me/verification/{vid}/media",
        json={"media_type": "document_front", "mime_type": "image/jpeg", "size_bytes": 50000},
    )
    media_id = media_res.json()["media_id"]
    upload_url = media_res.json()["upload_url"]
    object_key = upload_url.split("/upload/")[1].split("?")[0]
    storage.objects[object_key] = ("image/jpeg", b"mock-id-document")

    # Reviewer WITHOUT verification.media.read permission
    _request_as(
        client,
        role="reviewer_restricted",
        permissions=["verification.read", "verification.review"],
    )

    url_res = client.get(f"/api/v1/admin/verification/{vid}/media/{media_id}/url")
    assert url_res.status_code == 403
    assert url_res.json()["error"]["code"] == "FORBIDDEN"


def test_admin_rejection_requires_reason(
    verification_setup: tuple[TestClient, dict[str, str], VerificationService, MockVerificationProvider, MemoryVerificationStorage],
) -> None:
    client, _, _, _, _ = verification_setup

    start_res = client.post("/api/v1/me/verification/video/start")
    vid = start_res.json()["verification_id"]
    client.post(f"/api/v1/me/verification/{vid}/submit")

    _request_as(
        client,
        role="verification_admin",
        permissions=["verification.read", "verification.review", "verification.reject"],
    )
    client.post(f"/api/v1/admin/verification/{vid}/review")

    # Rejection without reason fails
    res_no_reason = client.post(f"/api/v1/admin/verification/{vid}/reject", json={"reason": "   "})
    assert res_no_reason.status_code == 422
    assert res_no_reason.json()["error"]["code"] == "REASON_REQUIRED"

    # Rejection with reason succeeds
    res_reject = client.post(f"/api/v1/admin/verification/{vid}/reject", json={"reason": "Lighting too dark, face not visible."})
    assert res_reject.status_code == 200
    assert res_reject.json()["status"] == "rejected"


def test_webhooks_signature_replay_and_idempotency(
    verification_setup: tuple[TestClient, dict[str, str], VerificationService, MockVerificationProvider, MemoryVerificationStorage],
) -> None:
    client, _, _, provider, _ = verification_setup

    start_res = client.post("/api/v1/me/verification/government_id/start")
    vid = start_res.json()["verification_id"]

    raw_payload = b'{"event":"decision","verification_id":"' + vid.encode() + b'","status":"in_review","reason":"documents_uploaded"}'
    ts = str(int(time.time()))
    valid_sig = provider.generate_signature(raw_payload, ts)

    # 1. Missing signature
    res_no_sig = client.post(
        "/api/v1/webhooks/verification/mock",
        content=raw_payload,
        headers={"x-timestamp": ts, "Content-Type": "application/json"},
    )
    assert res_no_sig.status_code == 401

    # 2. Invalid signature
    res_bad_sig = client.post(
        "/api/v1/webhooks/verification/mock",
        content=raw_payload,
        headers={"x-signature": "invalid-sig", "x-timestamp": ts, "Content-Type": "application/json"},
    )
    assert res_bad_sig.status_code == 401

    # 3. Expired timestamp (replay protection)
    old_ts = str(int(time.time()) - 400)
    old_sig = provider.generate_signature(raw_payload, old_ts)
    res_expired = client.post(
        "/api/v1/webhooks/verification/mock",
        content=raw_payload,
        headers={"x-signature": old_sig, "x-timestamp": old_ts, "Content-Type": "application/json"},
    )
    assert res_expired.status_code == 401

    # 4. Valid webhook
    res_valid = client.post(
        "/api/v1/webhooks/verification/mock",
        content=raw_payload,
        headers={"x-signature": valid_sig, "x-timestamp": ts, "Content-Type": "application/json"},
    )
    assert res_valid.status_code == 200
    assert res_valid.json()["new_status"] == "in_review"

    # 5. Duplicate webhook (idempotency)
    res_dup = client.post(
        "/api/v1/webhooks/verification/mock",
        content=raw_payload,
        headers={"x-signature": valid_sig, "x-timestamp": ts, "Content-Type": "application/json"},
    )
    assert res_dup.status_code == 200
    assert res_dup.json()["status"] == "idempotent_ok"


def test_storage_namespace_isolation(
    verification_setup: tuple[TestClient, dict[str, str], VerificationService, MockVerificationProvider, MemoryVerificationStorage],
) -> None:
    _, _, _, _, storage = verification_setup

    # Verification storage rejects keys that do not start with 'verification/'
    with pytest.raises(ValueError, match="private 'verification/' namespace"):
        import asyncio
        asyncio.run(storage.create_upload_url("profile/user-1/photo.jpg", "image/jpeg", 100, 120))


def test_retention_pruning_and_account_deletion_cleanup(
    verification_setup: tuple[TestClient, dict[str, str], VerificationService, MockVerificationProvider, MemoryVerificationStorage],
) -> None:
    client, _identity, service, _, storage = verification_setup

    start_res = client.post("/api/v1/me/verification/government_id/start")
    vid = start_res.json()["verification_id"]
    media_res = client.post(
        f"/api/v1/me/verification/{vid}/media",
        json={"media_type": "document_front", "mime_type": "image/jpeg", "size_bytes": 50000},
    )
    upload_url = media_res.json()["upload_url"]
    object_key = upload_url.split("/upload/")[1].split("?")[0]
    storage.objects[object_key] = ("image/jpeg", b"mock-id-document")

    # Verify object is present in storage
    assert object_key in storage.objects

    me_res = client.get("/api/v1/me")
    local_user_id = me_res.json()["user_id"]

    # Test account deletion cleanup
    import asyncio

    from app.core.dependencies import get_db_session

    async def run_cleanup():
        session_gen = app.dependency_overrides[get_db_session]()
        session = await anext(session_gen)
        try:
            deleted_count = await service.delete_user_verification_media(
                session=session,
                user_id=local_user_id,
                actor_id=local_user_id,
                reason="user_gdpr_account_deletion",
            )
            assert deleted_count == 1
        finally:
            await session.close()

    asyncio.run(run_cleanup())

    # Verify object is removed from private storage
    assert object_key not in storage.objects
    assert object_key in storage.deleted_keys
