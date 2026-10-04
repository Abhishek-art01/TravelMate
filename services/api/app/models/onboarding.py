from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint, Integer, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class ProviderIdentity(Base):
    __tablename__ = "provider_identities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    last_synced_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (UniqueConstraint("provider", "provider_subject", name="uq_provider_identities_subject"),)

class ProfileIdentity(Base):
    __tablename__ = "profile_identities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    first_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    middle_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    pronouns: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)

class DatingPreferences(Base):
    __tablename__ = "dating_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    attraction_preference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    primary_intention: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)

class DiscoveryPreferences(Base):
    __tablename__ = "discovery_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    discovery_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    target_audience: Mapped[str | None] = mapped_column(String(255), nullable=True)
    travel_social_preference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)

class TravelPreferences(Base):
    __tablename__ = "travel_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    travel_frequency: Mapped[str | None] = mapped_column(String(100), nullable=True)
    preferred_trip_duration: Mapped[str | None] = mapped_column(String(100), nullable=True)
    solo_group_preference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    travel_style: Mapped[str | None] = mapped_column(Text, nullable=True)
    compatibility_pace: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)

class LifestylePreferences(Base):
    __tablename__ = "lifestyle_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    food_preferences: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smoking_preference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    alcohol_preference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pets: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)
