from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.spatial import GeographyPointType


class Destination(Base):
    __tablename__ = "destinations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    country: Mapped[str] = mapped_column(String(80), nullable=False)
    country_code: Mapped[str] = mapped_column(String(3), index=True, nullable=False)
    region: Mapped[str] = mapped_column(String(80), nullable=False)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    location_geom: Mapped[str | None] = mapped_column(GeographyPointType(), nullable=True)
    timezone: Mapped[str] = mapped_column(String(40), default="UTC", nullable=False)
    category: Mapped[str] = mapped_column(String(40), default="general", nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)
    external_provider: Mapped[str | None] = mapped_column(String(40), nullable=True)
    external_place_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    geonames_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    osm_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    aliases: Mapped[list[DestinationAlias]] = relationship(
        "DestinationAlias", back_populates="destination", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint("status IN ('active', 'draft', 'archived')", name="ck_destinations_status"),
        CheckConstraint("latitude >= -90.0 AND latitude <= 90.0", name="ck_destinations_latitude"),
        CheckConstraint("longitude >= -180.0 AND longitude <= 180.0", name="ck_destinations_longitude"),
        Index("idx_destinations_country_region", "country_code", "region"),
        Index("idx_destinations_coordinates", "latitude", "longitude"),
    )


class DestinationAlias(Base):
    __tablename__ = "destination_aliases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    destination_id: Mapped[str] = mapped_column(
        ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alias: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )

    destination: Mapped[Destination] = relationship("Destination", back_populates="aliases")

    __table_args__ = (
        UniqueConstraint("destination_id", "alias", name="uq_destination_aliases_dest_alias"),
        Index("idx_destination_aliases_search", "alias"),
    )
