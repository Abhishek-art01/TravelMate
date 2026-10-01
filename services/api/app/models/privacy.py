from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserPrivacySettings(Base):
    __tablename__ = "user_privacy_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    location_precision: Mapped[str] = mapped_column(String(24), default="approximate", nullable=False)
    allow_exact_location_sharing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    personalization_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    communications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_privacy_settings_user_id"),
        CheckConstraint("location_precision IN ('hidden', 'approximate', 'destination')", name="ck_user_privacy_location_precision"),
    )
