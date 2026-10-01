from __future__ import annotations

import asyncio
from functools import cached_property
from typing import Any

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError

from app.config import Settings, get_settings
from app.services.media_storage import MediaStorage, StorageUnavailable, StoredObject


class R2Storage(MediaStorage):
    provider = "r2"

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        required = (
            self.settings.r2_account_id,
            self.settings.r2_bucket,
            self.settings.r2_endpoint,
            self.settings.r2_access_key_id,
            self.settings.r2_secret_access_key,
        )
        if not all(required):
            raise StorageUnavailable("R2 storage is not configured")

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
            raise StorageUnavailable("Object storage request failed") from exc

    async def create_upload_url(self, object_key: str, content_type: str, size_bytes: int, expires_seconds: int) -> str:
        expires = min(max(expires_seconds, 60), 900)
        return await asyncio.to_thread(
            self.client.generate_presigned_url,
            "put_object",
            Params={"Bucket": self.settings.r2_bucket, "Key": object_key, "ContentType": content_type, "ContentLength": size_bytes},
            ExpiresIn=expires,
            HttpMethod="PUT",
        )

    async def inspect_object(self, object_key: str) -> tuple[StoredObject, bytes]:
        head = await asyncio.to_thread(self._call, "head_object", Bucket=self.settings.r2_bucket, Key=object_key)
        response = await asyncio.to_thread(self._call, "get_object", Bucket=self.settings.r2_bucket, Key=object_key)
        data = await asyncio.to_thread(response["Body"].read, self.settings.media_max_profile_photo_size_bytes + 1)
        return StoredObject(int(head.get("ContentLength", 0)), head.get("ContentType")), data

    async def create_download_url(self, object_key: str, expires_seconds: int) -> str:
        expires = min(max(expires_seconds, 60), 900)
        return await asyncio.to_thread(
            self.client.generate_presigned_url,
            "get_object",
            Params={"Bucket": self.settings.r2_bucket, "Key": object_key},
            ExpiresIn=expires,
            HttpMethod="GET",
        )

    async def delete_object(self, object_key: str) -> None:
        await asyncio.to_thread(self._call, "delete_object", Bucket=self.settings.r2_bucket, Key=object_key)
