from __future__ import annotations

from pydantic import BaseModel, EmailStr


class UserSummary(BaseModel):
    user_id: str
    email: EmailStr | None = None
    role: str = "user"
    account_status: str = "active"
