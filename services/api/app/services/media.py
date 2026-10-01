from __future__ import annotations

import warnings
from datetime import UTC, datetime, timedelta
from io import BytesIO
from uuid import uuid4

from fastapi import HTTPException, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.models.media import MediaAsset
from app.models.profile import UserProfile
from app.models.user import User
from app.schemas.media import MediaPage, MediaRead, ProfileUploadCreate, ProfileUploadCreated
from app.services.media_storage import MediaStorage, StorageUnavailable, StoredObject

MIME_FORMATS = {"image/jpeg": ("JPEG", "jpg"), "image/png": ("PNG", "png"), "image/webp": ("WEBP", "webp")}


def _http_error(code: str, message: str, http_status: int) -> HTTPException:
    return HTTPException(status_code=http_status, detail={"error": {"code": code, "message": message}})


async def _owned_profile_media(session: AsyncSession, user_id: str, media_id: str) -> MediaAsset:
    result = await session.execute(select(MediaAsset).where(
        MediaAsset.id == media_id,
        MediaAsset.user_id == user_id,
        MediaAsset.media_type == "profile_media",
        MediaAsset.deleted_at.is_(None),
    ))
    asset = result.scalar_one_or_none()
    if asset is None:
        raise _http_error("MEDIA_NOT_FOUND", "Media item not found.", status.HTTP_404_NOT_FOUND)
    return asset


def _asset_read(asset: MediaAsset, download_url: str | None = None) -> MediaRead:
    return MediaRead(
        media_id=asset.id,
        media_type=asset.media_type,
        processing_status=asset.processing_status,
        moderation_status=asset.moderation_status,
        visibility=asset.visibility,
        mime_type=asset.mime_type,
        size_bytes=asset.size_bytes,
        width=asset.width,
        height=asset.height,
        sort_order=asset.sort_order,
        created_at=asset.created_at,
        download_url=download_url,
    )


class ProfileMediaService:
    def __init__(self, storage: MediaStorage, settings: Settings | None = None):
        self.storage = storage
        self.settings = settings or get_settings()

    async def create_upload(self, session: AsyncSession, user: User, payload: ProfileUploadCreate) -> ProfileUploadCreated:
        maximum = self.settings.media_max_profile_photo_size_bytes
        if payload.size_bytes > maximum:
            raise _http_error("MEDIA_TOO_LARGE", "The selected photo exceeds the upload size limit.", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        if payload.visibility == "public":
            profile_result = await session.execute(select(UserProfile).where(UserProfile.user_id == user.id))
            profile = profile_result.scalar_one_or_none()
            if profile is None or profile.profile_visibility not in {"public", "discoverable"} or not profile.discovery_visibility:
                raise _http_error("PROFILE_NOT_PUBLIC", "Enable a discoverable profile before requesting public media.", status.HTTP_409_CONFLICT)

        active_count = await session.scalar(select(func.count()).select_from(MediaAsset).where(
            MediaAsset.user_id == user.id,
            MediaAsset.media_type == "profile_media",
            MediaAsset.deleted_at.is_(None),
            MediaAsset.processing_status.in_(["uploading", "processing", "ready"]),
        ))
        if (active_count or 0) >= self.settings.media_max_profile_photos:
            raise _http_error("MEDIA_LIMIT_REACHED", "The profile photo limit has been reached.", status.HTTP_409_CONFLICT)

        extension = MIME_FORMATS[payload.mime_type][1]
        media_id = str(uuid4())
        object_key = f"profile/{media_id}/original.{extension}"
        now = datetime.now(UTC)
        asset = MediaAsset(
            id=media_id,
            user_id=user.id,
            media_type="profile_media",
            storage_provider=self.storage.provider,
            object_key=object_key,
            processing_status="uploading",
            moderation_status="pending_review",
            visibility=payload.visibility,
            mime_type=payload.mime_type,
            size_bytes=payload.size_bytes,
            sort_order=int(active_count or 0),
            created_at=now,
            updated_at=now,
        )
        session.add(asset)
        await session.commit()

        try:
            upload_url = await self.storage.create_upload_url(
                object_key,
                payload.mime_type,
                payload.size_bytes,
                self.settings.media_signed_url_ttl_seconds,
            )
        except StorageUnavailable as exc:
            asset.processing_status = "failed"
            asset.updated_at = datetime.now(UTC)
            await session.commit()
            raise _http_error("MEDIA_STORAGE_UNAVAILABLE", "Profile media upload is temporarily unavailable.", status.HTTP_503_SERVICE_UNAVAILABLE) from exc

        ttl = min(max(self.settings.media_signed_url_ttl_seconds, 60), 900)
        return ProfileUploadCreated(
            media_id=asset.id,
            upload_url=upload_url,
            expires_at=datetime.now(UTC) + timedelta(seconds=ttl),
            required_headers={"Content-Type": payload.mime_type},
        )

    @staticmethod
    def _validate_image(data: bytes, mime_type: str, declared_size: int, stored: StoredObject, settings: Settings) -> tuple[int, int]:
        if stored.size_bytes != declared_size or len(data) != declared_size or len(data) > settings.media_max_profile_photo_size_bytes:
            raise _http_error("MEDIA_SIZE_MISMATCH", "Uploaded media size did not match the authorized size.", status.HTTP_422_UNPROCESSABLE_ENTITY)
        if stored.content_type != mime_type:
            raise _http_error("MEDIA_TYPE_MISMATCH", "Uploaded media content type did not match its authorization.", status.HTTP_422_UNPROCESSABLE_ENTITY)

        expected_format = MIME_FORMATS[mime_type][0]
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(BytesIO(data)) as image:
                    if image.format != expected_format:
                        raise _http_error("INVALID_IMAGE", "The uploaded file is not a valid image of the selected type.", status.HTTP_422_UNPROCESSABLE_ENTITY)
                    image.verify()
                with Image.open(BytesIO(data)) as image:
                    width, height = image.size
                    if width < 1 or height < 1 or width * height > 40_000_000:
                        raise _http_error("IMAGE_DIMENSIONS_INVALID", "The uploaded image dimensions are not supported.", status.HTTP_422_UNPROCESSABLE_ENTITY)
                    return width, height
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
            raise _http_error("INVALID_IMAGE", "The uploaded file could not be validated as an image.", status.HTTP_422_UNPROCESSABLE_ENTITY) from exc

    async def complete_upload(self, session: AsyncSession, user: User, media_id: str) -> MediaRead:
        asset = await _owned_profile_media(session, user.id, media_id)
        if asset.processing_status != "uploading":
            raise _http_error("UPLOAD_STATE_INVALID", "This upload is not awaiting completion.", status.HTTP_409_CONFLICT)
        try:
            stored, data = await self.storage.inspect_object(asset.object_key)
        except StorageUnavailable as exc:
            raise _http_error("MEDIA_STORAGE_UNAVAILABLE", "Uploaded media could not be verified yet.", status.HTTP_503_SERVICE_UNAVAILABLE) from exc

        try:
            width, height = self._validate_image(data, asset.mime_type, asset.size_bytes, stored, self.settings)
        except HTTPException:
            asset.processing_status = "failed"
            asset.updated_at = datetime.now(UTC)
            await session.commit()
            try:
                await self.storage.delete_object(asset.object_key)
            except StorageUnavailable:
                pass
            raise
        asset.processing_status = "processing"
        asset.width = width
        asset.height = height
        asset.updated_at = datetime.now(UTC)
        await session.commit()

        # Image bytes and dimensions are validated, but moderation is deliberately not auto-approved.
        asset.processing_status = "ready"
        asset.updated_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(asset)
        return _asset_read(asset)

    async def list_media(self, session: AsyncSession, user: User, *, limit: int = 24, after: str | None = None) -> MediaPage:
        limit = min(max(limit, 1), 50)
        statement = select(MediaAsset).where(
            MediaAsset.user_id == user.id,
            MediaAsset.media_type == "profile_media",
            MediaAsset.deleted_at.is_(None),
            MediaAsset.processing_status != "deleted",
        ).order_by(MediaAsset.sort_order.asc(), MediaAsset.created_at.desc(), MediaAsset.id.desc())
        if after:
            anchor = await _owned_profile_media(session, user.id, after)
            statement = statement.where(or_(
                MediaAsset.sort_order > anchor.sort_order,
                (MediaAsset.sort_order == anchor.sort_order) & or_(
                    MediaAsset.created_at < anchor.created_at,
                    (MediaAsset.created_at == anchor.created_at) & (MediaAsset.id < anchor.id),
                ),
            ))
        result = await session.execute(statement.limit(limit + 1))
        assets = list(result.scalars().all())
        has_more = len(assets) > limit
        assets = assets[:limit]
        items: list[MediaRead] = []
        for asset in assets:
            url = None
            if asset.processing_status == "ready":
                try:
                    url = await self.storage.create_download_url(asset.object_key, self.settings.media_signed_url_ttl_seconds)
                except StorageUnavailable:
                    url = None
            items.append(_asset_read(asset, url))
        return MediaPage(items=items, next_cursor=assets[-1].id if has_more and assets else None)

    async def delete_media(self, session: AsyncSession, user: User, media_id: str) -> None:
        asset = await _owned_profile_media(session, user.id, media_id)
        try:
            await self.storage.delete_object(asset.object_key)
        except StorageUnavailable as exc:
            raise _http_error("MEDIA_STORAGE_UNAVAILABLE", "Media could not be deleted right now.", status.HTTP_503_SERVICE_UNAVAILABLE) from exc
        now = datetime.now(UTC)
        asset.processing_status = "deleted"
        asset.deleted_at = now
        asset.updated_at = now
        await session.commit()

    async def update_order(self, session: AsyncSession, user: User, media_id: str, sort_order: int) -> MediaRead:
        asset = await _owned_profile_media(session, user.id, media_id)
        result = await session.execute(select(MediaAsset).where(
            MediaAsset.user_id == user.id,
            MediaAsset.media_type == "profile_media",
            MediaAsset.deleted_at.is_(None),
            MediaAsset.processing_status.in_(["uploading", "processing", "ready"]),
        ).order_by(MediaAsset.sort_order.asc(), MediaAsset.created_at.asc(), MediaAsset.id.asc()))
        assets = list(result.scalars().all())
        if sort_order >= len(assets):
            raise _http_error("MEDIA_ORDER_INVALID", "Photo order is outside the current profile media range.", status.HTTP_422_UNPROCESSABLE_ENTITY)
        assets.remove(asset)
        assets.insert(sort_order, asset)
        now = datetime.now(UTC)
        for index, item in enumerate(assets):
            item.sort_order = index
            item.updated_at = now
        await session.commit()
        await session.refresh(asset)
        return _asset_read(asset)
