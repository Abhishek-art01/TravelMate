from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class StorageUnavailable(RuntimeError):
    pass


class UnconfiguredStorage:
    provider = "r2"

    async def create_upload_url(self, object_key: str, content_type: str, size_bytes: int, expires_seconds: int) -> str:
        raise StorageUnavailable("Object storage is not configured")

    async def inspect_object(self, object_key: str) -> tuple[StoredObject, bytes]:
        raise StorageUnavailable("Object storage is not configured")

    async def create_download_url(self, object_key: str, expires_seconds: int) -> str:
        raise StorageUnavailable("Object storage is not configured")

    async def delete_object(self, object_key: str) -> None:
        raise StorageUnavailable("Object storage is not configured")


@dataclass(frozen=True)
class StoredObject:
    size_bytes: int
    content_type: str | None


class MediaStorage(Protocol):
    provider: str

    async def create_upload_url(self, object_key: str, content_type: str, size_bytes: int, expires_seconds: int) -> str: ...

    async def inspect_object(self, object_key: str) -> tuple[StoredObject, bytes]: ...

    async def create_download_url(self, object_key: str, expires_seconds: int) -> str: ...

    async def delete_object(self, object_key: str) -> None: ...
