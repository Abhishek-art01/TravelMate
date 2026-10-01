from __future__ import annotations

from app.config import get_settings
from app.services.media import ProfileMediaService
from app.services.media_storage import StorageUnavailable, UnconfiguredStorage
from app.services.r2_storage import R2Storage


def get_profile_media_service() -> ProfileMediaService:
    try:
        return ProfileMediaService(R2Storage(get_settings()))
    except StorageUnavailable:
        return ProfileMediaService(UnconfiguredStorage())
