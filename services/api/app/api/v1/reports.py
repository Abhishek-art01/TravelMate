from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import require_permission
from app.core.dependencies import get_active_travelmate_user, get_db_session
from app.models.user import User
from app.schemas.discovery import (
    AdminReportListResponse,
    AdminReportRead,
    AdminReportUpdate,
    UserReportCreate,
    UserReportRead,
)
from app.services.discovery_service import DiscoveryService

router = APIRouter(prefix="/reports", tags=["user reports"])
admin_reports_router = APIRouter(prefix="/admin/reports", tags=["admin reports"])

Database = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[User, Depends(get_active_travelmate_user)]


@router.post("", response_model=UserReportRead, status_code=status.HTTP_201_CREATED)
async def submit_user_report(
    payload: UserReportCreate,
    current_user: CurrentUser,
    session: Database,
) -> UserReportRead:
    report = await DiscoveryService.create_report(
        session,
        reporter_id=current_user.id,
        reported_id=payload.reported_id,
        reason=payload.reason,
        details=payload.details,
    )
    await session.commit()
    return report


@admin_reports_router.get(
    "",
    response_model=AdminReportListResponse,
    dependencies=[Depends(require_permission("moderation.read"))],
)
async def list_admin_reports(
    session: Database,
    status_filter: Annotated[str | None, Query(alias="status", description="Filter by report status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AdminReportListResponse:
    return await DiscoveryService.list_admin_reports(
        session,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )


@admin_reports_router.patch(
    "/{report_id}",
    response_model=AdminReportRead,
)
async def update_admin_report(
    report_id: str,
    payload: AdminReportUpdate,
    current_user: Annotated[dict, Depends(require_permission("moderation.action"))],
    session: Database,
) -> AdminReportRead:
    admin_id = current_user.get("sub", "admin")
    report = await DiscoveryService.update_admin_report(
        session,
        report_id=report_id,
        reviewed_by_id=admin_id,
        update_data=payload,
    )
    await session.commit()
    return report
