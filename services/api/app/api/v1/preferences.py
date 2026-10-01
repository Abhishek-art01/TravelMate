from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_active_travelmate_user, get_db_session
from app.models.user import User
from app.schemas.preferences import PreferencesWrite
from app.services.preferences import read_preferences, save_preferences

router = APIRouter(tags=["preferences"])
CurrentUser = Annotated[User, Depends(get_active_travelmate_user)]
Database = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/me/preferences")
@router.get("/preferences/", include_in_schema=False)
async def get_my_preferences(current_user: CurrentUser, session: Database):
    return await read_preferences(session, current_user.id)


@router.put("/me/preferences")
@router.patch("/preferences/", include_in_schema=False)
async def update_my_preferences(payload: PreferencesWrite, current_user: CurrentUser, session: Database):
    return await save_preferences(session, current_user.id, payload)
