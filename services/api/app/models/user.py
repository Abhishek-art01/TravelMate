from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    auth_provider_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    account_status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)
    deleted_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_seen_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
