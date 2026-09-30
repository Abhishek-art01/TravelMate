from __future__ import annotations

from pydantic import BaseModel, Field


class TokenVerificationRequest(BaseModel):
    token: str = Field(..., min_length=10)


class TokenVerificationResponse(BaseModel):
    verified: bool
    user_id: str | None = None
    role: str | None = None
    provider: str = "supabase"
