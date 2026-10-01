from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import require_permission
from app.core.dependencies import get_active_travelmate_user, get_db_session
from app.models.user import User
from app.schemas.destination import (
    DestinationCreate,
    DestinationListResponse,
    DestinationRead,
    DestinationUpdate,
)
from app.schemas.location import LocationUpdate, UserLocationRead
from app.services.location_service import LocationService

router = APIRouter(prefix="/destinations", tags=["destinations"])
me_location_router = APIRouter(prefix="/me/location", tags=["location"])
admin_destinations_router = APIRouter(prefix="/admin/destinations", tags=["admin destinations"])

Database = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[User, Depends(get_active_travelmate_user)]


@router.get("", response_model=DestinationListResponse)
async def list_destinations(
    session: Database,
    q: Annotated[str, Query(description="Search destination name, city, region, or aliases")] = "",
    country_code: Annotated[str | None, Query(max_length=3)] = None,
    category: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    # Ensure default seeds are present if table is empty
    items, total = await LocationService.search_destinations(
        session, query=q, country_code=country_code, category=category, limit=limit, offset=offset
    )
    if total == 0 and not q and not country_code and not category:
        seeded = await LocationService.seed_default_destinations(session)
        if seeded > 0:
            items, total = await LocationService.search_destinations(
                session, query=q, country_code=country_code, category=category, limit=limit, offset=offset
            )

    read_items = [
        DestinationRead(
            id=d.id,
            name=d.name,
            slug=d.slug,
            country=d.country,
            country_code=d.country_code,
            region=d.region,
            city=d.city,
            description=d.description,
            latitude=d.latitude,
            longitude=d.longitude,
            timezone=d.timezone,
            category=d.category,
            status=d.status,
            aliases=[a.alias for a in d.aliases],
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in items
    ]
    return DestinationListResponse(items=read_items, total=total, limit=limit, offset=offset)


@router.get("/search", response_model=DestinationListResponse)
async def search_destinations_endpoint(
    session: Database,
    q: Annotated[str, Query(description="Search query")] = "",
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
):
    items, total = await LocationService.search_destinations(
        session, query=q, limit=limit, offset=0
    )
    if total == 0 and not q:
        await LocationService.seed_default_destinations(session)
        items, total = await LocationService.search_destinations(
            session, query=q, limit=limit, offset=0
        )

    read_items = [
        DestinationRead(
            id=d.id,
            name=d.name,
            slug=d.slug,
            country=d.country,
            country_code=d.country_code,
            region=d.region,
            city=d.city,
            description=d.description,
            latitude=d.latitude,
            longitude=d.longitude,
            timezone=d.timezone,
            category=d.category,
            status=d.status,
            aliases=[a.alias for a in d.aliases],
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in items
    ]
    return DestinationListResponse(items=read_items, total=total, limit=limit, offset=0)


@router.get("/nearby")
async def get_nearby_destinations_endpoint(
    session: Database,
    lat: Annotated[float, Query(ge=-90.0, le=90.0)],
    lon: Annotated[float, Query(ge=-180.0, le=180.0)],
    radius_km: Annotated[float, Query(ge=1.0, le=2000.0)] = 100.0,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
):
    nearby = await LocationService.get_nearby_destinations(
        session, latitude=lat, longitude=lon, radius_km=radius_km, limit=limit
    )
    if not nearby:
        await LocationService.seed_default_destinations(session)
        nearby = await LocationService.get_nearby_destinations(
            session, latitude=lat, longitude=lon, radius_km=radius_km, limit=limit
        )

    results = []
    for d, dist in nearby:
        results.append(
            {
                "destination": {
                    "id": d.id,
                    "name": d.name,
                    "slug": d.slug,
                    "country": d.country,
                    "country_code": d.country_code,
                    "region": d.region,
                    "city": d.city,
                    "category": d.category,
                    "latitude": d.latitude,
                    "longitude": d.longitude,
                },
                "distance_km": dist,
            }
        )
    return {"items": results, "total": len(results)}


@router.get("/{id_or_slug}", response_model=DestinationRead)
async def get_destination(session: Database, id_or_slug: str):
    dest = await LocationService.get_destination_by_id(session, id_or_slug)
    if not dest:
        dest = await LocationService.get_destination_by_slug(session, id_or_slug)
    if not dest:
        await LocationService.seed_default_destinations(session)
        dest = await LocationService.get_destination_by_id(session, id_or_slug)
        if not dest:
            dest = await LocationService.get_destination_by_slug(session, id_or_slug)

    if not dest or dest.status != "active":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "DESTINATION_NOT_FOUND", "message": "Destination not found."}},
        )

    return DestinationRead(
        id=dest.id,
        name=dest.name,
        slug=dest.slug,
        country=dest.country,
        country_code=dest.country_code,
        region=dest.region,
        city=dest.city,
        description=dest.description,
        latitude=dest.latitude,
        longitude=dest.longitude,
        timezone=dest.timezone,
        category=dest.category,
        status=dest.status,
        aliases=[a.alias for a in dest.aliases],
        created_at=dest.created_at,
        updated_at=dest.updated_at,
    )


# Me Location Endpoints
@me_location_router.get("", response_model=UserLocationRead | None)
async def get_my_location(current_user: CurrentUser, session: Database):
    loc = await LocationService.get_user_location(session, current_user.id)
    if not loc:
        return None
    return UserLocationRead(
        id=loc.id,
        user_id=loc.user_id,
        latitude=loc.latitude,
        longitude=loc.longitude,
        approx_latitude=loc.approx_latitude,
        approx_longitude=loc.approx_longitude,
        precision=loc.precision,
        sharing_mode=loc.sharing_mode,
        source=loc.source,
        city=loc.city,
        region=loc.region,
        country_code=loc.country_code,
        captured_at=loc.captured_at,
        updated_at=loc.updated_at,
    )


@me_location_router.put("", response_model=UserLocationRead)
async def update_my_location(
    current_user: CurrentUser, update_data: LocationUpdate, session: Database
):
    loc = await LocationService.set_user_location(session, current_user.id, update_data)
    return UserLocationRead(
        id=loc.id,
        user_id=loc.user_id,
        latitude=loc.latitude,
        longitude=loc.longitude,
        approx_latitude=loc.approx_latitude,
        approx_longitude=loc.approx_longitude,
        precision=loc.precision,
        sharing_mode=loc.sharing_mode,
        source=loc.source,
        city=loc.city,
        region=loc.region,
        country_code=loc.country_code,
        captured_at=loc.captured_at,
        updated_at=loc.updated_at,
    )


@me_location_router.delete("")
async def delete_my_location(current_user: CurrentUser, session: Database):
    deleted = await LocationService.delete_user_location(session, current_user.id)
    return {"ok": True, "deleted": deleted}


# Admin Destinations Endpoints
@admin_destinations_router.get("", response_model=DestinationListResponse)
async def admin_list_destinations(
    session: Database,
    _auth: Annotated[dict, Depends(require_permission("travel.read"))],
    q: Annotated[str, Query()] = "",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    items, total = await LocationService.search_destinations(
        session, query=q, limit=limit, offset=offset
    )
    if total == 0 and not q:
        await LocationService.seed_default_destinations(session)
        items, total = await LocationService.search_destinations(
            session, query=q, limit=limit, offset=offset
        )

    read_items = [
        DestinationRead(
            id=d.id,
            name=d.name,
            slug=d.slug,
            country=d.country,
            country_code=d.country_code,
            region=d.region,
            city=d.city,
            description=d.description,
            latitude=d.latitude,
            longitude=d.longitude,
            timezone=d.timezone,
            category=d.category,
            status=d.status,
            aliases=[a.alias for a in d.aliases],
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in items
    ]
    return DestinationListResponse(items=read_items, total=total, limit=limit, offset=offset)


@admin_destinations_router.post("", response_model=DestinationRead, status_code=status.HTTP_201_CREATED)
async def admin_create_destination(
    data: DestinationCreate,
    session: Database,
    _auth: Annotated[dict, Depends(require_permission("travel.manage"))],
):
    existing = await LocationService.get_destination_by_slug(session, data.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "SLUG_ALREADY_EXISTS", "message": f"Destination slug '{data.slug}' already exists."}},
        )
    dest = await LocationService.create_destination(session, data)
    return DestinationRead(
        id=dest.id,
        name=dest.name,
        slug=dest.slug,
        country=dest.country,
        country_code=dest.country_code,
        region=dest.region,
        city=dest.city,
        description=dest.description,
        latitude=dest.latitude,
        longitude=dest.longitude,
        timezone=dest.timezone,
        category=dest.category,
        status=dest.status,
        aliases=[a.alias for a in dest.aliases],
        created_at=dest.created_at,
        updated_at=dest.updated_at,
    )


@admin_destinations_router.get("/{id}", response_model=DestinationRead)
async def admin_get_destination(
    id: str,
    session: Database,
    _auth: Annotated[dict, Depends(require_permission("travel.read"))],
):
    dest = await LocationService.get_destination_by_id(session, id)
    if not dest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "DESTINATION_NOT_FOUND", "message": "Destination not found."}},
        )
    return DestinationRead(
        id=dest.id,
        name=dest.name,
        slug=dest.slug,
        country=dest.country,
        country_code=dest.country_code,
        region=dest.region,
        city=dest.city,
        description=dest.description,
        latitude=dest.latitude,
        longitude=dest.longitude,
        timezone=dest.timezone,
        category=dest.category,
        status=dest.status,
        aliases=[a.alias for a in dest.aliases],
        created_at=dest.created_at,
        updated_at=dest.updated_at,
    )


@admin_destinations_router.patch("/{id}", response_model=DestinationRead)
async def admin_update_destination(
    id: str,
    data: DestinationUpdate,
    session: Database,
    _auth: Annotated[dict, Depends(require_permission("travel.manage"))],
):
    dest = await LocationService.update_destination(session, id, data)
    if not dest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "DESTINATION_NOT_FOUND", "message": "Destination not found."}},
        )
    return DestinationRead(
        id=dest.id,
        name=dest.name,
        slug=dest.slug,
        country=dest.country,
        country_code=dest.country_code,
        region=dest.region,
        city=dest.city,
        description=dest.description,
        latitude=dest.latitude,
        longitude=dest.longitude,
        timezone=dest.timezone,
        category=dest.category,
        status=dest.status,
        aliases=[a.alias for a in dest.aliases],
        created_at=dest.created_at,
        updated_at=dest.updated_at,
    )
