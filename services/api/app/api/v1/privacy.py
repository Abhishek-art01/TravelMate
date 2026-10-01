from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_active_travelmate_user, get_db_session
from app.models.user import User
from app.schemas.privacy import PrivacyWrite
from app.services.privacy import read_privacy, save_privacy

router = APIRouter(tags=["privacy"])
CurrentUser = Annotated[User, Depends(get_active_travelmate_user)]
Database = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/me/privacy")
async def get_my_privacy(current_user: CurrentUser, session: Database):
    return await read_privacy(session, current_user)


@router.put("/me/privacy")
async def update_my_privacy(payload: PrivacyWrite, current_user: CurrentUser, session: Database):
    return await save_privacy(session, current_user, payload)
