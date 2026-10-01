from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.models.account import UserAccount
from app.models.audit import AuditLog
from app.models.profile import UserProfile
from app.models.user import User
from app.models.verification import (
    VerificationAttempt,
    VerificationEvent,
    VerificationMedia,
    VerificationRecord,
)
from app.schemas.verification import (
    AdminSignedMediaUrlResponse,
    AdminVerificationAttemptRead,
    AdminVerificationCaseDetail,
    AdminVerificationCaseSummary,
    AdminVerificationEventRead,
    AdminVerificationQueueResponse,
    CheckItemStatus,
    RequestMediaUpload,
    UserVerificationOverview,
    VerificationMediaRead,
    VerificationSessionResponse,
    VerificationStatusResponse,
    VerificationUploadCreated,
)
from app.services.verification_provider import (
    InvalidWebhookSignatureError,
    SessionInitParams,
    VerificationProvider,
    VerificationProviderNotConfiguredError,
)
from app.services.verification_state import (
    InvalidStateTransitionError,
    VerificationStatus,
    VerificationType,
    can_transition,
    validate_transition,
)
from app.services.verification_storage import (
    VerificationStorageProtocol,
    VerificationStorageUnavailable,
)

ALLOWED_VERIFICATION_TYPES = {
    VerificationType.SELFIE,
    VerificationType.GOVERNMENT_ID,
    VerificationType.VIDEO,
}

SUPPORTED_MEDIA_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "video/mp4": "mp4",
}


def _http_error(code: str, message: str, http_status: int) -> HTTPException:
    return HTTPException(status_code=http_status, detail={"error": {"code": code, "message": message}})


class VerificationService:
    def __init__(
        self,
        provider: VerificationProvider,
        storage: VerificationStorageProtocol,
        settings: Settings | None = None,
    ):
        self.provider = provider
        self.storage = storage
        self.settings = settings or get_settings()

    # ------------------------------------------------------------------
    # Audit Helpers
    # ------------------------------------------------------------------

    async def _record_event(
        self,
        session: AsyncSession,
        verification_id: str,
        user_id: str,
        event_type: str,
        actor_type: str = "user",
        actor_id: str | None = None,
        request_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        now = datetime.now(UTC)
        details_str = json.dumps(details) if details else None

        # 1. Scoped verification event
        event = VerificationEvent(
            id=str(uuid4()),
            verification_id=verification_id,
            user_id=user_id,
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            request_id=request_id,
            details=details_str,
            created_at=now,
        )
        session.add(event)

        # 2. Global system audit log
        audit = AuditLog(
            id=str(uuid4()),
            user_id=user_id,
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            details=details_str,
            created_at=now.isoformat(),
        )
        session.add(audit)

    # ------------------------------------------------------------------
    # User Overview
    # ------------------------------------------------------------------

    async def get_user_overview(self, session: AsyncSession, user: User) -> UserVerificationOverview:
        # Check UserAccount for email and social signals
        account_stmt = select(UserAccount).where(UserAccount.user_id == user.id)
        account_res = await session.execute(account_stmt)
        accounts = list(account_res.scalars().all())

        email_status = VerificationStatus.NOT_STARTED
        email_details = "Email unverified"
        social_status = VerificationStatus.NOT_STARTED
        social_details = "No social provider connected"

        for acc in accounts:
            if acc.email_verified:
                email_status = VerificationStatus.VERIFIED
                email_details = f"Verified via {acc.provider}"
            if acc.provider in {"google", "apple", "facebook", "linkedin", "github", "x"}:
                social_status = VerificationStatus.VERIFIED
                social_details = f"Identity signal linked with {acc.provider}"

        # Check VerificationRecord for selfie, government_id, video
        records_stmt = select(VerificationRecord).where(VerificationRecord.user_id == user.id)
        records_res = await session.execute(records_stmt)
        records = {r.v_type: r for r in records_res.scalars().all()}

        max_attempts = self.settings.verification_max_attempts
        checks: dict[str, CheckItemStatus] = {
            "email": CheckItemStatus(
                type="email",
                status=str(email_status),
                details=email_details,
            ),
            "social": CheckItemStatus(
                type="social",
                status=str(social_status),
                details=social_details,
            ),
        }

        overall_verified = bool(user.is_verified)
        overall_status = VerificationStatus.NOT_STARTED
        if overall_verified:
            overall_status = VerificationStatus.VERIFIED

        for v_type in [VerificationType.SELFIE, VerificationType.GOVERNMENT_ID, VerificationType.VIDEO]:
            record = records.get(v_type)
            if record:
                attempts_used = record.attempt_number
                attempts_rem = max(0, max_attempts - attempts_used)
                checks[v_type] = CheckItemStatus(
                    type=v_type,
                    status=record.status,
                    updated_at=record.updated_at,
                    attempts_remaining=attempts_rem,
                    details=record.review_decision_reason,
                )
                if not overall_verified and record.status in {
                    VerificationStatus.IN_REVIEW,
                    VerificationStatus.SUBMITTED,
                    VerificationStatus.IN_PROGRESS,
                    VerificationStatus.PENDING,
                }:
                    overall_status = record.status
            else:
                checks[v_type] = CheckItemStatus(
                    type=v_type,
                    status=VerificationStatus.NOT_STARTED,
                    attempts_remaining=max_attempts,
                )

        return UserVerificationOverview(
            user_id=user.id,
            overall_status=str(overall_status),
            is_verified=overall_verified,
            checks=checks,
            verification_status=str(overall_status),
            required_checks=[
                "email_verification",
                "selfie_verification",
                "government_id_verification",
                "video_verification",
            ],
        )

    # ------------------------------------------------------------------
    # User Verification Start & Sessions
    # ------------------------------------------------------------------

    async def start_verification(
        self,
        session: AsyncSession,
        user: User,
        verification_type: str,
        redirect_url: str | None = None,
        request_id: str | None = None,
    ) -> VerificationSessionResponse:
        norm_type = verification_type.lower().strip()
        if norm_type not in ALLOWED_VERIFICATION_TYPES:
            raise _http_error(
                "INVALID_VERIFICATION_TYPE",
                f"Verification type '{verification_type}' is not supported for manual verification sessions.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # 1. Existing record check
        record_stmt = select(VerificationRecord).where(
            VerificationRecord.user_id == user.id,
            VerificationRecord.category == norm_type,
        )
        record_res = await session.execute(record_stmt)
        record = record_res.scalar_one_or_none()

        if record and record.status == VerificationStatus.VERIFIED:
            raise _http_error(
                "VERIFICATION_ALREADY_VERIFIED",
                f"{norm_type.capitalize()} verification is already verified for this account.",
                status.HTTP_409_CONFLICT,
            )

        active_statuses = {
            VerificationStatus.PENDING,
            VerificationStatus.IN_PROGRESS,
            VerificationStatus.SUBMITTED,
            VerificationStatus.IN_REVIEW,
        }
        if record and record.status in active_statuses:
            raise _http_error(
                "VERIFICATION_ALREADY_ACTIVE",
                f"A verification session for {norm_type} is already active.",
                status.HTTP_409_CONFLICT,
            )

        # 2. Attempt limits check
        attempts_count = await session.scalar(
            select(func.count())
            .select_from(VerificationAttempt)
            .where(
                VerificationAttempt.user_id == user.id,
                VerificationAttempt.verification_id == record.id if record else False,
            )
        ) or 0

        if attempts_count >= self.settings.verification_max_attempts:
            raise _http_error(
                "VERIFICATION_LIMIT_REACHED",
                "Maximum verification attempts reached for this check. Please contact support.",
                status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # 3. Provider initialization
        now = datetime.now(UTC)
        ttl = self.settings.verification_session_ttl_seconds
        expires_at = now + timedelta(seconds=ttl)
        verification_id = record.id if record else str(uuid4())
        attempt_number = attempts_count + 1

        try:
            provider_result = await self.provider.create_verification_session(
                SessionInitParams(
                    verification_id=verification_id,
                    user_id=user.id,
                    verification_type=norm_type,
                    attempt_number=attempt_number,
                    redirect_url=redirect_url,
                )
            )
        except VerificationProviderNotConfiguredError as exc:
            raise _http_error(
                "VERIFICATION_PROVIDER_NOT_CONFIGURED",
                "Identity verification is temporarily unavailable because no provider is configured.",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from exc

        # 4. Save/Update record
        if not record:
            record = VerificationRecord(
                id=verification_id,
                user_id=user.id,
                category=norm_type,
                verification_type=norm_type,
                status=VerificationStatus.PENDING,
                provider=self.provider.provider_name,
                provider_reference=provider_result.session_id,
                attempt_number=attempt_number,
                expires_at=expires_at,
                created_at=now.isoformat(),
                updated_at=now.isoformat(),
            )
            session.add(record)
        else:
            validate_transition(record.status, VerificationStatus.PENDING)
            record.status = VerificationStatus.PENDING
            record.provider = self.provider.provider_name
            record.provider_reference = provider_result.session_id
            record.attempt_number = attempt_number
            record.expires_at = expires_at
            record.updated_at = now.isoformat()

        # 5. Record attempt
        attempt = VerificationAttempt(
            id=str(uuid4()),
            verification_id=verification_id,
            user_id=user.id,
            attempt_number=attempt_number,
            status=VerificationStatus.PENDING,
            provider=self.provider.provider_name,
            provider_session_id=provider_result.session_id,
            created_at=now,
            updated_at=now,
        )
        session.add(attempt)

        # 6. Audit event
        await self._record_event(
            session=session,
            verification_id=verification_id,
            user_id=user.id,
            event_type="VERIFICATION_STARTED",
            actor_type="user",
            actor_id=user.id,
            request_id=request_id,
            details={"verification_type": norm_type, "attempt_number": attempt_number},
        )

        await session.commit()
        await session.refresh(record)

        return VerificationSessionResponse(
            verification_id=record.id,
            verification_type=norm_type,
            status=record.status,
            attempt_number=record.attempt_number,
            session_url=provider_result.session_url,
            expires_at=expires_at.isoformat(),
        )

    # ------------------------------------------------------------------
    # User Verification Status & Actions
    # ------------------------------------------------------------------

    async def get_user_verification(
        self, session: AsyncSession, user: User, verification_id: str
    ) -> VerificationStatusResponse:
        record_stmt = select(VerificationRecord).where(
            VerificationRecord.id == verification_id,
            VerificationRecord.user_id == user.id,
        )
        record_res = await session.execute(record_stmt)
        record = record_res.scalar_one_or_none()
        if not record:
            raise _http_error("VERIFICATION_NOT_FOUND", "Verification record not found.", status.HTTP_404_NOT_FOUND)

        return VerificationStatusResponse(
            verification_id=record.id,
            verification_type=record.v_type,
            status=record.status,
            attempt_number=record.attempt_number,
            submitted_at=record.submitted_at.isoformat() if record.submitted_at else None,
            reviewed_at=record.reviewed_at.isoformat() if record.reviewed_at else None,
            updated_at=record.updated_at,
        )

    async def request_media_upload(
        self,
        session: AsyncSession,
        user: User,
        verification_id: str,
        payload: RequestMediaUpload,
    ) -> VerificationUploadCreated:
        record_stmt = select(VerificationRecord).where(
            VerificationRecord.id == verification_id,
            VerificationRecord.user_id == user.id,
        )
        record_res = await session.execute(record_stmt)
        record = record_res.scalar_one_or_none()
        if not record:
            raise _http_error("VERIFICATION_NOT_FOUND", "Verification record not found.", status.HTTP_404_NOT_FOUND)

        if record.status not in {VerificationStatus.PENDING, VerificationStatus.IN_PROGRESS}:
            raise _http_error(
                "VERIFICATION_NOT_ACCEPTING_UPLOADS",
                f"Cannot upload media for verification in state '{record.status}'.",
                status.HTTP_409_CONFLICT,
            )

        ext = SUPPORTED_MEDIA_EXTENSIONS.get(payload.mime_type)
        if not ext:
            raise _http_error(
                "UNSUPPORTED_MEDIA_TYPE",
                f"MIME type '{payload.mime_type}' is not supported.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        media_id = str(uuid4())
        # Private server-side key generation strictly isolated from profile media!
        object_key = f"verification/{user.id}/{verification_id}/{media_id}.{ext}"
        now = datetime.now(UTC)
        ttl = self.settings.verification_signed_url_ttl_seconds

        # Retention period calculation
        retention_days = self.settings.verification_id_retention_days
        if payload.media_type == "selfie":
            retention_days = self.settings.verification_selfie_retention_days
        elif payload.media_type == "video":
            retention_days = self.settings.verification_video_retention_days
        retention_expires_at = now + timedelta(days=retention_days)

        try:
            upload_url = await self.storage.create_upload_url(
                object_key=object_key,
                content_type=payload.mime_type,
                size_bytes=payload.size_bytes,
                expires_seconds=ttl,
            )
        except VerificationStorageUnavailable as exc:
            raise _http_error(
                "VERIFICATION_STORAGE_UNAVAILABLE",
                "Secure verification storage is currently unavailable.",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from exc

        media = VerificationMedia(
            id=media_id,
            verification_id=verification_id,
            user_id=user.id,
            media_type=payload.media_type,
            storage_provider=self.storage.provider,
            object_key=object_key,
            mime_type=payload.mime_type,
            size_bytes=payload.size_bytes,
            created_at=now,
            retention_expires_at=retention_expires_at,
        )
        session.add(media)

        # Transition to in_progress if still pending
        if record.status == VerificationStatus.PENDING:
            record.status = VerificationStatus.IN_PROGRESS
            record.updated_at = now.isoformat()

        await session.commit()

        return VerificationUploadCreated(
            media_id=media_id,
            upload_url=upload_url,
            expires_at=(now + timedelta(seconds=ttl)).isoformat(),
            required_headers={"Content-Type": payload.mime_type},
        )

    async def complete_media_upload(
        self,
        session: AsyncSession,
        user: User,
        verification_id: str,
        media_id: str,
    ) -> VerificationMediaRead:
        media_stmt = select(VerificationMedia).where(
            VerificationMedia.id == media_id,
            VerificationMedia.verification_id == verification_id,
            VerificationMedia.user_id == user.id,
            VerificationMedia.deleted_at.is_(None),
        )
        media_res = await session.execute(media_stmt)
        media = media_res.scalar_one_or_none()
        if not media:
            raise _http_error("MEDIA_NOT_FOUND", "Verification media item not found.", status.HTTP_404_NOT_FOUND)

        try:
            stored_obj, _ = await self.storage.inspect_object(media.object_key)
        except VerificationStorageUnavailable as exc:
            raise _http_error(
                "VERIFICATION_STORAGE_UNAVAILABLE",
                "Unable to verify stored media in private storage.",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from exc

        return VerificationMediaRead(
            media_id=media.id,
            media_type=media.media_type,
            mime_type=media.mime_type,
            size_bytes=stored_obj.size_bytes or media.size_bytes,
            created_at=media.created_at.isoformat(),
        )

    async def submit_verification(
        self,
        session: AsyncSession,
        user: User,
        verification_id: str,
        request_id: str | None = None,
    ) -> VerificationStatusResponse:
        record_stmt = select(VerificationRecord).where(
            VerificationRecord.id == verification_id,
            VerificationRecord.user_id == user.id,
        )
        record_res = await session.execute(record_stmt)
        record = record_res.scalar_one_or_none()
        if not record:
            raise _http_error("VERIFICATION_NOT_FOUND", "Verification record not found.", status.HTTP_404_NOT_FOUND)

        try:
            validate_transition(record.status, VerificationStatus.SUBMITTED)
        except InvalidStateTransitionError as exc:
            raise _http_error(
                "INVALID_STATE_TRANSITION",
                f"Cannot submit verification from state '{record.status}'.",
                status.HTTP_409_CONFLICT,
            ) from exc

        now = datetime.now(UTC)
        record.status = VerificationStatus.SUBMITTED
        record.submitted_at = now
        record.updated_at = now.isoformat()

        await self._record_event(
            session=session,
            verification_id=verification_id,
            user_id=user.id,
            event_type="VERIFICATION_SUBMITTED",
            actor_type="user",
            actor_id=user.id,
            request_id=request_id,
            details={"verification_type": record.v_type, "attempt_number": record.attempt_number},
        )

        await session.commit()
        await session.refresh(record)

        return VerificationStatusResponse(
            verification_id=record.id,
            verification_type=record.v_type,
            status=record.status,
            attempt_number=record.attempt_number,
            submitted_at=record.submitted_at.isoformat(),
            reviewed_at=None,
            updated_at=record.updated_at,
        )

    async def cancel_verification(
        self,
        session: AsyncSession,
        user: User,
        verification_id: str,
        request_id: str | None = None,
    ) -> VerificationStatusResponse:
        record_stmt = select(VerificationRecord).where(
            VerificationRecord.id == verification_id,
            VerificationRecord.user_id == user.id,
        )
        record_res = await session.execute(record_stmt)
        record = record_res.scalar_one_or_none()
        if not record:
            raise _http_error("VERIFICATION_NOT_FOUND", "Verification record not found.", status.HTTP_404_NOT_FOUND)

        try:
            validate_transition(record.status, VerificationStatus.CANCELLED)
        except InvalidStateTransitionError as exc:
            raise _http_error(
                "INVALID_STATE_TRANSITION",
                f"Cannot cancel verification from state '{record.status}'.",
                status.HTTP_409_CONFLICT,
            ) from exc

        now = datetime.now(UTC)
        old_status = record.status
        record.status = VerificationStatus.CANCELLED
        record.updated_at = now.isoformat()

        await self._record_event(
            session=session,
            verification_id=verification_id,
            user_id=user.id,
            event_type="VERIFICATION_STATUS_CHANGED",
            actor_type="user",
            actor_id=user.id,
            request_id=request_id,
            details={"from": old_status, "to": record.status},
        )

        await session.commit()
        await session.refresh(record)

        return VerificationStatusResponse(
            verification_id=record.id,
            verification_type=record.v_type,
            status=record.status,
            attempt_number=record.attempt_number,
            submitted_at=record.submitted_at.isoformat() if record.submitted_at else None,
            reviewed_at=None,
            updated_at=record.updated_at,
        )

    # ------------------------------------------------------------------
    # Admin Operations
    # ------------------------------------------------------------------

    async def list_admin_queue(
        self,
        session: AsyncSession,
        status_filter: str | None = None,
        type_filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AdminVerificationQueueResponse:
        query = select(VerificationRecord, UserProfile.display_name, UserAccount.email).outerjoin(
            UserProfile, UserProfile.user_id == VerificationRecord.user_id
        ).outerjoin(
            UserAccount, UserAccount.user_id == VerificationRecord.user_id
        )

        if status_filter and status_filter.lower() != "all":
            query = query.where(VerificationRecord.status == status_filter.lower())
        if type_filter and type_filter.lower() != "all":
            query = query.where(VerificationRecord.category == type_filter.lower())

        total = await session.scalar(
            select(func.count()).select_from(query.subquery())
        ) or 0

        query = query.order_by(VerificationRecord.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(query)

        items: list[AdminVerificationCaseSummary] = []
        for rec, display_name, email in result.all():
            items.append(
                AdminVerificationCaseSummary(
                    id=rec.id,
                    user_id=rec.user_id,
                    user_display_name=display_name,
                    user_email=email,
                    verification_type=rec.v_type,
                    status=rec.status,
                    attempt_number=rec.attempt_number,
                    submitted_at=rec.submitted_at.isoformat() if rec.submitted_at else None,
                    reviewed_at=rec.reviewed_at.isoformat() if rec.reviewed_at else None,
                    reviewed_by=rec.reviewed_by,
                )
            )

        return AdminVerificationQueueResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_admin_case_detail(
        self, session: AsyncSession, verification_id: str, admin_user_id: str
    ) -> AdminVerificationCaseDetail:
        record_stmt = (
            select(VerificationRecord, UserProfile.display_name, UserAccount.email)
            .outerjoin(UserProfile, UserProfile.user_id == VerificationRecord.user_id)
            .outerjoin(UserAccount, UserAccount.user_id == VerificationRecord.user_id)
            .where(VerificationRecord.id == verification_id)
        )
        record_res = await session.execute(record_stmt)
        row = record_res.first()
        if not row:
            raise _http_error("VERIFICATION_NOT_FOUND", "Verification case not found.", status.HTTP_404_NOT_FOUND)

        rec, display_name, email = row

        # Fetch attempts
        attempts_res = await session.execute(
            select(VerificationAttempt)
            .where(VerificationAttempt.verification_id == verification_id)
            .order_by(VerificationAttempt.attempt_number.asc())
        )
        attempts = [
            AdminVerificationAttemptRead(
                id=a.id,
                attempt_number=a.attempt_number,
                status=a.status,
                failure_reason=a.failure_reason,
                created_at=a.created_at.isoformat(),
            )
            for a in attempts_res.scalars().all()
        ]

        # Fetch events
        events_res = await session.execute(
            select(VerificationEvent)
            .where(VerificationEvent.verification_id == verification_id)
            .order_by(VerificationEvent.created_at.asc())
        )
        events = [
            AdminVerificationEventRead(
                id=e.id,
                event_type=e.event_type,
                actor_type=e.actor_type,
                actor_id=e.actor_id,
                details=e.details,
                created_at=e.created_at.isoformat(),
            )
            for e in events_res.scalars().all()
        ]

        # Fetch media metadata (NO presigned URLs generated in advance)
        media_res = await session.execute(
            select(VerificationMedia)
            .where(
                VerificationMedia.verification_id == verification_id,
                VerificationMedia.deleted_at.is_(None),
            )
        )
        media = [
            VerificationMediaRead(
                media_id=m.id,
                media_type=m.media_type,
                mime_type=m.mime_type,
                size_bytes=m.size_bytes,
                created_at=m.created_at.isoformat(),
            )
            for m in media_res.scalars().all()
        ]

        # Record audit log that the verification case was viewed
        await self._record_event(
            session=session,
            verification_id=verification_id,
            user_id=rec.user_id,
            event_type="VERIFICATION_VIEWED",
            actor_type="admin",
            actor_id=admin_user_id,
            details={"case_id": verification_id},
        )
        await session.commit()

        return AdminVerificationCaseDetail(
            id=rec.id,
            user_id=rec.user_id,
            user_display_name=display_name,
            user_email=email,
            verification_type=rec.v_type,
            status=rec.status,
            attempt_number=rec.attempt_number,
            submitted_at=rec.submitted_at.isoformat() if rec.submitted_at else None,
            reviewed_at=rec.reviewed_at.isoformat() if rec.reviewed_at else None,
            reviewed_by=rec.reviewed_by,
            review_decision_reason=rec.review_decision_reason,
            created_at=rec.created_at,
            updated_at=rec.updated_at,
            attempts=attempts,
            events=events,
            media=media,
        )

    async def get_admin_signed_media_url(
        self,
        session: AsyncSession,
        verification_id: str,
        media_id: str,
        admin_user_id: str,
    ) -> AdminSignedMediaUrlResponse:
        media_stmt = select(VerificationMedia).where(
            VerificationMedia.id == media_id,
            VerificationMedia.verification_id == verification_id,
            VerificationMedia.deleted_at.is_(None),
        )
        media_res = await session.execute(media_stmt)
        media = media_res.scalar_one_or_none()
        if not media:
            raise _http_error("MEDIA_NOT_FOUND", "Verification media document not found.", status.HTTP_404_NOT_FOUND)

        ttl = self.settings.verification_signed_url_ttl_seconds
        try:
            download_url = await self.storage.create_download_url(media.object_key, ttl)
        except VerificationStorageUnavailable as exc:
            raise _http_error(
                "VERIFICATION_STORAGE_UNAVAILABLE",
                "Secure storage could not generate access URL.",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from exc

        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=ttl)

        # Audit media access
        await self._record_event(
            session=session,
            verification_id=verification_id,
            user_id=media.user_id,
            event_type="VERIFICATION_MEDIA_ACCESSED",
            actor_type="admin",
            actor_id=admin_user_id,
            details={"media_id": media.id, "media_type": media.media_type},
        )
        await session.commit()

        return AdminSignedMediaUrlResponse(
            media_id=media.id,
            download_url=download_url,
            expires_at=expires_at.isoformat(),
        )

    async def start_admin_review(
        self, session: AsyncSession, verification_id: str, admin_user_id: str
    ) -> AdminVerificationCaseSummary:
        record_stmt = select(VerificationRecord).where(VerificationRecord.id == verification_id)
        record_res = await session.execute(record_stmt)
        rec = record_res.scalar_one_or_none()
        if not rec:
            raise _http_error("VERIFICATION_NOT_FOUND", "Verification case not found.", status.HTTP_404_NOT_FOUND)

        try:
            validate_transition(rec.status, VerificationStatus.IN_REVIEW)
        except InvalidStateTransitionError as exc:
            raise _http_error(
                "INVALID_STATE_TRANSITION",
                f"Cannot start review from state '{rec.status}'.",
                status.HTTP_409_CONFLICT,
            ) from exc

        now = datetime.now(UTC)
        rec.status = VerificationStatus.IN_REVIEW
        rec.reviewed_by = admin_user_id
        rec.updated_at = now.isoformat()

        await self._record_event(
            session=session,
            verification_id=verification_id,
            user_id=rec.user_id,
            event_type="VERIFICATION_REVIEW_STARTED",
            actor_type="admin",
            actor_id=admin_user_id,
        )
        await session.commit()

        return AdminVerificationCaseSummary(
            id=rec.id,
            user_id=rec.user_id,
            verification_type=rec.v_type,
            status=rec.status,
            attempt_number=rec.attempt_number,
            submitted_at=rec.submitted_at.isoformat() if rec.submitted_at else None,
            reviewed_at=rec.reviewed_at.isoformat() if rec.reviewed_at else None,
            reviewed_by=rec.reviewed_by,
        )

    async def admin_approve(
        self,
        session: AsyncSession,
        verification_id: str,
        admin_user_id: str,
        reason: str | None = None,
    ) -> AdminVerificationCaseSummary:
        record_stmt = select(VerificationRecord).where(VerificationRecord.id == verification_id)
        record_res = await session.execute(record_stmt)
        rec = record_res.scalar_one_or_none()
        if not rec:
            raise _http_error("VERIFICATION_NOT_FOUND", "Verification case not found.", status.HTTP_404_NOT_FOUND)

        try:
            validate_transition(rec.status, VerificationStatus.VERIFIED)
        except InvalidStateTransitionError as exc:
            raise _http_error(
                "INVALID_STATE_TRANSITION",
                f"Cannot approve verification from state '{rec.status}'.",
                status.HTTP_409_CONFLICT,
            ) from exc

        now = datetime.now(UTC)
        rec.status = VerificationStatus.VERIFIED
        rec.reviewed_at = now
        rec.reviewed_by = admin_user_id
        rec.review_decision_reason = reason or "Approved by admin review."
        rec.updated_at = now.isoformat()

        # Update user is_verified = True when government_id or selfie verification is approved
        user_stmt = select(User).where(User.id == rec.user_id)
        user_res = await session.execute(user_stmt)
        user = user_res.scalar_one_or_none()
        if user:
            user.is_verified = True
            user.updated_at = now.isoformat()

        await self._record_event(
            session=session,
            verification_id=verification_id,
            user_id=rec.user_id,
            event_type="VERIFICATION_APPROVED",
            actor_type="admin",
            actor_id=admin_user_id,
            details={"reason": rec.review_decision_reason},
        )
        await session.commit()

        return AdminVerificationCaseSummary(
            id=rec.id,
            user_id=rec.user_id,
            verification_type=rec.v_type,
            status=rec.status,
            attempt_number=rec.attempt_number,
            submitted_at=rec.submitted_at.isoformat() if rec.submitted_at else None,
            reviewed_at=rec.reviewed_at.isoformat(),
            reviewed_by=rec.reviewed_by,
        )

    async def admin_reject(
        self,
        session: AsyncSession,
        verification_id: str,
        admin_user_id: str,
        reason: str,
    ) -> AdminVerificationCaseSummary:
        if not reason or not reason.strip():
            raise _http_error("REASON_REQUIRED", "A reason is required to reject verification.", status.HTTP_422_UNPROCESSABLE_ENTITY)

        record_stmt = select(VerificationRecord).where(VerificationRecord.id == verification_id)
        record_res = await session.execute(record_stmt)
        rec = record_res.scalar_one_or_none()
        if not rec:
            raise _http_error("VERIFICATION_NOT_FOUND", "Verification case not found.", status.HTTP_404_NOT_FOUND)

        try:
            validate_transition(rec.status, VerificationStatus.REJECTED)
        except InvalidStateTransitionError as exc:
            raise _http_error(
                "INVALID_STATE_TRANSITION",
                f"Cannot reject verification from state '{rec.status}'.",
                status.HTTP_409_CONFLICT,
            ) from exc

        now = datetime.now(UTC)
        rec.status = VerificationStatus.REJECTED
        rec.reviewed_at = now
        rec.reviewed_by = admin_user_id
        rec.review_decision_reason = reason.strip()
        rec.updated_at = now.isoformat()

        await self._record_event(
            session=session,
            verification_id=verification_id,
            user_id=rec.user_id,
            event_type="VERIFICATION_REJECTED",
            actor_type="admin",
            actor_id=admin_user_id,
            details={"reason": rec.review_decision_reason},
        )
        await session.commit()

        return AdminVerificationCaseSummary(
            id=rec.id,
            user_id=rec.user_id,
            verification_type=rec.v_type,
            status=rec.status,
            attempt_number=rec.attempt_number,
            submitted_at=rec.submitted_at.isoformat() if rec.submitted_at else None,
            reviewed_at=rec.reviewed_at.isoformat(),
            reviewed_by=rec.reviewed_by,
        )

    async def admin_request_action(
        self,
        session: AsyncSession,
        verification_id: str,
        admin_user_id: str,
        reason: str,
    ) -> AdminVerificationCaseSummary:
        if not reason or not reason.strip():
            raise _http_error("REASON_REQUIRED", "Action guidance is required to request changes.", status.HTTP_422_UNPROCESSABLE_ENTITY)

        record_stmt = select(VerificationRecord).where(VerificationRecord.id == verification_id)
        record_res = await session.execute(record_stmt)
        rec = record_res.scalar_one_or_none()
        if not rec:
            raise _http_error("VERIFICATION_NOT_FOUND", "Verification case not found.", status.HTTP_404_NOT_FOUND)

        try:
            validate_transition(rec.status, VerificationStatus.REQUIRES_ACTION)
        except InvalidStateTransitionError as exc:
            raise _http_error(
                "INVALID_STATE_TRANSITION",
                f"Cannot request action from state '{rec.status}'.",
                status.HTTP_409_CONFLICT,
            ) from exc

        now = datetime.now(UTC)
        rec.status = VerificationStatus.REQUIRES_ACTION
        rec.reviewed_at = now
        rec.reviewed_by = admin_user_id
        rec.review_decision_reason = reason.strip()
        rec.updated_at = now.isoformat()

        await self._record_event(
            session=session,
            verification_id=verification_id,
            user_id=rec.user_id,
            event_type="VERIFICATION_STATUS_CHANGED",
            actor_type="admin",
            actor_id=admin_user_id,
            details={"action": "requires_action", "reason": rec.review_decision_reason},
        )
        await session.commit()

        return AdminVerificationCaseSummary(
            id=rec.id,
            user_id=rec.user_id,
            verification_type=rec.v_type,
            status=rec.status,
            attempt_number=rec.attempt_number,
            submitted_at=rec.submitted_at.isoformat() if rec.submitted_at else None,
            reviewed_at=rec.reviewed_at.isoformat(),
            reviewed_by=rec.reviewed_by,
        )

    # ------------------------------------------------------------------
    # Provider Webhooks (Idempotent & Authenticated)
    # ------------------------------------------------------------------

    async def handle_provider_webhook(
        self,
        session: AsyncSession,
        provider_name: str,
        headers: dict[str, str],
        raw_body: bytes,
    ) -> dict[str, Any]:
        if provider_name != self.provider.provider_name:
            raise _http_error(
                "PROVIDER_MISMATCH",
                f"Configured provider '{self.provider.provider_name}' does not match webhook path '{provider_name}'.",
                status.HTTP_400_BAD_REQUEST,
            )

        try:
            webhook_res = await self.provider.handle_webhook(headers, raw_body)
        except InvalidWebhookSignatureError as exc:
            raise _http_error("INVALID_SIGNATURE", str(exc), status.HTTP_401_UNAUTHORIZED) from exc
        except Exception as exc:
            raise _http_error("WEBHOOK_PROCESSING_FAILED", str(exc), status.HTTP_400_BAD_REQUEST) from exc

        # Find verification record
        rec = None
        if webhook_res.verification_id:
            rec_stmt = select(VerificationRecord).where(VerificationRecord.id == webhook_res.verification_id)
            rec = (await session.execute(rec_stmt)).scalar_one_or_none()

        if not rec and webhook_res.provider_session_id:
            rec_stmt = select(VerificationRecord).where(
                VerificationRecord.provider_reference == webhook_res.provider_session_id
            )
            rec = (await session.execute(rec_stmt)).scalar_one_or_none()

        if not rec:
            raise _http_error(
                "VERIFICATION_NOT_FOUND",
                "Webhook event refers to an unknown verification session.",
                status.HTTP_404_NOT_FOUND,
            )

        target_status = webhook_res.new_status
        if not target_status:
            return {"status": "ignored", "reason": "No status transition specified."}

        # Idempotency check: if already at target status, return 200 without duplicate action
        if rec.status == target_status:
            return {"status": "idempotent_ok", "verification_id": rec.id, "current_status": rec.status}

        if not can_transition(rec.status, target_status):
            return {
                "status": "transition_rejected",
                "verification_id": rec.id,
                "current_status": rec.status,
                "target_status": target_status,
            }

        now = datetime.now(UTC)
        old_status = rec.status
        rec.status = target_status
        rec.updated_at = now.isoformat()

        if target_status == VerificationStatus.VERIFIED:
            rec.reviewed_at = now
            user_stmt = select(User).where(User.id == rec.user_id)
            user = (await session.execute(user_stmt)).scalar_one_or_none()
            if user:
                user.is_verified = True
                user.updated_at = now.isoformat()

        await self._record_event(
            session=session,
            verification_id=rec.id,
            user_id=rec.user_id,
            event_type="VERIFICATION_STATUS_CHANGED",
            actor_type="provider",
            actor_id=provider_name,
            details={
                "from": old_status,
                "to": target_status,
                "event_type": webhook_res.event_type,
                "reason": webhook_res.reason,
            },
        )
        await session.commit()

        return {"status": "success", "verification_id": rec.id, "new_status": rec.status}

    # ------------------------------------------------------------------
    # Retention & Deletion Workflows
    # ------------------------------------------------------------------

    async def prune_expired_media(self, session: AsyncSession) -> int:
        now = datetime.now(UTC)
        media_stmt = select(VerificationMedia).where(
            VerificationMedia.deleted_at.is_(None),
            VerificationMedia.retention_expires_at.is_not(None),
            VerificationMedia.retention_expires_at <= now,
        )
        result = await session.execute(media_stmt)
        expired_media = list(result.scalars().all())

        count = 0
        for m in expired_media:
            try:
                await self.storage.delete_object(m.object_key)
            except VerificationStorageUnavailable:
                pass
            m.deleted_at = now
            count += 1
            await self._record_event(
                session=session,
                verification_id=m.verification_id,
                user_id=m.user_id,
                event_type="VERIFICATION_MEDIA_DELETED",
                actor_type="system",
                details={"media_id": m.id, "reason": "retention_policy_expired"},
            )

        await session.commit()
        return count

    async def delete_user_verification_media(
        self,
        session: AsyncSession,
        user_id: str,
        actor_id: str | None = None,
        reason: str = "account_deletion",
    ) -> int:
        now = datetime.now(UTC)
        media_stmt = select(VerificationMedia).where(
            VerificationMedia.user_id == user_id,
            VerificationMedia.deleted_at.is_(None),
        )
        result = await session.execute(media_stmt)
        media_items = list(result.scalars().all())

        count = 0
        for m in media_items:
            try:
                await self.storage.delete_object(m.object_key)
            except VerificationStorageUnavailable:
                pass
            m.deleted_at = now
            count += 1
            await self._record_event(
                session=session,
                verification_id=m.verification_id,
                user_id=m.user_id,
                event_type="VERIFICATION_MEDIA_DELETED",
                actor_type="user" if actor_id == user_id else "system",
                actor_id=actor_id,
                details={"media_id": m.id, "reason": reason},
            )

        await session.commit()
        return count
