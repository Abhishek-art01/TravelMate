from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import User


class DiscoveryInteraction(Base):
    __tablename__ = "discovery_interactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    interaction_type: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    user: Mapped[User] = relationship("User", foreign_keys=[user_id], lazy="selectin")
    target_user: Mapped[User] = relationship("User", foreign_keys=[target_user_id], lazy="selectin")

    __table_args__ = (
        UniqueConstraint("user_id", "target_user_id", name="uq_discovery_interactions_user_target"),
        CheckConstraint("user_id != target_user_id", name="ck_discovery_interactions_not_self"),
        CheckConstraint(
            "interaction_type IN ('like', 'pass', 'super_like', 'save')",
            name="ck_discovery_interactions_type",
        ),
        Index("idx_discovery_interactions_target_type", "target_user_id", "interaction_type"),
    )
