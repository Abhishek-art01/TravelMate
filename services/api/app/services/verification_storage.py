from __future__ import annotations

import asyncio
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Protocol

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError

from app.config import Settings, get_settings


class VerificationStorageUnavailable(RuntimeError):
    """Raised when verification storage is not configured or fails to respond."""


@dataclass(frozen=True)
class StoredVerificationObject:
    size_bytes: int
    content_type: str | None


class VerificationStorageProtocol(Protocol):
    provider: str

    async def create_upload_url(self, object_key: str, content_type: str, size_bytes: int, expires_seconds: int) -> str: ...

    async def inspect_object(self, object_key: str) -> tuple[StoredVerificationObject, bytes]: ...

    async def create_download_url(self, object_key: str, expires_seconds: int) -> str: ...

    async def delete_object(self, object_key: str) -> None: ...


class UnconfiguredVerificationStorage:
    provider = "not_configured"

    async def create_upload_url(self, object_key: str, content_type: str, size_bytes: int, expires_seconds: int) -> str:
        raise VerificationStorageUnavailable("Verification object storage is not configured.")

    async def inspect_object(self, object_key: str) -> tuple[StoredVerificationObject, bytes]:
        raise VerificationStorageUnavailable("Verification object storage is not configured.")

    async def create_download_url(self, object_key: str, expires_seconds: int) -> str:
        raise VerificationStorageUnavailable("Verification object storage is not configured.")

    async def delete_object(self, object_key: str) -> None:
        raise VerificationStorageUnavailable("Verification object storage is not configured.")


class R2VerificationStorage(VerificationStorageProtocol):
    """Dedicated private verification storage adapter.

    Enforces that all objects reside in the protected 'verification/' namespace
    and provides strictly short-lived presigned URLs.
    """
    provider = "r2"

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        bucket = self.settings.verification_r2_bucket or self.settings.r2_bucket
        required = (
            self.settings.r2_account_id,
            bucket,
            self.settings.r2_endpoint,
            self.settings.r2_access_key_id,
            self.settings.r2_secret_access_key,
        )
        if not all(required):
            raise VerificationStorageUnavailable("R2 verification storage is not configured.")
        self.bucket = bucket

    @cached_property
    def client(self):
        return boto3.client(
            "s3",
            endpoint_url=self.settings.r2_endpoint,
            region_name=self.settings.r2_region,
            aws_access_key_id=self.settings.r2_access_key_id,
            aws_secret_access_key=self.settings.r2_secret_access_key,
            config=BotoConfig(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def _call(self, operation: str, **kwargs: Any) -> dict[str, Any]:
        try:
            return getattr(self.client, operation)(**kwargs)
        except (BotoCoreError, ClientError) as exc:
            raise VerificationStorageUnavailable("Verification storage request failed.") from exc

    def _validate_key_domain(self, object_key: str) -> None:
        if not object_key.startswith("verification/"):
            raise ValueError("Verification media key must reside in the private 'verification/' namespace.")

    async def create_upload_url(self, object_key: str, content_type: str, size_bytes: int, expires_seconds: int) -> str:
        self._validate_key_domain(object_key)
        expires = min(max(expires_seconds, 60), 300)
        return await asyncio.to_thread(
            self.client.generate_presigned_url,
            "put_object",
            Params={
                "Bucket": self.bucket,
                "Key": object_key,
                "ContentType": content_type,
                "ContentLength": size_bytes,
            },
            ExpiresIn=expires,
            HttpMethod="PUT",
        )

    async def inspect_object(self, object_key: str) -> tuple[StoredVerificationObject, bytes]:
        self._validate_key_domain(object_key)
        head = await asyncio.to_thread(self._call, "head_object", Bucket=self.bucket, Key=object_key)
        response = await asyncio.to_thread(self._call, "get_object", Bucket=self.bucket, Key=object_key)
        data = await asyncio.to_thread(response["Body"].read)
        return StoredVerificationObject(int(head.get("ContentLength", 0)), head.get("ContentType")), data

    async def create_download_url(self, object_key: str, expires_seconds: int) -> str:
        self._validate_key_domain(object_key)
        expires = min(max(expires_seconds, 30), 300)
        return await asyncio.to_thread(
            self.client.generate_presigned_url,
            "get_object",
            Params={"Bucket": self.bucket, "Key": object_key},
            ExpiresIn=expires,
            HttpMethod="GET",
        )

    async def delete_object(self, object_key: str) -> None:
        self._validate_key_domain(object_key)
        await asyncio.to_thread(self._call, "delete_object", Bucket=self.bucket, Key=object_key)


class MemoryVerificationStorage(VerificationStorageProtocol):
    """In-memory verification storage for testing."""
    provider = "mock"

    def __init__(self):
        self.objects: dict[str, tuple[str, bytes]] = {}
        self.deleted_keys: list[str] = []

    def _validate_key_domain(self, object_key: str) -> None:
        if not object_key.startswith("verification/"):
            raise ValueError("Verification media key must reside in the private 'verification/' namespace.")

    async def create_upload_url(self, object_key: str, content_type: str, size_bytes: int, expires_seconds: int) -> str:
        self._validate_key_domain(object_key)
        return f"https://private-verify-storage.invalid/upload/{object_key}?expires={expires_seconds}"

    async def inspect_object(self, object_key: str) -> tuple[StoredVerificationObject, bytes]:
        self._validate_key_domain(object_key)
        if object_key not in self.objects:
            raise VerificationStorageUnavailable("Object not found in test storage.")
        mime_type, data = self.objects[object_key]
        return StoredVerificationObject(len(data), mime_type), data

    async def create_download_url(self, object_key: str, expires_seconds: int) -> str:
        self._validate_key_domain(object_key)
        if object_key not in self.objects:
            raise VerificationStorageUnavailable("Object not found in test storage.")
        return f"https://private-verify-storage.invalid/download/{object_key}?expires={expires_seconds}"

    async def delete_object(self, object_key: str) -> None:
        self._validate_key_domain(object_key)
        self.deleted_keys.append(object_key)
        self.objects.pop(object_key, None)
