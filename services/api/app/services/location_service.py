from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.destination import Destination, DestinationAlias
from app.models.location import UserLocation
from app.schemas.destination import DestinationCreate, DestinationUpdate
from app.schemas.location import LocationUpdate
from app.services.location_privacy import approximate_coordinates, bounding_box, haversine_distance_km

INITIAL_DESTINATIONS = [
    {
        "name": "Goa",
        "slug": "goa",
        "country": "India",
        "country_code": "IND",
        "region": "Goa",
        "city": "Panaji",
        "description": "Tropical paradise known for golden beaches, vibrant nightlife, Portuguese heritage, and seafood.",
        "latitude": 15.4989,
        "longitude": 73.8278,
        "timezone": "Asia/Kolkata",
        "category": "beach",
        "aliases": ["north goa", "south goa"],
    },
    {
        "name": "Mumbai",
        "slug": "mumbai",
        "country": "India",
        "country_code": "IND",
        "region": "Maharashtra",
        "city": "Mumbai",
        "description": "Financial capital and city of dreams, home to Marine Drive, Gateway of India, and Bollywood.",
        "latitude": 18.9220,
        "longitude": 72.8347,
        "timezone": "Asia/Kolkata",
        "category": "city",
        "aliases": ["bombay"],
    },
    {
        "name": "Bengaluru",
        "slug": "bengaluru",
        "country": "India",
        "country_code": "IND",
        "region": "Karnataka",
        "city": "Bengaluru",
        "description": "India's tech hub and Garden City, renowned for craft breweries, vibrant cafes, and pleasant weather.",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "timezone": "Asia/Kolkata",
        "category": "city",
        "aliases": ["bangalore"],
    },
    {
        "name": "New Delhi",
        "slug": "new-delhi",
        "country": "India",
        "country_code": "IND",
        "region": "Delhi",
        "city": "New Delhi",
        "description": "Historic national capital filled with Mughal monuments, grand avenues, and culinary diversity.",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone": "Asia/Kolkata",
        "category": "heritage",
        "aliases": ["delhi", "dilli"],
    },
    {
        "name": "Jaipur",
        "slug": "jaipur",
        "country": "India",
        "country_code": "IND",
        "region": "Rajasthan",
        "city": "Jaipur",
        "description": "The Pink City, celebrated for majestic hilltop forts, royal palaces, and textile traditions.",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "timezone": "Asia/Kolkata",
        "category": "heritage",
        "aliases": ["pink city"],
    },
    {
        "name": "Kochi",
        "slug": "kochi",
        "country": "India",
        "country_code": "IND",
        "region": "Kerala",
        "city": "Kochi",
        "description": "Queen of the Arabian Sea, featuring Chinese fishing nets, colonial spice warehouses, and backwaters.",
        "latitude": 9.9312,
        "longitude": 76.2673,
        "timezone": "Asia/Kolkata",
        "category": "coastal",
        "aliases": ["cochin"],
    },
    {
        "name": "Manali",
        "slug": "manali",
        "country": "India",
        "country_code": "IND",
        "region": "Himachal Pradesh",
        "city": "Manali",
        "description": "Himalayan resort town set along the Beas River, popular for trekking, skiing, and mountain passes.",
        "latitude": 32.2432,
        "longitude": 77.1892,
        "timezone": "Asia/Kolkata",
        "category": "mountains",
        "aliases": ["kullu manali"],
    },
    {
        "name": "Varanasi",
        "slug": "varanasi",
        "country": "India",
        "country_code": "IND",
        "region": "Uttar Pradesh",
        "city": "Varanasi",
        "description": "One of the world's oldest living cities, celebrated for sacred Ganges ghats, evening aarti, and silk.",
        "latitude": 25.3176,
        "longitude": 82.9739,
        "timezone": "Asia/Kolkata",
        "category": "heritage",
        "aliases": ["banaras", "kashi", "benares"],
    },
    {
        "name": "Leh Ladakh",
        "slug": "leh-ladakh",
        "country": "India",
        "country_code": "IND",
        "region": "Ladakh",
        "city": "Leh",
        "description": "High-altitude desert wonderland framed by monastery-dotted valleys, Pangong Tso, and mountain passes.",
        "latitude": 34.1526,
        "longitude": 77.5771,
        "timezone": "Asia/Kolkata",
        "category": "mountains",
        "aliases": ["ladakh", "leh"],
    },
    {
        "name": "Paris",
        "slug": "paris",
        "country": "France",
        "country_code": "FRA",
        "region": "Île-de-France",
        "city": "Paris",
        "description": "City of Light, famed for art museums, Haussmannian boulevards, cafes, and global culture.",
        "latitude": 48.8566,
        "longitude": 2.3522,
        "timezone": "Europe/Paris",
        "category": "city",
        "aliases": ["city of light"],
    },
    {
        "name": "Tokyo",
        "slug": "tokyo",
        "country": "Japan",
        "country_code": "JPN",
        "region": "Kanto",
        "city": "Tokyo",
        "description": "Ultra-modern metropolis blending neon skyscrapers, historic shrines, culinary mastery, and anime.",
        "latitude": 35.6762,
        "longitude": 139.6503,
        "timezone": "Asia/Tokyo",
        "category": "city",
        "aliases": ["edo"],
    },
    {
        "name": "Bangkok",
        "slug": "bangkok",
        "country": "Thailand",
        "country_code": "THA",
        "region": "Central Thailand",
        "city": "Bangkok",
        "description": "Bustling capital known for ornate shrines, lively street food, Chao Phraya river boats, and night markets.",
        "latitude": 13.7563,
        "longitude": 100.5018,
        "timezone": "Asia/Bangkok",
        "category": "city",
        "aliases": ["krung thep"],
    },
]


class LocationService:
    @staticmethod
    async def get_destination_by_id(db: AsyncSession, destination_id: str) -> Destination | None:
        stmt = (
            select(Destination)
            .options(selectinload(Destination.aliases))
            .where(Destination.id == destination_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_destination_by_slug(db: AsyncSession, slug: str) -> Destination | None:
        stmt = (
            select(Destination)
            .options(selectinload(Destination.aliases))
            .where(Destination.slug == slug)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def search_destinations(
        db: AsyncSession,
        query: str = "",
        country_code: str | None = None,
        category: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Destination], int]:
        clean_q = query.strip().lower()

        stmt = select(Destination).options(selectinload(Destination.aliases))
        count_stmt = select(func.count(Destination.id))

        filters = [Destination.status == "active"]

        if country_code:
            filters.append(Destination.country_code == country_code.upper())
        if category:
            filters.append(Destination.category == category.lower())

        if clean_q:
            alias_subq = select(DestinationAlias.destination_id).where(
                DestinationAlias.alias.ilike(f"%{clean_q}%")
            )
            q_filter = or_(
                Destination.name.ilike(f"%{clean_q}%"),
                Destination.city.ilike(f"%{clean_q}%"),
                Destination.region.ilike(f"%{clean_q}%"),
                Destination.country.ilike(f"%{clean_q}%"),
                Destination.id.in_(alias_subq),
            )
            filters.append(q_filter)

        for f in filters:
            stmt = stmt.where(f)
            count_stmt = count_stmt.where(f)

        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = stmt.order_by(Destination.name.asc()).limit(limit).offset(offset)
        result = await db.execute(stmt)
        items = list(result.scalars().all())
        return items, total

    @staticmethod
    async def get_nearby_destinations(
        db: AsyncSession,
        latitude: float,
        longitude: float,
        radius_km: float = 100.0,
        limit: int = 20,
    ) -> list[tuple[Destination, float]]:
        min_lat, max_lat, min_lon, max_lon = bounding_box(latitude, longitude, radius_km)

        stmt = (
            select(Destination)
            .options(selectinload(Destination.aliases))
            .where(
                Destination.status == "active",
                Destination.latitude >= min_lat,
                Destination.latitude <= max_lat,
                Destination.longitude >= min_lon,
                Destination.longitude <= max_lon,
            )
        )
        result = await db.execute(stmt)
        candidates = result.scalars().all()

        within_radius: list[tuple[Destination, float]] = []
        for d in candidates:
            dist = haversine_distance_km(latitude, longitude, d.latitude, d.longitude)
            if dist <= radius_km:
                within_radius.append((d, round(dist, 2)))

        within_radius.sort(key=lambda x: x[1])
        return within_radius[:limit]

    @staticmethod
    async def create_destination(db: AsyncSession, data: DestinationCreate) -> Destination:
        dest_id = str(uuid.uuid4())
        destination = Destination(
            id=dest_id,
            name=data.name,
            slug=data.slug,
            country=data.country,
            country_code=data.country_code.upper(),
            region=data.region,
            city=data.city,
            description=data.description,
            latitude=data.latitude,
            longitude=data.longitude,
            timezone=data.timezone,
            category=data.category,
            status=data.status,
        )
        db.add(destination)
        await db.flush()

        for alias_str in set(data.aliases):
            clean_alias = alias_str.strip().lower()
            if clean_alias:
                alias_obj = DestinationAlias(
                    id=str(uuid.uuid4()),
                    destination_id=dest_id,
                    alias=clean_alias,
                    locale="en",
                )
                db.add(alias_obj)

        await db.commit()
        return await LocationService.get_destination_by_id(db, dest_id)  # type: ignore[return-value]

    @staticmethod
    async def update_destination(
        db: AsyncSession, destination_id: str, data: DestinationUpdate
    ) -> Destination | None:
        dest = await LocationService.get_destination_by_id(db, destination_id)
        if not dest:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            if field != "aliases" and hasattr(dest, field):
                setattr(dest, field, value)

        if data.aliases is not None:
            # Refresh aliases
            for old_alias in list(dest.aliases):
                await db.delete(old_alias)
            await db.flush()
            for alias_str in set(data.aliases):
                clean_alias = alias_str.strip().lower()
                if clean_alias:
                    new_alias = DestinationAlias(
                        id=str(uuid.uuid4()),
                        destination_id=destination_id,
                        alias=clean_alias,
                        locale="en",
                    )
                    db.add(new_alias)

        await db.commit()
        return await LocationService.get_destination_by_id(db, destination_id)

    @staticmethod
    async def seed_default_destinations(db: AsyncSession) -> int:
        seeded = 0
        for entry in INITIAL_DESTINATIONS:
            existing = await LocationService.get_destination_by_slug(db, entry["slug"])  # type: ignore[arg-type]
            if not existing:
                create_data = DestinationCreate(
                    name=entry["name"],  # type: ignore[arg-type]
                    slug=entry["slug"],  # type: ignore[arg-type]
                    country=entry["country"],  # type: ignore[arg-type]
                    country_code=entry["country_code"],  # type: ignore[arg-type]
                    region=entry["region"],  # type: ignore[arg-type]
                    city=entry["city"],  # type: ignore[arg-type]
                    description=entry["description"],  # type: ignore[arg-type]
                    latitude=entry["latitude"],  # type: ignore[arg-type]
                    longitude=entry["longitude"],  # type: ignore[arg-type]
                    timezone=entry["timezone"],  # type: ignore[arg-type]
                    category=entry["category"],  # type: ignore[arg-type]
                    status="active",
                    aliases=entry.get("aliases", []),  # type: ignore[arg-type]
                )
                await LocationService.create_destination(db, create_data)
                seeded += 1
        return seeded

    # User Location Methods
    @staticmethod
    async def get_user_location(db: AsyncSession, user_id: str) -> UserLocation | None:
        stmt = select(UserLocation).where(UserLocation.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def set_user_location(
        db: AsyncSession, user_id: str, data: LocationUpdate
    ) -> UserLocation:
        existing = await LocationService.get_user_location(db, user_id)

        lat = data.latitude or 0.0
        lon = data.longitude or 0.0
        approx_lat, approx_lon = approximate_coordinates(
            lat, lon, precision_mode=data.precision
        )

        exact_lat = data.latitude if data.sharing_mode == "explicit_share" else None
        exact_lon = data.longitude if data.sharing_mode == "explicit_share" else None

        if existing:
            existing.latitude = exact_lat
            existing.longitude = exact_lon
            existing.approx_latitude = approx_lat
            existing.approx_longitude = approx_lon
            existing.precision = data.precision
            existing.sharing_mode = data.sharing_mode
            existing.source = data.source
            existing.city = data.city
            existing.region = data.region
            existing.country_code = data.country_code
            await db.commit()
            await db.refresh(existing)
            return existing

        location_id = str(uuid.uuid4())
        new_loc = UserLocation(
            id=location_id,
            user_id=user_id,
            latitude=exact_lat,
            longitude=exact_lon,
            approx_latitude=approx_lat,
            approx_longitude=approx_lon,
            precision=data.precision,
            sharing_mode=data.sharing_mode,
            source=data.source,
            city=data.city,
            region=data.region,
            country_code=data.country_code,
        )
        db.add(new_loc)
        await db.commit()
        await db.refresh(new_loc)
        return new_loc

    @staticmethod
    async def delete_user_location(db: AsyncSession, user_id: str) -> bool:
        existing = await LocationService.get_user_location(db, user_id)
        if not existing:
            return False
        await db.delete(existing)
        await db.commit()
        return True
