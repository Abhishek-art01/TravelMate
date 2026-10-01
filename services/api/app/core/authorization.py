from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "user": {"profile.read", "profile.write"},
    "moderator": {"profile.read", "profile.write", "moderation.read", "moderation.action"},
    "support": {"support.read", "support.manage", "users.read"},
    "verification_admin": {
        "verification.read",
        "verification.review",
        "verification.approve",
        "verification.reject",
        "verification.media.read",
    },
    "finance_admin": {"payments.read", "payments.manage"},
    "security_admin": {"security.read", "security.manage", "audit.read"},
    "travel_admin": {"travel.read", "travel.manage", "users.read"},
    "analytics_admin": {"analytics.read"},
    "operations_admin": {"operations.read", "operations.manage", "support.read"},
    "super_admin": {
        "profile.read",
        "profile.write",
        "users.read",
        "users.restrict",
        "users.suspend",
        "verification.read",
        "verification.review",
        "verification.approve",
        "verification.reject",
        "verification.media.read",
        "moderation.read",
        "moderation.action",
        "support.read",
        "support.manage",
        "payments.read",
        "payments.manage",
        "analytics.read",
        "travel.read",
        "travel.manage",
        "operations.read",
        "operations.manage",
        "security.read",
        "security.manage",
        "audit.read",
        "system.manage",
    },
}

ADMIN_ACCESS_PERMISSIONS = frozenset({
    "users.read",
    "users.restrict",
    "users.suspend",
    "verification.read",
    "verification.review",
    "verification.approve",
    "verification.reject",
    "verification.media.read",
    "moderation.read",
    "moderation.action",
    "support.read",
    "support.manage",
    "payments.read",
    "payments.manage",
    "analytics.read",
    "security.read",
    "security.manage",
    "audit.read",
    "system.manage",
    "travel.read",
    "travel.manage",
    "operations.read",
    "operations.manage",
})


def get_permissions_for_role(role: str | None, explicit_permissions: set[str] | list[str] | None = None) -> set[str]:
    resolved = set(explicit_permissions or [])
    normalized = (role or "user").lower()
    resolved.update(ROLE_PERMISSIONS.get(normalized, ROLE_PERMISSIONS["user"]))
    return {permission for permission in resolved if permission}


def require_permission(permission: str):
    async def permission_dependency(current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
        perms = set(current_user.get("permissions", []))
        if permission not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": f"Permission '{permission}' is required for this operation.",
                    }
                },
            )
        return current_user

    return permission_dependency


def require_any_permission(*permissions: str):
    required_permissions = set(permissions)

    async def permission_dependency(current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
        if not required_permissions.intersection(current_user.get("permissions", [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "You do not have permission to access the administration console.",
                    }
                },
            )
        return current_user

    return permission_dependency
