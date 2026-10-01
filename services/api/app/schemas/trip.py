from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.destination import DestinationSummary


class TripBase(BaseModel):
    destination_id: str
    title: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    start_date: date
    end_date: date
    visibility: str = Field(default="discoverable", pattern="^(private|matches_only|discoverable|public)$")
    companion_preference: str = Field(
        default="open_to_companion",
        pattern="^(travelling_alone|open_to_companion|travelling_with_group)$",
    )
    party_size: int = Field(default=1, ge=1, le=50)
    intents: list[str] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def validate_dates(self) -> TripBase:
        if self.start_date > self.end_date:
            raise ValueError("start_date must be on or before end_date")
        if (self.end_date - self.start_date).days > 365:
            raise ValueError("Trip duration cannot exceed 365 days")
        return self


class TripCreate(TripBase):
    pass


class TripUpdate(BaseModel):
    destination_id: str | None = None
    title: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = Field(
        default=None,
        pattern="^(draft|planned|active|completed|cancelled|archived)$",
    )
    visibility: str | None = Field(
        default=None,
        pattern="^(private|matches_only|discoverable|public)$",
    )
    companion_preference: str | None = Field(
        default=None,
        pattern="^(travelling_alone|open_to_companion|travelling_with_group)$",
    )
    party_size: int | None = Field(default=None, ge=1, le=50)
    intents: list[str] | None = Field(default=None, max_length=8)

    @model_validator(mode="after")
    def validate_dates(self) -> TripUpdate:
        if self.start_date is not None and self.end_date is not None:
            if self.start_date > self.end_date:
                raise ValueError("start_date must be on or before end_date")
            if (self.end_date - self.start_date).days > 365:
                raise ValueError("Trip duration cannot exceed 365 days")
        return self


class TripRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    destination_id: str
    destination: DestinationSummary
    title: str
    description: str | None = None
    start_date: date
    end_date: date
    status: str
    visibility: str
    companion_preference: str
    party_size: int
    intents: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PublicTripRead(BaseModel):
    id: str
    destination: DestinationSummary
    title: str
    description: str | None = None
    start_date: date
    end_date: date
    companion_preference: str
    party_size: int
    intents: list[str] = Field(default_factory=list)
    creator_display_name: str | None = None
    creator_avatar_url: str | None = None
    creator_verified: bool = False
    created_at: datetime


class AdminTripRead(BaseModel):
    id: str
    user_id: str
    user_email: str | None = None
    destination_id: str
    destination: DestinationSummary
    title: str
    description: str | None = None
    start_date: date
    end_date: date
    status: str
    visibility: str
    companion_preference: str
    party_size: int
    intents: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class TripListResponse(BaseModel):
    items: list[TripRead]
    total: int
    limit: int
    offset: int


class PublicTripListResponse(BaseModel):
    items: list[PublicTripRead]
    total: int
    limit: int
    offset: int


class AdminTripListResponse(BaseModel):
    items: list[AdminTripRead]
    total: int
    limit: int
    offset: int
