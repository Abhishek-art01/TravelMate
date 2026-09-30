from __future__ import annotations

from pydantic import BaseModel


class VerificationState(BaseModel):
    user_id: str
    category: str
    status: str = "not_started"
    provider: str | None = None
