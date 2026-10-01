from __future__ import annotations

from collections.abc import Iterator
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.media_dependencies import get_profile_media_service
from app.main import app
from app.services.media import ProfileMediaService
from app.services.media_storage import StorageUnavailable, StoredObject


class MemoryStorage:
    provider = "r2"

    def __init__(self):
        self.objects: dict[str, tuple[str, bytes]] = {}
        self.deleted: list[str] = []

    async def create_upload_url(self, object_key: str, content_type: str, size_bytes: int, expires_seconds: int) -> str:
        return f"https://storage.invalid/upload/{object_key}?expires={expires_seconds}"

    async def inspect_object(self, object_key: str) -> tuple[StoredObject, bytes]:
        if object_key not in self.objects:
            raise StorageUnavailable("missing object")
        mime_type, data = self.objects[object_key]
        return StoredObject(len(data), mime_type), data

    async def create_download_url(self, object_key: str, expires_seconds: int) -> str:
        return f"https://storage.invalid/read/{object_key}?expires={expires_seconds}"

    async def delete_object(self, object_key: str) -> None:
        self.deleted.append(object_key)
        self.objects.pop(object_key, None)


def make_png() -> bytes:
    output = BytesIO()
    Image.new("RGB", (24, 16), color=(30, 90, 70)).save(output, format="PNG")
    return output.getvalue()


@pytest.fixture
def media_api(profile_api: tuple[TestClient, dict[str, str]]) -> Iterator[tuple[TestClient, dict[str, str], MemoryStorage]]:
    client, identity = profile_api
    storage = MemoryStorage()
    app.dependency_overrides[get_profile_media_service] = lambda: ProfileMediaService(storage)
    try:
        yield client, identity, storage
    finally:
        app.dependency_overrides.pop(get_profile_media_service, None)


def create_upload(client: TestClient, *, data: bytes | None = None, visibility: str = "profile_only") -> tuple[str, bytes]:
    image = data if data is not None else make_png()
    response = client.post("/api/v1/media/uploads", json={
        "mime_type": "image/png",
        "size_bytes": len(image),
        "visibility": visibility,
    })
    assert response.status_code == 200
    return response.json()["media_id"], image


def test_upload_requires_authentication() -> None:
    response = TestClient(app).post("/api/v1/media/uploads", json={"mime_type": "image/png", "size_bytes": 99})
    assert response.status_code == 401


def test_upload_key_is_generated_and_image_becomes_ready_only_after_validation(media_api) -> None:
    client, _, storage = media_api
    media_id, image = create_upload(client)
    upload = client.post(f"/api/v1/media/uploads/{media_id}/complete")
    assert upload.status_code == 503

    row_key = f"profile/{media_id}/original.png"
    storage.objects[row_key] = ("image/png", image)
    complete = client.post(f"/api/v1/media/uploads/{media_id}/complete")

    assert complete.status_code == 200
    assert complete.json()["processing_status"] == "ready"
    assert complete.json()["moderation_status"] == "pending_review"
    assert complete.json()["width"] == 24
    assert "filename" not in complete.json()


def test_upload_rejects_mismatched_or_invalid_image_content(media_api) -> None:
    client, _, storage = media_api
    invalid_image = b"not a png file"
    media_id, _ = create_upload(client, data=invalid_image)
    key = f"profile/{media_id}/original.png"
    storage.objects[key] = ("image/png", invalid_image)

    response = client.post(f"/api/v1/media/uploads/{media_id}/complete")
    assert response.status_code == 422
    assert response.json()["error"]["code"] in {"INVALID_IMAGE", "IMAGE_DIMENSIONS_INVALID"}
    assert f"profile/{media_id}/original.png" in storage.deleted


def test_upload_size_must_match_authorized_size(media_api) -> None:
    client, _, storage = media_api
    image = make_png()
    created = client.post("/api/v1/media/uploads", json={"mime_type": "image/png", "size_bytes": len(image) + 10})
    assert created.status_code == 200
    media_id = created.json()["media_id"]
    storage.objects[f"profile/{media_id}/original.png"] = ("image/png", image)

    response = client.post(f"/api/v1/media/uploads/{media_id}/complete")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "MEDIA_SIZE_MISMATCH"


def test_user_cannot_delete_another_users_media(media_api) -> None:
    client, identity, storage = media_api
    image = make_png()
    media_id, _ = create_upload(client, data=image)
    storage.objects[f"profile/{media_id}/original.png"] = ("image/png", image)
    assert client.post(f"/api/v1/media/uploads/{media_id}/complete").status_code == 200

    identity["user_id"] = "different-supabase-user"
    response = client.delete(f"/api/v1/media/{media_id}")
    assert response.status_code == 404
    assert not storage.deleted


def test_owner_can_list_reorder_and_delete_media(media_api) -> None:
    client, _, storage = media_api
    image = make_png()
    first_id, _ = create_upload(client, data=image)
    storage.objects[f"profile/{first_id}/original.png"] = ("image/png", image)
    assert client.post(f"/api/v1/media/uploads/{first_id}/complete").status_code == 200
    second_id, _ = create_upload(client, data=image)
    storage.objects[f"profile/{second_id}/original.png"] = ("image/png", image)
    assert client.post(f"/api/v1/media/uploads/{second_id}/complete").status_code == 200

    listing = client.get("/api/v1/media")
    assert listing.status_code == 200
    assert len(listing.json()["items"]) == 2
    assert all(item["download_url"].startswith("https://storage.invalid/read/") for item in listing.json()["items"])

    reordered = client.patch(f"/api/v1/media/{second_id}/order", json={"sort_order": 0})
    assert reordered.status_code == 200
    assert reordered.json()["sort_order"] == 0
    assert client.get("/api/v1/media").json()["items"][0]["media_id"] == second_id

    deleted = client.delete(f"/api/v1/media/{second_id}")
    assert deleted.status_code == 204
    assert storage.deleted == [f"profile/{second_id}/original.png"]
    assert [item["media_id"] for item in client.get("/api/v1/media").json()["items"]] == [first_id]
