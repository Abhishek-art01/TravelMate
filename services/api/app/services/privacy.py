from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.privacy import UserPrivacySettings
from app.models.profile import UserProfile
from app.models.user import User
from app.schemas.privacy import PrivacyRead, PrivacyWrite
from app.services.profiles import ensure_profile_draft


def _serialize(profile: UserProfile, settings: UserPrivacySettings) -> PrivacyRead:
    visibility = "hidden" if profile.profile_visibility == "private" else profile.profile_visibility
    return PrivacyRead(
        profile_visibility=visibility,
        discovery_visibility=profile.discovery_visibility,
        location_precision=settings.location_precision,
        allow_exact_location_sharing=settings.allow_exact_location_sharing,
        personalization_enabled=settings.personalization_enabled,
        communications_enabled=settings.communications_enabled,
    )


async def read_privacy(session: AsyncSession, user: User) -> PrivacyRead:
    profile = await ensure_profile_draft(session, user)
    settings_result = await session.execute(
        select(UserPrivacySettings).where(UserPrivacySettings.user_id == user.id)
    )
    settings = settings_result.scalar_one_or_none()
    if settings is None:
        settings = UserPrivacySettings(id=str(uuid4()), user_id=user.id)
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
    return _serialize(profile, settings)


async def save_privacy(session: AsyncSession, user: User, payload: PrivacyWrite) -> PrivacyRead:
    profile = await ensure_profile_draft(session, user)
    settings_result = await session.execute(
        select(UserPrivacySettings).where(UserPrivacySettings.user_id == user.id)
    )
    settings = settings_result.scalar_one_or_none()
    if settings is None:
        settings = UserPrivacySettings(id=str(uuid4()), user_id=user.id)
        session.add(settings)

    fields = payload.model_fields_set
    if "profile_visibility" in fields and payload.profile_visibility is not None:
        profile.profile_visibility = payload.profile_visibility
        if payload.profile_visibility == "hidden":
            profile.discovery_visibility = False
    if "discovery_visibility" in fields and payload.discovery_visibility is not None:
        profile.discovery_visibility = payload.discovery_visibility and profile.profile_visibility not in {"hidden", "limited"}
    if "location_precision" in fields and payload.location_precision is not None:
        settings.location_precision = payload.location_precision
    if "allow_exact_location_sharing" in fields and payload.allow_exact_location_sharing is not None:
        settings.allow_exact_location_sharing = payload.allow_exact_location_sharing
    if "personalization_enabled" in fields and payload.personalization_enabled is not None:
        settings.personalization_enabled = payload.personalization_enabled
    if "communications_enabled" in fields and payload.communications_enabled is not None:
        settings.communications_enabled = payload.communications_enabled

    now = datetime.now(UTC)
    profile.updated_at = now.isoformat()
    settings.updated_at = now
    await session.commit()
    await session.refresh(profile)
    await session.refresh(settings)
    return _serialize(profile, settings)
