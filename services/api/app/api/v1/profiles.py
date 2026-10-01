from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_active_travelmate_user, get_db_session
from app.core.security import get_current_user_optional
from app.models.user import User
from app.schemas.profile import ProfileCreate, ProfileWrite
from app.services.profiles import create_profile_write, read_own_profile, read_public_profile, save_profile

router = APIRouter(tags=["profiles"])
CurrentUser = Annotated[User, Depends(get_active_travelmate_user)]
Database = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/me/profile")
async def get_my_profile(current_user: CurrentUser, session: Database):
    return await read_own_profile(session, current_user)


@router.put("/me/profile")
async def update_my_profile(payload: ProfileWrite, current_user: CurrentUser, session: Database):
    return await save_profile(session, current_user, payload)


@router.patch("/me/profile")
async def patch_my_profile(payload: ProfileWrite, current_user: CurrentUser, session: Database):
    return await save_profile(session, current_user, payload)


@router.post("/profiles", status_code=status.HTTP_200_OK)
async def create_profile(
    payload: ProfileCreate,
    identity: Annotated[dict | None, Depends(get_current_user_optional)],
    session: Database,
):
    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "AUTHENTICATION_REQUIRED", "message": "Authentication credentials were not provided."}},
        )
    from app.core.identity import resolve_travelmate_user

    current_user = await resolve_travelmate_user(session, identity)
    return await save_profile(session, current_user, create_profile_write(payload), require_create_fields=True)


@router.get("/profiles/{profile_id}/public")
async def get_public_profile(profile_id: str, session: Database):
    return await read_public_profile(session, profile_id)
