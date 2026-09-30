from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user

router = APIRouter(prefix="/verification", tags=["verification"])


@router.get("/status")
async def get_verification_status(current_user: dict = Depends(get_current_user)):
    return {
        "user_id": current_user["user_id"],
        "verification_status": "not_started",
        "required_checks": [
            "email_verification",
            "selfie_verification",
            "government_id_verification",
            "video_verification",
        ],
    }


@router.post("/submit")
async def submit_verification(current_user: dict = Depends(get_current_user)):
    return {
        "user_id": current_user["user_id"],
        "status": "submitted",
        "message": "Verification submission received. Sensitive documents are handled in the private verification store.",
    }


@router.patch("/admin/{verification_id}/status")
async def update_verification_status(verification_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in {"verification_admin", "super_admin", "security_admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "Only verification admins may change verification status.",
                }
            },
        )

    return {
        "verification_id": verification_id,
        "status": "pending_review",
        "updated_by": current_user["user_id"],
    }
