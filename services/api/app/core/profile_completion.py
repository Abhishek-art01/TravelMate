from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interest import UserInterest
from app.models.media import MediaAsset
from app.models.preferences import UserPreferenceOption
from app.models.profile import UserProfile


async def calculate_profile_completion(session: AsyncSession, profile: UserProfile) -> int:
    score = 0
    if profile.display_name and profile.display_name.strip():
        score += 20
    if profile.date_of_birth:
        score += 20
    if profile.bio and profile.bio.strip():
        score += 10
    if profile.gender_identity and profile.gender_identity.strip():
        score += 5

    option_rows = await session.execute(
        select(UserPreferenceOption.category).where(UserPreferenceOption.user_id == profile.user_id)
    )
    categories = set(option_rows.scalars().all())
    if categories.intersection({"dating_intention", "travel_intention", "dating_preference", "discovery_preference"}):
        score += 15
    if "language" in categories:
        score += 10

    interest_count = await session.scalar(
        select(func.count()).select_from(UserInterest).where(UserInterest.user_id == profile.user_id)
    )
    if interest_count:
        score += 10

    approved_media_count = await session.scalar(
        select(func.count()).select_from(MediaAsset).where(
            MediaAsset.user_id == profile.user_id,
            MediaAsset.media_type == "profile_media",
            MediaAsset.processing_status == "ready",
            MediaAsset.moderation_status == "approved",
            MediaAsset.deleted_at.is_(None),
        )
    )
    if approved_media_count:
        score += 10

    profile.profile_completion = min(score, 100)
    profile.profile_status = "complete" if score >= 80 else "draft"
    return profile.profile_completion
