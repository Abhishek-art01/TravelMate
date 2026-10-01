from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    minimum_age: Mapped[int] = mapped_column(Integer, default=18, nullable=False)
    maximum_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_preferences_user_id"),
        CheckConstraint("minimum_age >= 18 AND minimum_age <= 100", name="ck_user_preferences_minimum_age"),
        CheckConstraint("maximum_age IS NULL OR (maximum_age >= minimum_age AND maximum_age <= 100)", name="ck_user_preferences_maximum_age"),
    )


class UserPreferenceOption(Base):
    __tablename__ = "user_preference_options"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "category", "value", name="uq_user_preference_options_value"),
        CheckConstraint(
            "category IN ('dating_intention', 'dating_preference', 'discovery_preference', 'travel_intention', 'language')",
            name="ck_user_preference_options_category",
        ),
    )
