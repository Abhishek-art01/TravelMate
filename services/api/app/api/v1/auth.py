from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.security import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenRequest(BaseModel):
    token: str = Field(..., min_length=10)


@router.post("/verify")
async def verify_token(payload: TokenRequest):
    try:
        auth_context = await get_current_user()
    except HTTPException:
        raise

    return {
        "verified": True,
        "user_id": auth_context["user_id"],
        "role": auth_context["role"],
        "provider": "supabase",
    }


@router.post("/session")
async def create_session(payload: TokenRequest):
    if not payload.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_TOKEN", "message": "A bearer token is required."}},
        )

    return {
        "status": "session_ready",
        "provider": "supabase",
        "token_length": len(payload.token),
    }
