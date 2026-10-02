from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import User


class UserReport(Base):
    __tablename__ = "user_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    reporter_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reported_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="pending", nullable=False)
    reviewed_by_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    reporter: Mapped[User] = relationship("User", foreign_keys=[reporter_id], lazy="selectin")
    reported: Mapped[User] = relationship("User", foreign_keys=[reported_id], lazy="selectin")
    reviewed_by: Mapped[User | None] = relationship("User", foreign_keys=[reviewed_by_id], lazy="selectin")

    __table_args__ = (
        CheckConstraint("reporter_id != reported_id", name="ck_user_reports_not_self"),
        CheckConstraint(
            "status IN ('pending', 'under_review', 'actioned', 'dismissed')",
            name="ck_user_reports_status",
        ),
        Index("idx_user_reports_status_created", "status", "created_at"),
        Index("idx_user_reports_reported", "reported_id"),
    )
