from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_active_travelmate_user, get_db_session
from app.models.user import User
from app.schemas.discovery import UserBlockCreate, UserBlockListResponse, UserBlockRead
from app.services.discovery_service import DiscoveryService

router = APIRouter(prefix="/me/blocks", tags=["user blocks"])

Database = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[User, Depends(get_active_travelmate_user)]


@router.get("", response_model=UserBlockListResponse)
async def list_my_blocks(
    current_user: CurrentUser,
    session: Database,
) -> UserBlockListResponse:
    return await DiscoveryService.list_blocks(session, blocker_id=current_user.id)


@router.post("/{user_id}", response_model=UserBlockRead, status_code=status.HTTP_201_CREATED)
async def block_user(
    user_id: str,
    payload: UserBlockCreate,
    current_user: CurrentUser,
    session: Database,
) -> UserBlockRead:
    block = await DiscoveryService.block_user(
        session,
        blocker_id=current_user.id,
        blocked_id=user_id,
        reason=payload.reason,
    )
    await session.commit()
    return block


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unblock_user(
    user_id: str,
    current_user: CurrentUser,
    session: Database,
) -> Response:
    await DiscoveryService.unblock_user(
        session,
        blocker_id=current_user.id,
        blocked_id=user_id,
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
