from __future__ import annotations

from pydantic import BaseModel, Field

# ==========================================
# User-Facing Verification Schemas
# ==========================================

class CheckItemStatus(BaseModel):
    type: str
    status: str
    updated_at: str | None = None
    attempts_remaining: int | None = None
    details: str | None = None


class UserVerificationOverview(BaseModel):
    user_id: str
    overall_status: str
    is_verified: bool
    checks: dict[str, CheckItemStatus]
    verification_status: str
    required_checks: list[str]


class StartVerificationRequest(BaseModel):
    redirect_url: str | None = None


class VerificationSessionResponse(BaseModel):
    verification_id: str
    verification_type: str
    status: str
    attempt_number: int
    session_url: str | None = None
    expires_at: str | None = None


class VerificationStatusResponse(BaseModel):
    verification_id: str
    verification_type: str
    status: str
    attempt_number: int
    submitted_at: str | None = None
    reviewed_at: str | None = None
    updated_at: str


class RequestMediaUpload(BaseModel):
    media_type: str = Field(..., description="selfie, document_front, document_back, video")
    mime_type: str = Field(..., description="image/jpeg, image/png, image/webp, video/mp4")
    size_bytes: int = Field(..., gt=0, le=52_428_800)  # max 50MB for video, 10MB for photos


class VerificationUploadCreated(BaseModel):
    media_id: str
    upload_url: str
    expires_at: str
    required_headers: dict[str, str] = Field(default_factory=dict)


class VerificationMediaRead(BaseModel):
    media_id: str
    media_type: str
    mime_type: str
    size_bytes: int
    created_at: str


# ==========================================
# Admin-Facing Verification Schemas
# ==========================================

class AdminVerificationCaseSummary(BaseModel):
    id: str
    user_id: str
    user_display_name: str | None = None
    user_email: str | None = None
    verification_type: str
    status: str
    attempt_number: int
    submitted_at: str | None = None
    reviewed_at: str | None = None
    reviewed_by: str | None = None


class AdminVerificationQueueResponse(BaseModel):
    items: list[AdminVerificationCaseSummary]
    total: int
    limit: int
    offset: int


class AdminVerificationEventRead(BaseModel):
    id: str
    event_type: str
    actor_type: str
    actor_id: str | None = None
    details: str | None = None
    created_at: str


class AdminVerificationAttemptRead(BaseModel):
    id: str
    attempt_number: int
    status: str
    failure_reason: str | None = None
    created_at: str


class AdminVerificationCaseDetail(BaseModel):
    id: str
    user_id: str
    user_display_name: str | None = None
    user_email: str | None = None
    verification_type: str
    status: str
    attempt_number: int
    submitted_at: str | None = None
    reviewed_at: str | None = None
    reviewed_by: str | None = None
    review_decision_reason: str | None = None
    created_at: str
    updated_at: str
    attempts: list[AdminVerificationAttemptRead] = Field(default_factory=list)
    events: list[AdminVerificationEventRead] = Field(default_factory=list)
    media: list[VerificationMediaRead] = Field(default_factory=list)


class AdminSignedMediaUrlResponse(BaseModel):
    media_id: str
    download_url: str
    expires_at: str


class AdminReviewDecision(BaseModel):
    reason: str | None = None


# Legacy compatibility schema
class VerificationState(BaseModel):
    user_id: str
    category: str
    status: str = "not_started"
    provider: str | None = None
