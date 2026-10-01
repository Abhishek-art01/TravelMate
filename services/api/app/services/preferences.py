from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.profile_completion import calculate_profile_completion
from app.models.interest import Interest, UserInterest
from app.models.preferences import UserPreferenceOption, UserPreferences
from app.models.profile import UserProfile
from app.schemas.preferences import PreferencesRead, PreferencesWrite

PREFERENCE_VALUES = {
    "dating_intention": {"dating_romantic", "serious_relationship", "casual_dating"},
    "dating_preference": {"women", "men", "non_binary", "all_genders", "not_dating"},
    "discovery_preference": {"shared_interests", "similar_travel_intentions", "same_destination"},
    "travel_intention": {"travel_companion", "friends_social", "local_guide", "activity_partner"},
    "language": {"hi", "bn", "te", "mr", "ta", "gu", "kn", "ml", "pa", "or", "as", "ur", "en"},
}


def _bad_value(field_name: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"error": {"code": "INVALID_PREFERENCE", "message": f"One or more {field_name} values are not supported."}},
    )


async def read_preferences(session: AsyncSession, user_id: str) -> PreferencesRead:
    preference_result = await session.execute(select(UserPreferences).where(UserPreferences.user_id == user_id))
    settings = preference_result.scalar_one_or_none()
    option_result = await session.execute(
        select(UserPreferenceOption).where(UserPreferenceOption.user_id == user_id)
    )
    grouped: dict[str, list[str]] = {category: [] for category in PREFERENCE_VALUES}
    for row in option_result.scalars():
        grouped.setdefault(row.category, []).append(row.value)
    interest_result = await session.execute(
        select(Interest.code)
        .join(UserInterest, UserInterest.interest_id == Interest.id)
        .where(UserInterest.user_id == user_id, Interest.active.is_(True))
        .order_by(Interest.code)
    )
    return PreferencesRead(
        dating_intentions=sorted(grouped["dating_intention"]),
        dating_preferences=sorted(grouped["dating_preference"]),
        discovery_preferences=sorted(grouped["discovery_preference"]),
        travel_intentions=sorted(grouped["travel_intention"]),
        languages=sorted(grouped["language"]),
        interests=list(interest_result.scalars().all()),
        minimum_age=settings.minimum_age if settings else 18,
        maximum_age=settings.maximum_age if settings else None,
    )


async def save_preferences(session: AsyncSession, user_id: str, payload: PreferencesWrite) -> PreferencesRead:
    supplied = {
        "dating_intention": payload.dating_intentions,
        "dating_preference": payload.dating_preferences,
        "discovery_preference": payload.discovery_preferences,
        "travel_intention": payload.travel_intentions,
        "language": payload.languages,
    }
    for category, values in supplied.items():
        if not set(values).issubset(PREFERENCE_VALUES[category]):
            raise _bad_value(category)

    if payload.interests:
        catalog_result = await session.execute(
            select(Interest.code).where(Interest.active.is_(True), Interest.code.in_(payload.interests))
        )
        available = set(catalog_result.scalars().all())
        if available != set(payload.interests):
            raise _bad_value("interests")

    preference_result = await session.execute(select(UserPreferences).where(UserPreferences.user_id == user_id))
    settings = preference_result.scalar_one_or_none()
    now = datetime.now(UTC)
    if settings is None:
        settings = UserPreferences(id=str(uuid4()), user_id=user_id, minimum_age=payload.minimum_age, maximum_age=payload.maximum_age)
        session.add(settings)
    else:
        settings.minimum_age = payload.minimum_age
        settings.maximum_age = payload.maximum_age
        settings.updated_at = now

    await session.execute(delete(UserPreferenceOption).where(UserPreferenceOption.user_id == user_id))
    for category, values in supplied.items():
        for value in values:
            session.add(UserPreferenceOption(id=str(uuid4()), user_id=user_id, category=category, value=value))

    await session.execute(delete(UserInterest).where(UserInterest.user_id == user_id))
    if payload.interests:
        ids_result = await session.execute(select(Interest.id).where(Interest.code.in_(payload.interests)))
        for interest_id in ids_result.scalars():
            session.add(UserInterest(user_id=user_id, interest_id=interest_id))

    profile_result = await session.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = profile_result.scalar_one_or_none()
    if profile is not None:
        profile.updated_at = now.isoformat()
        await calculate_profile_completion(session, profile)

    await session.commit()
    return await read_preferences(session, user_id)
