from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import require_permission
from app.core.dependencies import get_active_travelmate_user, get_db_session
from app.core.security import get_current_user_optional
from app.models.user import User
from app.schemas.trip import (
    AdminTripListResponse,
    AdminTripRead,
    PublicTripListResponse,
    PublicTripRead,
    TripCreate,
    TripListResponse,
    TripRead,
    TripUpdate,
)
from app.services.trip_service import TripService

router = APIRouter(prefix="/trips", tags=["public trips"])
me_trips_router = APIRouter(prefix="/me/trips", tags=["my trips"])
admin_trips_router = APIRouter(prefix="/admin/trips", tags=["admin trips"])

Database = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[User, Depends(get_active_travelmate_user)]
OptionalAuth = Annotated[dict | None, Depends(get_current_user_optional)]


# User Own Trips (/api/v1/me/trips)
@me_trips_router.get("", response_model=TripListResponse)
async def list_my_trips(
    current_user: CurrentUser,
    session: Database,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    items, total = await TripService.list_user_trips(
        session, user_id=current_user.id, limit=limit, offset=offset
    )
    return TripListResponse(items=items, total=total, limit=limit, offset=offset)


@me_trips_router.post("", response_model=TripRead, status_code=status.HTTP_201_CREATED)
async def create_my_trip(
    data: TripCreate,
    current_user: CurrentUser,
    session: Database,
):
    return await TripService.create_trip(session, user_id=current_user.id, data=data)


@me_trips_router.get("/{id}", response_model=TripRead)
async def get_my_trip(
    id: str,
    current_user: CurrentUser,
    session: Database,
):
    trip = await TripService.get_trip_by_id(session, id)
    if not trip or trip.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TRIP_NOT_FOUND", "message": "Trip not found."}},
        )
    return TripService._map_trip_read(trip)


@me_trips_router.patch("/{id}", response_model=TripRead)
async def update_my_trip(
    id: str,
    data: TripUpdate,
    current_user: CurrentUser,
    session: Database,
):
    return await TripService.update_trip(session, trip_id=id, user_id=current_user.id, data=data)


@me_trips_router.delete("/{id}")
async def delete_my_trip(
    id: str,
    current_user: CurrentUser,
    session: Database,
):
    deleted = await TripService.delete_trip(session, trip_id=id, user_id=current_user.id)
    return {"ok": True, "deleted": deleted}


# Public / Discovery Trips (/api/v1/trips)
@router.get("", response_model=PublicTripListResponse)
async def discover_trips(
    session: Database,
    destination_id: Annotated[str | None, Query()] = None,
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    companion_preference: Annotated[str | None, Query()] = None,
    intent: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    items, total = await TripService.list_discoverable_trips(
        session,
        destination_id=destination_id,
        start_date=start_date,
        end_date=end_date,
        companion_preference=companion_preference,
        intent=intent,
        limit=limit,
        offset=offset,
    )
    return PublicTripListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{id}", response_model=PublicTripRead)
async def get_public_trip(
    id: str,
    session: Database,
    auth: OptionalAuth = None,
):
    viewer_id = auth.get("user_id") if auth else None
    return await TripService.get_public_trip(session, trip_id=id, viewer_id=viewer_id)


# Admin Trips (/api/v1/admin/trips)
@admin_trips_router.get("", response_model=AdminTripListResponse)
async def admin_list_trips(
    session: Database,
    _auth: Annotated[dict, Depends(require_permission("travel.read"))],
    q: Annotated[str, Query()] = "",
    status: Annotated[str | None, Query()] = None,
    visibility: Annotated[str | None, Query()] = None,
    destination_id: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    items, total = await TripService.list_admin_trips(
        session,
        query=q,
        status_filter=status,
        visibility_filter=visibility,
        destination_id=destination_id,
        limit=limit,
        offset=offset,
    )
    return AdminTripListResponse(items=items, total=total, limit=limit, offset=offset)


@admin_trips_router.get("/{id}", response_model=AdminTripRead)
async def admin_get_trip(
    id: str,
    session: Database,
    _auth: Annotated[dict, Depends(require_permission("travel.read"))],
):
    trip = await TripService.get_trip_by_id(session, id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TRIP_NOT_FOUND", "message": "Trip not found."}},
        )

    from app.schemas.destination import DestinationSummary

    dest_summary = DestinationSummary(
        id=trip.destination.id,
        name=trip.destination.name,
        slug=trip.destination.slug,
        country=trip.destination.country,
        country_code=trip.destination.country_code,
        region=trip.destination.region,
        city=trip.destination.city,
        category=trip.destination.category,
        latitude=trip.destination.latitude,
        longitude=trip.destination.longitude,
    )
    return AdminTripRead(
        id=trip.id,
        user_id=trip.user_id,
        user_email=trip.user.email if trip.user else None,
        destination_id=trip.destination_id,
        destination=dest_summary,
        title=trip.title,
        description=trip.description,
        start_date=trip.start_date,
        end_date=trip.end_date,
        status=trip.status,
        visibility=trip.visibility,
        companion_preference=trip.companion_preference,
        party_size=trip.party_size,
        intents=[i.intent for i in trip.intents],
        created_at=trip.created_at,
        updated_at=trip.updated_at,
    )
