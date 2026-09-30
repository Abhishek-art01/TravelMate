from __future__ import annotations

from pydantic import BaseModel


class SessionRead(BaseModel):
    session_id: str
    user_id: str
    device_id: str | None = None
    client_platform: str | None = None
    revoked: bool = False
