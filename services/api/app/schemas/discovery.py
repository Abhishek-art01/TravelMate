from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DiscoveryTripRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    destination_id: str
    destination_name: str
    city: str | None = None
    region: str | None = None
    country: str
    country_code: str
    start_date: date
    end_date: date
    companion_preference: str
    party_size: int
    intents: list[str] = Field(default_factory=list)


class DiscoveryCandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    display_name: str
    age: int
    bio: str | None = None
    gender_identity: str | None = None
    is_verified: bool = False
    photo_url: str | None = None
    approx_city: str | None = None
    approx_country: str | None = None
    approx_latitude: float | None = None
    approx_longitude: float | None = None
    approx_distance_km: float | None = None
    trips: list[DiscoveryTripRead] = Field(default_factory=list)
    travel_intentions: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    match_score: int = Field(ge=0, le=100)
    match_reasons: list[str] = Field(default_factory=list)


class DiscoveryListResponse(BaseModel):
    items: list[DiscoveryCandidateRead]
    next_cursor: str | None = None
    total: int


class DiscoveryInteractionCreate(BaseModel):
    interaction_type: Literal["like", "pass"]


class DiscoveryInteractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    target_user_id: str
    interaction_type: str
    is_match: bool = False
    created_at: datetime


class UserBlockCreate(BaseModel):
    reason: str | None = Field(default=None, max_length=255)


class UserBlockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    blocker_id: str
    blocked_id: str
    reason: str | None = None
    created_at: datetime


class UserBlockListResponse(BaseModel):
    items: list[UserBlockRead]
    total: int


REPORT_REASONS = Literal[
    "inappropriate_content",
    "harassment",
    "spam_or_commercial",
    "fake_profile",
    "safety_concern",
    "other",
]


class UserReportCreate(BaseModel):
    reported_id: str
    reason: REPORT_REASONS
    details: str | None = Field(default=None, max_length=1000)


class UserReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    reporter_id: str
    reported_id: str
    reason: str
    details: str | None = None
    status: str
    created_at: datetime


class AdminReportUpdate(BaseModel):
    status: Literal["pending", "under_review", "actioned", "dismissed"]
    resolution_notes: str | None = Field(default=None, max_length=1000)


class AdminReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    reporter_id: str
    reported_id: str
    reason: str
    details: str | None = None
    status: str
    reviewed_by_id: str | None = None
    resolution_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class AdminReportListResponse(BaseModel):
    items: list[AdminReportRead]
    total: int
