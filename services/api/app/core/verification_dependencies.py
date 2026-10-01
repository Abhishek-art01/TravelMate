from __future__ import annotations

from app.config import get_settings
from app.services.verification_provider import get_verification_provider
from app.services.verification_service import VerificationService
from app.services.verification_storage import (
    R2VerificationStorage,
    UnconfiguredVerificationStorage,
    VerificationStorageUnavailable,
)


def get_verification_service() -> VerificationService:
    settings = get_settings()
    provider = get_verification_provider(settings)
    try:
        storage = R2VerificationStorage(settings)
    except VerificationStorageUnavailable:
        storage = UnconfiguredVerificationStorage()

    return VerificationService(provider=provider, storage=storage, settings=settings)
