from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import User


class UserBlock(Base):
    __tablename__ = "user_blocks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    blocker_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    blocked_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )

    blocker: Mapped[User] = relationship("User", foreign_keys=[blocker_id], lazy="selectin")
    blocked: Mapped[User] = relationship("User", foreign_keys=[blocked_id], lazy="selectin")

    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="uq_user_blocks_blocker_blocked"),
        CheckConstraint("blocker_id != blocked_id", name="ck_user_blocks_not_self"),
        Index("idx_user_blocks_blocked_blocker", "blocked_id", "blocker_id"),
    )
