"""Upsert additional destinations required for the presentation dataset."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.destination import Destination

# Destinations to add on top of the 12 already seeded in Phase 6.
# slug must be globally unique.
EXTRA_DESTINATIONS: list[dict] = [
    {
        "name": "Dubai",
        "slug": "dubai",
        "country": "United Arab Emirates",
        "country_code": "AE",
        "region": "Dubai",
        "city": "Dubai",
        "description": "A futuristic desert city famous for luxury, skyscrapers, and global culture.",
        "latitude": 25.2048,
        "longitude": 55.2708,
        "timezone": "Asia/Dubai",
        "category": "city",
    },
    {
        "name": "Singapore",
        "slug": "singapore",
        "country": "Singapore",
        "country_code": "SG",
        "region": "Central Region",
        "city": "Singapore",
        "description": "A vibrant island city-state blending modernity with multicultural heritage.",
        "latitude": 1.3521,
        "longitude": 103.8198,
        "timezone": "Asia/Singapore",
        "category": "city",
    },
    {
        "name": "Bali",
        "slug": "bali",
        "country": "Indonesia",
        "country_code": "ID",
        "region": "Bali",
        "city": "Denpasar",
        "description": "Tropical island paradise known for temples, rice terraces, and surf beaches.",
        "latitude": -8.3405,
        "longitude": 115.0920,
        "timezone": "Asia/Makassar",
        "category": "beach",
    },
    {
        "name": "London",
        "slug": "london",
        "country": "United Kingdom",
        "country_code": "GB",
        "region": "England",
        "city": "London",
        "description": "A world capital with iconic history, culture, and cosmopolitan energy.",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "timezone": "Europe/London",
        "category": "city",
    },
    {
        "name": "Udaipur",
        "slug": "udaipur",
        "country": "India",
        "country_code": "IN",
        "region": "Rajasthan",
        "city": "Udaipur",
        "description": "The City of Lakes, known for its ornate palaces and romantic lakeside charm.",
        "latitude": 24.5854,
        "longitude": 73.7125,
        "timezone": "Asia/Kolkata",
        "category": "city",
    },
    {
        "name": "Rishikesh",
        "slug": "rishikesh",
        "country": "India",
        "country_code": "IN",
        "region": "Uttarakhand",
        "city": "Rishikesh",
        "description": "The yoga capital of the world, nestled in the Himalayan foothills by the Ganges.",
        "latitude": 30.0869,
        "longitude": 78.2676,
        "timezone": "Asia/Kolkata",
        "category": "adventure",
    },
    {
        "name": "Hyderabad",
        "slug": "hyderabad",
        "country": "India",
        "country_code": "IN",
        "region": "Telangana",
        "city": "Hyderabad",
        "description": "The City of Pearls — a blend of Nizami heritage, biryani, and tech culture.",
        "latitude": 17.3850,
        "longitude": 78.4867,
        "timezone": "Asia/Kolkata",
        "category": "city",
    },
    {
        "name": "Chennai",
        "slug": "chennai",
        "country": "India",
        "country_code": "IN",
        "region": "Tamil Nadu",
        "city": "Chennai",
        "description": "The cultural heart of South India with classical arts, temples, and beaches.",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "timezone": "Asia/Kolkata",
        "category": "city",
    },
    {
        "name": "Kolkata",
        "slug": "kolkata",
        "country": "India",
        "country_code": "IN",
        "region": "West Bengal",
        "city": "Kolkata",
        "description": "The City of Joy — rich in literature, colonial heritage, and street food.",
        "latitude": 22.5726,
        "longitude": 88.3639,
        "timezone": "Asia/Kolkata",
        "category": "city",
    },
    {
        "name": "Kashmir",
        "slug": "kashmir",
        "country": "India",
        "country_code": "IN",
        "region": "Jammu & Kashmir",
        "city": "Srinagar",
        "description": "Paradise on Earth — Dal Lake, Mughal gardens, and snow-capped Himalayas.",
        "latitude": 34.0836,
        "longitude": 74.7973,
        "timezone": "Asia/Kolkata",
        "category": "adventure",
    },
]


async def upsert_destinations(session: AsyncSession) -> dict[str, str]:
    """
    Upsert extra destinations. Returns a mapping slug→id for all destinations
    (existing + newly inserted) so the seed can look them up by slug.
    """
    # Load existing slugs
    existing_rows = (await session.execute(select(Destination))).scalars().all()
    existing_by_slug: dict[str, Destination] = {d.slug: d for d in existing_rows}

    now_dt = datetime.now(UTC)
    for spec in EXTRA_DESTINATIONS:
        if spec["slug"] in existing_by_slug:
            continue  # already present — idempotent
        dest = Destination(
            id=str(uuid.uuid4()),
            name=spec["name"],
            slug=spec["slug"],
            country=spec["country"],
            country_code=spec["country_code"],
            region=spec["region"],
            city=spec.get("city"),
            description=spec.get("description"),
            latitude=spec["latitude"],
            longitude=spec["longitude"],
            timezone=spec["timezone"],
            category=spec.get("category", "general"),
            status="active",
            created_at=now_dt,
            updated_at=now_dt,
        )
        session.add(dest)
        existing_by_slug[dest.slug] = dest

    await session.commit()

    # Refresh mapping after commit
    all_rows = (await session.execute(select(Destination))).scalars().all()
    return {d.slug: d.id for d in all_rows}
