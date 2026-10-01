from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import require_permission
from app.core.dependencies import get_active_travelmate_user, get_db_session
from app.core.security import get_current_user
from app.core.verification_dependencies import get_verification_service
from app.models.user import User
from app.schemas.verification import (
    AdminReviewDecision,
    AdminSignedMediaUrlResponse,
    AdminVerificationCaseDetail,
    AdminVerificationCaseSummary,
    AdminVerificationQueueResponse,
    RequestMediaUpload,
    StartVerificationRequest,
    UserVerificationOverview,
    VerificationMediaRead,
    VerificationSessionResponse,
    VerificationStatusResponse,
    VerificationUploadCreated,
)
from app.services.verification_service import VerificationService

# Routers
router = APIRouter(prefix="/verification", tags=["verification"])
me_verification_router = APIRouter(prefix="/me/verification", tags=["me-verification"])
admin_verification_router = APIRouter(prefix="/admin/verification", tags=["admin-verification"])
webhook_verification_router = APIRouter(prefix="/webhooks/verification", tags=["webhooks"])

# Dependency aliases
Database = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[User, Depends(get_active_travelmate_user)]
AuthUser = Annotated[dict, Depends(get_current_user)]
Service = Annotated[VerificationService, Depends(get_verification_service)]


# ==============================================================================
# 1. User Verification Endpoints (/api/v1/me/verification and /api/v1/verification)
# ==============================================================================

@router.get("/status", response_model=UserVerificationOverview)
@me_verification_router.get("/status", response_model=UserVerificationOverview)
async def get_verification_status(
    current_user: CurrentUser,
    session: Database,
    service: Service,
):
    """Retrieve the unified verification status across all identity dimensions."""
    return await service.get_user_overview(session, current_user)


@me_verification_router.post("/{type}/start", response_model=VerificationSessionResponse)
async def start_verification(
    type: str,
    current_user: CurrentUser,
    session: Database,
    service: Service,
    payload: StartVerificationRequest | None = None,
    x_request_id: Annotated[str | None, Header()] = None,
):
    """Initialize a verification session with the configured identity provider."""
    redirect_url = payload.redirect_url if payload else None
    return await service.start_verification(
        session=session,
        user=current_user,
        verification_type=type,
        redirect_url=redirect_url,
        request_id=x_request_id,
    )


@me_verification_router.get("/{verification_id}", response_model=VerificationStatusResponse)
async def get_verification(
    verification_id: str,
    current_user: CurrentUser,
    session: Database,
    service: Service,
):
    """Retrieve safe status information for an active or past verification attempt."""
    return await service.get_user_verification(session, current_user, verification_id)


@me_verification_router.post("/{verification_id}/media", response_model=VerificationUploadCreated)
async def request_media_upload(
    verification_id: str,
    payload: RequestMediaUpload,
    current_user: CurrentUser,
    session: Database,
    service: Service,
):
    """Authorize a direct upload of sensitive verification media into private storage."""
    return await service.request_media_upload(session, current_user, verification_id, payload)


@me_verification_router.post(
    "/{verification_id}/media/{media_id}/complete", response_model=VerificationMediaRead
)
async def complete_media_upload(
    verification_id: str,
    media_id: str,
    current_user: CurrentUser,
    session: Database,
    service: Service,
):
    """Confirm the completion of a private verification media upload."""
    return await service.complete_media_upload(session, current_user, verification_id, media_id)


@me_verification_router.post("/{verification_id}/submit", response_model=VerificationStatusResponse)
async def submit_verification(
    verification_id: str,
    current_user: CurrentUser,
    session: Database,
    service: Service,
    x_request_id: Annotated[str | None, Header()] = None,
):
    """Submit uploaded verification documents for processing and review."""
    return await service.submit_verification(session, current_user, verification_id, x_request_id)


@me_verification_router.post("/{verification_id}/cancel", response_model=VerificationStatusResponse)
async def cancel_verification(
    verification_id: str,
    current_user: CurrentUser,
    session: Database,
    service: Service,
    x_request_id: Annotated[str | None, Header()] = None,
):
    """Cancel an active verification process."""
    return await service.cancel_verification(session, current_user, verification_id, x_request_id)


# Legacy endpoints for backwards compatibility
@router.post("/submit")
async def submit_verification_legacy(current_user: AuthUser):
    return {
        "user_id": current_user["user_id"],
        "status": "submitted",
        "message": "Verification submission received. Sensitive documents are handled in the private verification store.",
    }


@router.patch("/admin/{verification_id}/status")
async def update_verification_status_legacy(
    verification_id: str,
    current_user: Annotated[dict, Depends(require_permission("verification.review"))],
):
    return {
        "verification_id": verification_id,
        "status": "pending_review",
        "updated_by": current_user["user_id"],
    }


# ==============================================================================
# 2. Admin Verification Review Endpoints (/api/v1/admin/verification)
# ==============================================================================

@admin_verification_router.get("", response_model=AdminVerificationQueueResponse)
async def list_verification_queue(
    current_admin: Annotated[dict, Depends(require_permission("verification.read"))],
    session: Database,
    service: Service,
    status: Annotated[str | None, Query()] = None,
    type: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """List verification cases in the triage queue."""
    return await service.list_admin_queue(
        session=session,
        status_filter=status,
        type_filter=type,
        limit=limit,
        offset=offset,
    )


@admin_verification_router.get("/{verification_id}", response_model=AdminVerificationCaseDetail)
async def get_verification_case(
    verification_id: str,
    current_admin: Annotated[dict, Depends(require_permission("verification.read"))],
    session: Database,
    service: Service,
):
    """Retrieve full verification case detail without pre-generating media URLs."""
    admin_id = current_admin["user_id"]
    return await service.get_admin_case_detail(session, verification_id, admin_id)


@admin_verification_router.get(
    "/{verification_id}/media/{media_id}/url", response_model=AdminSignedMediaUrlResponse
)
async def get_admin_signed_media_url(
    verification_id: str,
    media_id: str,
    current_admin: Annotated[dict, Depends(require_permission("verification.media.read"))],
    session: Database,
    service: Service,
):
    """Generate a strictly short-lived signed access URL for sensitive verification media."""
    admin_id = current_admin["user_id"]
    return await service.get_admin_signed_media_url(session, verification_id, media_id, admin_id)


@admin_verification_router.post(
    "/{verification_id}/review", response_model=AdminVerificationCaseSummary
)
async def start_case_review(
    verification_id: str,
    current_admin: Annotated[dict, Depends(require_permission("verification.review"))],
    session: Database,
    service: Service,
):
    """Mark a submitted verification case as actively under review."""
    admin_id = current_admin["user_id"]
    return await service.start_admin_review(session, verification_id, admin_id)


@admin_verification_router.post(
    "/{verification_id}/approve", response_model=AdminVerificationCaseSummary
)
async def approve_case(
    verification_id: str,
    current_admin: Annotated[dict, Depends(require_permission("verification.approve"))],
    session: Database,
    service: Service,
    decision: AdminReviewDecision | None = None,
):
    """Approve verification case, updating identity state and user verification badge."""
    admin_id = current_admin["user_id"]
    reason = decision.reason if decision else None
    return await service.admin_approve(session, verification_id, admin_id, reason)


@admin_verification_router.post(
    "/{verification_id}/reject", response_model=AdminVerificationCaseSummary
)
async def reject_case(
    verification_id: str,
    current_admin: Annotated[dict, Depends(require_permission("verification.reject"))],
    session: Database,
    service: Service,
    decision: AdminReviewDecision,
):
    """Reject verification case with mandatory reason recorded in audit log."""
    admin_id = current_admin["user_id"]
    return await service.admin_reject(session, verification_id, admin_id, decision.reason or "")


@admin_verification_router.post(
    "/{verification_id}/request-action", response_model=AdminVerificationCaseSummary
)
async def request_case_action(
    verification_id: str,
    current_admin: Annotated[dict, Depends(require_permission("verification.review"))],
    session: Database,
    service: Service,
    decision: AdminReviewDecision,
):
    """Request additional action or re-upload from traveller with required guidance."""
    admin_id = current_admin["user_id"]
    return await service.admin_request_action(session, verification_id, admin_id, decision.reason or "")


# ==============================================================================
# 3. Provider Webhooks (/api/v1/webhooks/verification/{provider})
# ==============================================================================

@webhook_verification_router.post("/{provider}")
async def handle_provider_webhook(
    provider: str,
    request: Request,
    session: Database,
    service: Service,
):
    """Secure, signature-verified, replay-protected webhook receiver."""
    headers = dict(request.headers)
    raw_body = await request.body()
    return await service.handle_provider_webhook(
        session=session,
        provider_name=provider,
        headers=headers,
        raw_body=raw_body,
    )
