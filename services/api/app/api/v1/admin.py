from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.authorization import ADMIN_ACCESS_PERMISSIONS, require_any_permission, require_permission

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/access")
async def verify_admin_access(
    current_user: Annotated[dict, Depends(require_any_permission(*ADMIN_ACCESS_PERMISSIONS))],
):
    permissions = sorted(set(current_user.get("permissions", [])).intersection(ADMIN_ACCESS_PERMISSIONS))
    return {"authorized": True, "permissions": permissions}


@router.get("/system")
async def admin_system_status(current_user: Annotated[dict, Depends(require_permission("system.manage"))]):
    return {
        "ok": True,
        "service": "system",
        "role": current_user["role"],
        "permissions": sorted(current_user.get("permissions", [])),
    }
