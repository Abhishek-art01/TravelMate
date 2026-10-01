from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.privacy import ProfileVisibility


def calculate_age(date_of_birth: date, today: date | None = None) -> int:
    current = today or datetime.now(UTC).date()
    return current.year - date_of_birth.year - ((current.month, current.day) < (date_of_birth.month, date_of_birth.day))


def validate_adult(value: date) -> date:
    if calculate_age(value) < 18:
        raise ValueError("date_of_birth must be at least 18 years old")
    return value


class ProfileCreate(BaseModel):
    display_name: str = Field(min_length=2, max_length=80)
    date_of_birth: date
    bio: str | None = Field(default=None, max_length=500)
    gender_identity: str | None = Field(default=None, max_length=80)

    @field_validator("date_of_birth")
    @classmethod
    def validate_minimum_age(cls, value: date) -> date:
        return validate_adult(value)


class ProfileWrite(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=80)
    date_of_birth: date | None = None
    bio: str | None = Field(default=None, max_length=500)
    gender_identity: str | None = Field(default=None, max_length=80)
    profile_visibility: ProfileVisibility | None = None
    discovery_visibility: bool | None = None

    @field_validator("date_of_birth")
    @classmethod
    def validate_minimum_age(cls, value: date | None) -> date | None:
        return validate_adult(value) if value is not None else None


class OwnProfileRead(BaseModel):
    profile_id: str
    user_id: str
    display_name: str | None
    age: int | None
    bio: str | None
    gender_identity: str | None
    profile_visibility: ProfileVisibility
    discovery_visibility: bool
    profile_status: str
    completion_percentage: int
    created_at: str
    updated_at: str


class ProfileWriteResponse(OwnProfileRead):
    pass


class PublicProfileRead(BaseModel):
    display_name: str
    age: int
    bio: str | None
    gender_identity: str | None
    interests: list[str] = Field(default_factory=list)
    profile_media: list[str] = Field(default_factory=list)
    profile_status: Literal["active"] = "active"
