from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ProfileUploadCreate(BaseModel):
    media_type: Literal["profile_media"] = "profile_media"
    mime_type: Literal["image/jpeg", "image/png", "image/webp"]
    size_bytes: int = Field(gt=0)
    visibility: Literal["public", "profile_only", "private"] = "profile_only"


class ProfileUploadCreated(BaseModel):
    media_id: str
    upload_url: str
    expires_at: datetime
    required_headers: dict[str, str]


class UploadComplete(BaseModel):
    pass


class MediaRead(BaseModel):
    media_id: str
    media_type: str
    processing_status: str
    moderation_status: str
    visibility: str
    mime_type: str
    size_bytes: int
    width: int | None
    height: int | None
    sort_order: int
    created_at: datetime
    download_url: str | None = None


class MediaPage(BaseModel):
    items: list[MediaRead]
    next_cursor: str | None = None


class MediaOrderUpdate(BaseModel):
    sort_order: int = Field(ge=0, le=1000)
