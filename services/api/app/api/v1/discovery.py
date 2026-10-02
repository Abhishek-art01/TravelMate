from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_active_travelmate_user, get_db_session
from app.models.user import User
from app.schemas.discovery import (
    DiscoveryCandidateRead,
    DiscoveryInteractionCreate,
    DiscoveryInteractionRead,
    DiscoveryListResponse,
)
from app.services.discovery_service import DiscoveryService

router = APIRouter(prefix="/discovery", tags=["discovery"])

Database = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[User, Depends(get_active_travelmate_user)]


@router.get("", response_model=DiscoveryListResponse)
async def get_discovery_candidates(
    current_user: CurrentUser,
    session: Database,
    destination_id: Annotated[str | None, Query(description="Destination ID filter")] = None,
    country_code: Annotated[str | None, Query(description="2-letter ISO country code")] = None,
    start_date: Annotated[date | None, Query(description="Start travel date")] = None,
    end_date: Annotated[date | None, Query(description="End travel date")] = None,
    intent: Annotated[str | None, Query(description="Travel or match intent filter")] = None,
    interests: Annotated[list[str] | None, Query(description="List of interest codes")] = None,
    languages: Annotated[list[str] | None, Query(description="List of language codes")] = None,
    gender: Annotated[str | None, Query(description="Gender identity filter")] = None,
    min_age: Annotated[int | None, Query(ge=18, le=100, description="Minimum age filter")] = None,
    max_age: Annotated[int | None, Query(ge=18, le=100, description="Maximum age filter")] = None,
    cursor: Annotated[str | None, Query(description="Opaque base64 cursor from previous page")] = None,
    limit: Annotated[int, Query(ge=1, le=50, description="Page limit (max 50)")] = 20,
) -> DiscoveryListResponse:
    return await DiscoveryService.get_candidates(
        session,
        viewer_id=current_user.id,
        destination_id=destination_id,
        country_code=country_code,
        start_date=start_date,
        end_date=end_date,
        intent=intent,
        interests=interests,
        languages=languages,
        gender=gender,
        min_age=min_age,
        max_age=max_age,
        cursor=cursor,
        limit=limit,
    )


@router.get("/{user_id}", response_model=DiscoveryCandidateRead)
async def get_candidate_detail(
    user_id: str,
    current_user: CurrentUser,
    session: Database,
) -> DiscoveryCandidateRead:
    return await DiscoveryService.get_candidate_detail(
        session,
        viewer_id=current_user.id,
        candidate_id=user_id,
    )


@router.post("/{user_id}/interaction", response_model=DiscoveryInteractionRead, status_code=status.HTTP_201_CREATED)
async def record_candidate_interaction(
    user_id: str,
    payload: DiscoveryInteractionCreate,
    current_user: CurrentUser,
    session: Database,
) -> DiscoveryInteractionRead:
    interaction = await DiscoveryService.record_interaction(
        session,
        user_id=current_user.id,
        target_user_id=user_id,
        interaction_type=payload.interaction_type,
    )
    await session.commit()
    return interaction
