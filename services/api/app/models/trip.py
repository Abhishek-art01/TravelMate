from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.destination import Destination
from app.models.user import User


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    destination_id: Mapped[str] = mapped_column(
        ForeignKey("destinations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(24), default="planned", nullable=False)
    visibility: Mapped[str] = mapped_column(String(24), default="discoverable", nullable=False)
    companion_preference: Mapped[str] = mapped_column(String(32), default="open_to_companion", nullable=False)
    party_size: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    destination: Mapped[Destination] = relationship("Destination", lazy="selectin")
    user: Mapped[User] = relationship("User", lazy="selectin")
    intents: Mapped[list[TripIntent]] = relationship(
        "TripIntent", back_populates="trip", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint("start_date <= end_date", name="ck_trips_start_end_dates"),
        CheckConstraint(
            "status IN ('draft', 'planned', 'active', 'completed', 'cancelled', 'archived')",
            name="ck_trips_status",
        ),
        CheckConstraint(
            "visibility IN ('private', 'matches_only', 'discoverable', 'public')",
            name="ck_trips_visibility",
        ),
        CheckConstraint(
            "companion_preference IN ('travelling_alone', 'open_to_companion', 'travelling_with_group')",
            name="ck_trips_companion_preference",
        ),
        CheckConstraint("party_size >= 1 AND party_size <= 50", name="ck_trips_party_size"),
        Index("idx_trips_dates", "start_date", "end_date"),
        Index("idx_trips_destination_dates", "destination_id", "start_date", "end_date"),
        Index("idx_trips_visibility_status", "visibility", "status"),
    )


class TripIntent(Base):
    __tablename__ = "trip_intents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    trip_id: Mapped[str] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    intent: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )

    trip: Mapped[Trip] = relationship("Trip", back_populates="intents")

    __table_args__ = (
        UniqueConstraint("trip_id", "intent", name="uq_trip_intents_trip_intent"),
        CheckConstraint(
            "intent IN ('dating_romantic', 'serious_relationship', 'casual_dating', 'travel_companion', 'friends_social', 'local_guide', 'activity_partner')",
            name="ck_trip_intents_intent",
        ),
    )
