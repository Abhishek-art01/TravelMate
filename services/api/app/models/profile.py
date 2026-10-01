from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserProfile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_of_birth: Mapped[str | None] = mapped_column(String(16), nullable=True)
    gender_identity: Mapped[str | None] = mapped_column(String(80), nullable=True)
    profile_visibility: Mapped[str] = mapped_column(String(32), default="hidden", nullable=False)
    discovery_visibility: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    profile_status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    profile_completion: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_profiles_user_id"),
        CheckConstraint("profile_completion >= 0 AND profile_completion <= 100", name="ck_profiles_completion_range"),
        CheckConstraint(
            "profile_visibility IN ('public', 'discoverable', 'limited', 'hidden', 'private')",
            name="ck_profiles_visibility",
        ),
    )
