from __future__ import annotations

import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profile import UserProfile
from app.models.trip import Trip, TripIntent
from app.models.verification import VerificationRecord
from app.schemas.destination import DestinationSummary
from app.schemas.trip import (
    AdminTripRead,
    PublicTripRead,
    TripCreate,
    TripRead,
    TripUpdate,
)
from app.services.location_service import LocationService
from app.services.travel_dates import validate_date_range
from app.services.trip_state import can_transition_trip


class TripService:
    @staticmethod
    def _map_trip_read(trip: Trip) -> TripRead:
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
        return TripRead(
            id=trip.id,
            user_id=trip.user_id,
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

    @staticmethod
    def _map_public_trip_read(trip: Trip, display_name: str | None = None, is_verified: bool = False) -> PublicTripRead:
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
        return PublicTripRead(
            id=trip.id,
            destination=dest_summary,
            title=trip.title,
            description=trip.description,
            start_date=trip.start_date,
            end_date=trip.end_date,
            companion_preference=trip.companion_preference,
            party_size=trip.party_size,
            intents=[i.intent for i in trip.intents],
            creator_display_name=display_name,
            creator_avatar_url=None,
            creator_verified=is_verified,
            created_at=trip.created_at,
        )

    @staticmethod
    async def get_trip_by_id(db: AsyncSession, trip_id: str) -> Trip | None:
        stmt = (
            select(Trip)
            .options(
                selectinload(Trip.destination),
                selectinload(Trip.intents),
                selectinload(Trip.user),
            )
            .where(Trip.id == trip_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_trip(db: AsyncSession, user_id: str, data: TripCreate) -> TripRead:
        dest = await LocationService.get_destination_by_id(db, data.destination_id)
        if not dest or dest.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "INVALID_DESTINATION", "message": "Destination not found or inactive."}},
            )

        validate_date_range(data.start_date, data.end_date)

        trip_id = str(uuid.uuid4())
        trip = Trip(
            id=trip_id,
            user_id=user_id,
            destination_id=data.destination_id,
            title=data.title.strip(),
            description=data.description.strip() if data.description else None,
            start_date=data.start_date,
            end_date=data.end_date,
            status="planned",
            visibility=data.visibility,
            companion_preference=data.companion_preference,
            party_size=data.party_size,
        )
        db.add(trip)
        await db.flush()

        for intent_str in set(data.intents):
            clean_intent = intent_str.strip().lower()
            if clean_intent:
                intent_obj = TripIntent(
                    id=str(uuid.uuid4()),
                    trip_id=trip_id,
                    intent=clean_intent,
                )
                db.add(intent_obj)

        await db.commit()
        created = await TripService.get_trip_by_id(db, trip_id)
        return TripService._map_trip_read(created)  # type: ignore[arg-type]

    @staticmethod
    async def list_user_trips(
        db: AsyncSession, user_id: str, limit: int = 20, offset: int = 0
    ) -> tuple[list[TripRead], int]:
        count_stmt = select(func.count(Trip.id)).where(Trip.user_id == user_id)
        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = (
            select(Trip)
            .options(selectinload(Trip.destination), selectinload(Trip.intents))
            .where(Trip.user_id == user_id)
            .order_by(Trip.start_date.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        trips = result.scalars().all()
        return [TripService._map_trip_read(t) for t in trips], total

    @staticmethod
    async def update_trip(
        db: AsyncSession, trip_id: str, user_id: str, data: TripUpdate
    ) -> TripRead:
        trip = await TripService.get_trip_by_id(db, trip_id)
        if not trip or trip.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "TRIP_NOT_FOUND", "message": "Trip not found."}},
            )

        if data.destination_id and data.destination_id != trip.destination_id:
            dest = await LocationService.get_destination_by_id(db, data.destination_id)
            if not dest or dest.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": {"code": "INVALID_DESTINATION", "message": "Destination not found or inactive."}},
                )
            trip.destination_id = data.destination_id

        if data.status and data.status != trip.status:
            if not can_transition_trip(trip.status, data.status):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": {
                            "code": "INVALID_STATUS_TRANSITION",
                            "message": f"Cannot transition trip from '{trip.status}' to '{data.status}'.",
                        }
                    },
                )
            trip.status = data.status

        new_start = data.start_date or trip.start_date
        new_end = data.end_date or trip.end_date
        validate_date_range(new_start, new_end)

        if data.title is not None:
            trip.title = data.title.strip()
        if data.description is not None:
            trip.description = data.description.strip() or None
        if data.start_date is not None:
            trip.start_date = data.start_date
        if data.end_date is not None:
            trip.end_date = data.end_date
        if data.visibility is not None:
            trip.visibility = data.visibility
        if data.companion_preference is not None:
            trip.companion_preference = data.companion_preference
        if data.party_size is not None:
            trip.party_size = data.party_size

        if data.intents is not None:
            for old_intent in list(trip.intents):
                await db.delete(old_intent)
            await db.flush()
            for intent_str in set(data.intents):
                clean_intent = intent_str.strip().lower()
                if clean_intent:
                    new_intent = TripIntent(
                        id=str(uuid.uuid4()),
                        trip_id=trip_id,
                        intent=clean_intent,
                    )
                    db.add(new_intent)

        await db.commit()
        updated = await TripService.get_trip_by_id(db, trip_id)
        return TripService._map_trip_read(updated)  # type: ignore[arg-type]

    @staticmethod
    async def delete_trip(db: AsyncSession, trip_id: str, user_id: str) -> bool:
        trip = await TripService.get_trip_by_id(db, trip_id)
        if not trip or trip.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "TRIP_NOT_FOUND", "message": "Trip not found."}},
            )

        await db.delete(trip)
        await db.commit()
        return True

    @staticmethod
    async def get_public_trip(db: AsyncSession, trip_id: str, viewer_id: str | None = None) -> PublicTripRead:
        trip = await TripService.get_trip_by_id(db, trip_id)
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "TRIP_NOT_FOUND", "message": "Trip not found."}},
            )

        # If private or matches_only and viewer is not owner, 404
        if trip.visibility in ("private", "matches_only") and trip.user_id != viewer_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "TRIP_NOT_FOUND", "message": "Trip not found."}},
            )

        profile_stmt = select(UserProfile.display_name).where(UserProfile.user_id == trip.user_id)
        profile_res = await db.execute(profile_stmt)
        display_name = profile_res.scalar_one_or_none()

        verif_stmt = select(VerificationRecord.status).where(
            VerificationRecord.user_id == trip.user_id,
            VerificationRecord.status == "verified",
        )
        verif_res = await db.execute(verif_stmt)
        is_verified = bool(verif_res.first())

        return TripService._map_public_trip_read(trip, display_name, is_verified)

    @staticmethod
    async def list_discoverable_trips(
        db: AsyncSession,
        destination_id: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        companion_preference: str | None = None,
        intent: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[PublicTripRead], int]:
        filters = [
            Trip.visibility.in_(["discoverable", "public"]),
            Trip.status.in_(["planned", "active"]),
        ]

        if destination_id:
            filters.append(Trip.destination_id == destination_id)

        # Date overlap condition: trip.start_date <= end_date AND trip.end_date >= start_date
        if start_date and end_date:
            filters.append(Trip.start_date <= end_date)
            filters.append(Trip.end_date >= start_date)
        elif start_date:
            filters.append(Trip.end_date >= start_date)
        elif end_date:
            filters.append(Trip.start_date <= end_date)

        if companion_preference:
            filters.append(Trip.companion_preference == companion_preference)

        if intent:
            intent_subq = select(TripIntent.trip_id).where(TripIntent.intent == intent.lower())
            filters.append(Trip.id.in_(intent_subq))

        count_stmt = select(func.count(Trip.id))
        stmt = (
            select(Trip)
            .options(selectinload(Trip.destination), selectinload(Trip.intents))
            .order_by(Trip.start_date.asc())
            .limit(limit)
            .offset(offset)
        )

        for f in filters:
            count_stmt = count_stmt.where(f)
            stmt = stmt.where(f)

        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one()

        trips_res = await db.execute(stmt)
        trips = list(trips_res.scalars().all())

        # Collect user ids for display names
        user_ids = {t.user_id for t in trips}
        profile_map: dict[str, str | None] = {}
        if user_ids:
            p_stmt = select(UserProfile.user_id, UserProfile.display_name).where(UserProfile.user_id.in_(user_ids))
            p_res = await db.execute(p_stmt)
            for uid, name in p_res.all():
                profile_map[uid] = name

        return [
            TripService._map_public_trip_read(t, profile_map.get(t.user_id), False)
            for t in trips
        ], total

    @staticmethod
    async def list_admin_trips(
        db: AsyncSession,
        query: str = "",
        status_filter: str | None = None,
        visibility_filter: str | None = None,
        destination_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[AdminTripRead], int]:
        filters = []
        if status_filter and status_filter != "all":
            filters.append(Trip.status == status_filter)
        if visibility_filter and visibility_filter != "all":
            filters.append(Trip.visibility == visibility_filter)
        if destination_id and destination_id != "all":
            filters.append(Trip.destination_id == destination_id)

        clean_q = query.strip()
        if clean_q:
            filters.append(
                or_(
                    Trip.title.ilike(f"%{clean_q}%"),
                    Trip.description.ilike(f"%{clean_q}%"),
                )
            )

        count_stmt = select(func.count(Trip.id))
        stmt = (
            select(Trip)
            .options(
                selectinload(Trip.destination),
                selectinload(Trip.intents),
                selectinload(Trip.user),
            )
            .order_by(Trip.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        for f in filters:
            count_stmt = count_stmt.where(f)
            stmt = stmt.where(f)

        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one()

        trips_res = await db.execute(stmt)
        trips = list(trips_res.scalars().all())

        items = []
        for t in trips:
            dest_summary = DestinationSummary(
                id=t.destination.id,
                name=t.destination.name,
                slug=t.destination.slug,
                country=t.destination.country,
                country_code=t.destination.country_code,
                region=t.destination.region,
                city=t.destination.city,
                category=t.destination.category,
                latitude=t.destination.latitude,
                longitude=t.destination.longitude,
            )
            items.append(
                AdminTripRead(
                    id=t.id,
                    user_id=t.user_id,
                    user_email=t.user.email if t.user else None,
                    destination_id=t.destination_id,
                    destination=dest_summary,
                    title=t.title,
                    description=t.description,
                    start_date=t.start_date,
                    end_date=t.end_date,
                    status=t.status,
                    visibility=t.visibility,
                    companion_preference=t.companion_preference,
                    party_size=t.party_size,
                    intents=[i.intent for i in t.intents],
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                )
            )

        return items, total
