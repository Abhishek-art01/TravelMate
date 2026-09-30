from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from app.core.security import bearer_scheme, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenRequest(BaseModel):
    token: str = Field(..., min_length=10)


@router.post("/verify")
async def verify_token(
    payload: TokenRequest | None = None,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
):
    token = payload.token if payload is not None else credentials.credentials if credentials else None
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "AUTHENTICATION_REQUIRED", "message": "A bearer token is required."}},
        )

    auth_context = await get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))
    return {
        "verified": True,
        "user_id": auth_context["user_id"],
        "role": auth_context["role"],
        "provider": auth_context["provider"],
    }


@router.post("/session")
async def create_session(
    payload: TokenRequest | None = None,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
):
    token = payload.token if payload is not None else credentials.credentials if credentials else None
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_TOKEN", "message": "A bearer token is required."}},
        )

    auth_context = await get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))
    return {
        "status": "session_ready",
        "provider": auth_context["provider"],
        "session_id": str(uuid4()),
        "user_id": auth_context["user_id"],
        "token_length": len(token),
    }
