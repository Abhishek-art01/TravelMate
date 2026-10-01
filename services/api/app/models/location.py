from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.spatial import GeographyPointType


class UserLocation(Base):
    __tablename__ = "user_locations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    approx_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    approx_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    location_geom: Mapped[str | None] = mapped_column(GeographyPointType(), nullable=True)
    precision: Mapped[str] = mapped_column(String(24), default="approximate", nullable=False)
    sharing_mode: Mapped[str] = mapped_column(String(24), default="approximate", nullable=False)
    source: Mapped[str] = mapped_column(String(32), default="manual", nullable=False)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    region: Mapped[str | None] = mapped_column(String(80), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_locations_user_id"),
        CheckConstraint(
            "precision IN ('exact', 'approximate', 'city', 'destination', 'region')",
            name="ck_user_locations_precision",
        ),
        CheckConstraint(
            "sharing_mode IN ('private', 'approximate', 'explicit_share')",
            name="ck_user_locations_sharing_mode",
        ),
        Index("idx_user_locations_approx_coords", "approx_latitude", "approx_longitude"),
    )
