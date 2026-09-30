from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.security import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    return {
        "user_id": current_user["user_id"],
        "email": current_user.get("email"),
        "role": current_user["role"],
        "account_status": "active",
        "provider": "supabase",
    }
