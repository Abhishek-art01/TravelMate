from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Interest(Base):
    __tablename__ = "interests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class InterestTranslation(Base):
    __tablename__ = "interest_translations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    interest_id: Mapped[str] = mapped_column(ForeignKey("interests.id", ondelete="CASCADE"), nullable=False)
    language_code: Mapped[str] = mapped_column(String(16), nullable=False)
    localized_name: Mapped[str] = mapped_column(String(100), nullable=False)

    __table_args__ = (UniqueConstraint("interest_id", "language_code", name="uq_interest_translations_locale"),)


class UserInterest(Base):
    __tablename__ = "user_interests"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    interest_id: Mapped[str] = mapped_column(ForeignKey("interests.id", ondelete="RESTRICT"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now())
