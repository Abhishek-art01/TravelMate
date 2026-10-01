from fastapi.testclient import TestClient

from app.core.authorization import ADMIN_ACCESS_PERMISSIONS
from app.core.security import get_current_user, get_permissions_for_role
from app.main import app

client = TestClient(app)


def test_super_admin_has_all_configured_admin_permissions() -> None:
    assert ADMIN_ACCESS_PERMISSIONS <= get_permissions_for_role("super_admin")


def _request_with_user(user: dict, path: str = "/api/v1/admin/access"):
    async def current_user() -> dict:
        return user

    app.dependency_overrides[get_current_user] = current_user
    try:
        return client.get(path)
    finally:
        app.dependency_overrides.clear()


def test_admin_access_rejects_regular_user() -> None:
    response = _request_with_user({"user_id": "user-1", "role": "user", "permissions": ["profile.read"]})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_admin_access_requires_a_verified_bearer_token() -> None:
    response = client.get("/api/v1/admin/access")

    assert response.status_code == 401


def test_admin_access_allows_scoped_moderator_and_returns_effective_permissions() -> None:
    response = _request_with_user({
        "user_id": "moderator-1",
        "role": "moderator",
        "permissions": ["profile.read", "moderation.read", "moderation.action"],
    })

    assert response.status_code == 200
    assert response.json() == {
        "authorized": True,
        "permissions": ["moderation.action", "moderation.read"],
    }


def test_admin_access_does_not_return_identity_or_claims() -> None:
    response = _request_with_user({
        "user_id": "admin-1",
        "email": "admin@example.com",
        "role": "super_admin",
        "permissions": ["system.manage"],
        "claims": {"sub": "admin-1", "secret": "must-not-be-returned"},
    })

    assert response.status_code == 200
    assert "user_id" not in response.json()
    assert "claims" not in response.json()
