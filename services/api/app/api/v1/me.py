from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_active_travelmate_user, get_db_session
from app.core.profile_completion import calculate_profile_completion
from app.core.security import get_current_user
from app.models.user import User
from app.services.profiles import ensure_profile_draft

router = APIRouter(tags=["current user"])
CurrentUser = Annotated[User, Depends(get_active_travelmate_user)]
VerifiedIdentity = Annotated[dict, Depends(get_current_user)]
Database = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/me")
async def read_me(current_user: CurrentUser, verified_identity: VerifiedIdentity, session: Database):
    profile = await ensure_profile_draft(session, current_user)
    await calculate_profile_completion(session, profile)
    await session.commit()
    return {
        "user_id": current_user.id,
        "email": verified_identity.get("email"),
        "provider": verified_identity.get("provider", "supabase"),
        "account_status": current_user.account_status,
        "profile_status": profile.profile_status,
        "completion_percentage": profile.profile_completion,
    }
