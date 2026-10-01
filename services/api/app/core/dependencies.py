from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_async_session
from app.models.user import User


def get_request_id(request: Request) -> str:
    return request.headers.get("X-Request-ID", "unknown-request")


get_db_session = get_async_session


async def get_active_travelmate_user(
    current_user: Annotated[dict, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    from app.core.identity import resolve_travelmate_user

    user = await resolve_travelmate_user(session, current_user)
    account_status = user.account_status.lower()
    if account_status != "active" or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "ACCOUNT_UNAVAILABLE", "message": "This account cannot access TravelMate."}},
        )
    return user
