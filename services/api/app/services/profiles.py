from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.profile_completion import calculate_profile_completion
from app.models.media import MediaAsset
from app.models.profile import UserProfile
from app.models.user import User
from app.schemas.profile import OwnProfileRead, ProfileCreate, ProfileWrite, PublicProfileRead, calculate_age
from app.services.media_storage import StorageUnavailable
from app.services.r2_storage import R2Storage


def _now() -> str:
    return datetime.now(UTC).isoformat()


def visibility_for_response(value: str) -> str:
    return "hidden" if value == "private" else value


def _profile_read(profile: UserProfile) -> OwnProfileRead:
    birth_date = date.fromisoformat(profile.date_of_birth) if profile.date_of_birth else None
    return OwnProfileRead(
        profile_id=profile.id,
        user_id=profile.user_id,
        display_name=profile.display_name,
        age=calculate_age(birth_date) if birth_date else None,
        bio=profile.bio,
        gender_identity=profile.gender_identity,
        profile_visibility=visibility_for_response(profile.profile_visibility),
        discovery_visibility=profile.discovery_visibility,
        profile_status=profile.profile_status,
        completion_percentage=profile.profile_completion,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


async def find_profile(session: AsyncSession, user_id: str) -> UserProfile | None:
    result = await session.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    return result.scalar_one_or_none()


async def ensure_profile_draft(session: AsyncSession, user: User) -> UserProfile:
    profile = await find_profile(session, user.id)
    if profile is None:
        now = _now()
        profile = UserProfile(
            id=str(uuid4()),
            user_id=user.id,
            display_name=None,
            bio=None,
            date_of_birth=None,
            gender_identity=None,
            profile_visibility="hidden",
            discovery_visibility=False,
            profile_status="draft",
            profile_completion=0,
            created_at=now,
            updated_at=now,
        )
        session.add(profile)
        await session.flush()
    return profile


async def save_profile(
    session: AsyncSession,
    user: User,
    payload: ProfileWrite,
    *,
    require_create_fields: bool = False,
) -> OwnProfileRead:
    profile = await find_profile(session, user.id)
    is_new = profile is None
    if is_new:
        profile = await ensure_profile_draft(session, user)

    fields_set = payload.model_fields_set
    if (is_new or require_create_fields) and (not payload.display_name or payload.date_of_birth is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[{"type": "value_error", "loc": ["body"], "msg": "display_name and date_of_birth are required to create a profile"}],
        )

    if "display_name" in fields_set and payload.display_name is not None:
        profile.display_name = payload.display_name.strip()
    if "date_of_birth" in fields_set and payload.date_of_birth is not None:
        profile.date_of_birth = payload.date_of_birth.isoformat()
    if "bio" in fields_set:
        profile.bio = payload.bio.strip() if payload.bio else None
    if "gender_identity" in fields_set:
        profile.gender_identity = payload.gender_identity.strip() if payload.gender_identity else None
    if "profile_visibility" in fields_set and payload.profile_visibility is not None:
        profile.profile_visibility = payload.profile_visibility
    if "discovery_visibility" in fields_set and payload.discovery_visibility is not None:
        profile.discovery_visibility = payload.discovery_visibility

    profile.updated_at = _now()
    await calculate_profile_completion(session, profile)
    await session.commit()
    await session.refresh(profile)
    return _profile_read(profile)


async def read_own_profile(session: AsyncSession, user: User) -> OwnProfileRead:
    profile = await ensure_profile_draft(session, user)
    await calculate_profile_completion(session, profile)
    await session.commit()
    await session.refresh(profile)
    return _profile_read(profile)


async def read_public_profile(session: AsyncSession, profile_id: str) -> PublicProfileRead:
    result = await session.execute(select(UserProfile).where(UserProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if (
        profile is None
        or not profile.display_name
        or not profile.date_of_birth
        or profile.profile_visibility not in {"public", "discoverable"}
        or not profile.discovery_visibility
    ):
        raise HTTPException(status_code=404, detail={"error": {"code": "PROFILE_NOT_FOUND", "message": "Profile not found."}})

    media_result = await session.execute(
        select(MediaAsset).where(
            MediaAsset.user_id == profile.user_id,
            MediaAsset.media_type == "profile_media",
            MediaAsset.processing_status == "ready",
            MediaAsset.moderation_status == "approved",
            MediaAsset.visibility == "public",
            MediaAsset.deleted_at.is_(None),
        ).order_by(MediaAsset.sort_order.asc(), MediaAsset.created_at.asc()).limit(6)
    )
    media_assets = list(media_result.scalars().all())
    media_urls: list[str] = []
    if media_assets:
        try:
            storage = R2Storage()
            for asset in media_assets:
                media_urls.append(await storage.create_download_url(asset.object_key, 300))
        except StorageUnavailable as exc:
            raise HTTPException(
                status_code=503,
                detail={"error": {"code": "MEDIA_STORAGE_UNAVAILABLE", "message": "Public profile media is temporarily unavailable."}},
            ) from exc

    return PublicProfileRead(
        display_name=profile.display_name,
        age=calculate_age(date.fromisoformat(profile.date_of_birth)),
        bio=profile.bio,
        gender_identity=profile.gender_identity,
        interests=[],
        profile_media=media_urls,
    )


def create_profile_write(payload: ProfileCreate) -> ProfileWrite:
    return ProfileWrite(**payload.model_dump())
