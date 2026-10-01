from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_active_travelmate_user, get_db_session
from app.core.media_dependencies import get_profile_media_service
from app.models.user import User
from app.schemas.media import MediaOrderUpdate, MediaPage, MediaRead, ProfileUploadCreate, ProfileUploadCreated
from app.services.media import ProfileMediaService

router = APIRouter(prefix="/media", tags=["profile media"])
CurrentUser = Annotated[User, Depends(get_active_travelmate_user)]
Database = Annotated[AsyncSession, Depends(get_db_session)]
MediaService = Annotated[ProfileMediaService, Depends(get_profile_media_service)]


@router.post("/uploads", response_model=ProfileUploadCreated)
async def create_profile_upload(payload: ProfileUploadCreate, current_user: CurrentUser, session: Database, media: MediaService):
    return await media.create_upload(session, current_user, payload)


@router.post("/uploads/{media_id}/complete", response_model=MediaRead)
async def complete_profile_upload(media_id: str, current_user: CurrentUser, session: Database, media: MediaService):
    return await media.complete_upload(session, current_user, media_id)


@router.get("", response_model=MediaPage)
async def list_profile_media(
    current_user: CurrentUser,
    session: Database,
    media: MediaService,
    limit: int = Query(default=24, ge=1, le=50),
    after: str | None = None,
):
    return await media.list_media(session, current_user, limit=limit, after=after)


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile_media(media_id: str, current_user: CurrentUser, session: Database, media: MediaService):
    await media.delete_media(session, current_user, media_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{media_id}/order", response_model=MediaRead)
async def update_profile_media_order(
    media_id: str,
    payload: MediaOrderUpdate,
    current_user: CurrentUser,
    session: Database,
    media: MediaService,
):
    return await media.update_order(session, current_user, media_id, payload.sort_order)
