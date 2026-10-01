from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    media_type: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(32), nullable=False)
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    processing_status: Mapped[str] = mapped_column(String(24), default="pending", nullable=False)
    moderation_status: Mapped[str] = mapped_column(String(24), default="pending_review", nullable=False)
    visibility: Mapped[str] = mapped_column(String(24), default="private", nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("object_key", name="uq_media_assets_object_key"),
        CheckConstraint("media_type IN ('profile_media', 'chat_media', 'verification_media')", name="ck_media_assets_type"),
        CheckConstraint("storage_provider IN ('r2', 'cloudinary')", name="ck_media_assets_provider"),
        CheckConstraint("processing_status IN ('pending', 'uploading', 'processing', 'ready', 'failed', 'deleted')", name="ck_media_assets_processing_status"),
        CheckConstraint("moderation_status IN ('pending_review', 'approved', 'rejected', 'requires_review')", name="ck_media_assets_moderation_status"),
        CheckConstraint("visibility IN ('public', 'profile_only', 'private')", name="ck_media_assets_visibility"),
        CheckConstraint("size_bytes > 0", name="ck_media_assets_size_positive"),
        CheckConstraint("sort_order >= 0", name="ck_media_assets_sort_order"),
        Index("ix_media_assets_user_type_status", "user_id", "media_type", "processing_status"),
    )
