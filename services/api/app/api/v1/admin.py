from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.authorization import require_permission

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/system")
async def admin_system_status(current_user: Annotated[dict, Depends(require_permission("system.manage"))]):
    return {
        "ok": True,
        "service": "system",
        "role": current_user["role"],
        "permissions": sorted(current_user.get("permissions", [])),
    }
