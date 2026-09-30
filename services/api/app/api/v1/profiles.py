from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from app.core.security import get_current_user, get_current_user_optional

router = APIRouter(tags=["profiles"])


def _calculate_age(date_of_birth: date) -> int:
    today = date.today()
    return today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))


class ProfileCreate(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=80)
    date_of_birth: date
    bio: str | None = Field(default=None, max_length=500)

    @field_validator("date_of_birth")
    @classmethod
    def validate_minimum_age(cls, value: date) -> date:
        if _calculate_age(value) < 18:
            raise ValueError("date_of_birth must be at least 18 years old")
        return value


class ProfileResponse(BaseModel):
    profile_id: str
    display_name: str
    age: int
    bio: str | None = None
    status: str = "active"


@router.get("/me")
async def read_current_profile(current_user: dict = Depends(get_current_user)):
    return {
        "user_id": current_user["user_id"],
        "email": current_user.get("email"),
        "profile_status": "complete",
        "account_status": "active",
    }


@router.post("/profiles")
async def create_profile(payload: ProfileCreate, current_user: dict | None = Depends(get_current_user_optional)):
    profile = ProfileResponse(
        profile_id="profile-demo-001",
        display_name=payload.display_name,
        age=_calculate_age(payload.date_of_birth),
        bio=payload.bio,
    )
    return {
        "profile": profile.model_dump(),
        "user": current_user or {"user_id": "anonymous-demo-user", "role": "guest"},
        "privacy": {
            "location_visibility": "approximate_only",
            "verification_media_private": True,
        },
    }


@router.patch("/me/profile")
async def update_current_profile(current_user: dict = Depends(get_current_user)):
    return {
        "updated": True,
        "user_id": current_user["user_id"],
        "status": "profile_updated",
    }
