from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator


def _calculate_age(value: date) -> int:
    today = date.today()
    return today.year - value.year - ((today.month, today.day) < (value.month, value.day))


class ProfileCreate(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=80)
    date_of_birth: date
    bio: str | None = Field(default=None, max_length=500)

    @field_validator("date_of_birth")
    @classmethod
    def validate_age(cls, value: date) -> date:
        if _calculate_age(value) < 18:
            raise ValueError("date_of_birth must be at least 18 years old")
        return value


class ProfileRead(BaseModel):
    profile_id: str
    display_name: str
    age: int
    bio: str | None = None
    status: str = "active"
