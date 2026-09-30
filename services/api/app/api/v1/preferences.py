from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import get_current_user

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("/")
async def get_preferences(current_user: Annotated[dict, Depends(get_current_user)]):
    return {
        "user_id": current_user["user_id"],
        "preferences": {
            "travel_intent": ["dating", "travel_companion"],
            "discovery_visibility": "friends_only",
            "privacy_mode": "standard",
        },
    }


@router.patch("/")
async def update_preferences(current_user: Annotated[dict, Depends(get_current_user)]):
    return {
        "updated": True,
        "user_id": current_user["user_id"],
        "message": "Preferences updated.",
    }
