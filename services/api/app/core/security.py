from __future__ import annotations

import json
import time
from typing import Annotated, Any

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "user": {"profile.read", "profile.write"},
    "moderator": {"profile.read", "profile.write", "moderation.read", "moderation.action"},
    "support": {"support.read", "support.manage", "users.read"},
    "verification_admin": {"verification.read", "verification.review", "verification.approve", "verification.reject"},
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


def _raise_auth_error(code: str, message: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": {"code": code, "message": message}},
    )


def _normalise_role(role: Any) -> str:
    normalized = str(role or "user").strip().lower()
    return normalized if normalized in ROLE_PERMISSIONS else "user"


def get_permissions_for_role(role: str | None, explicit_permissions: set[str] | list[str] | None = None) -> set[str]:
    normalized = _normalise_role(role)
    permissions = set(explicit_permissions or [])
    permissions.update(ROLE_PERMISSIONS.get(normalized, ROLE_PERMISSIONS["user"]))
    return {perm for perm in permissions if perm}


def _extract_bearer_token(credentials: HTTPAuthorizationCredentials | None) -> str:
    if credentials is None:
        _raise_auth_error("AUTHENTICATION_REQUIRED", "Authentication credentials were not provided.")
    return credentials.credentials


def _fetch_jwks_document(url: str) -> dict[str, Any]:
    settings = get_settings()
    if not url or url.startswith(("https://example", "http://example")):
        _raise_auth_error("JWKS_NOT_CONFIGURED", "Supabase JWKS is not configured for this environment.")
    try:
        response = httpx.get(url, timeout=max(10.0, float(settings.port) / 10.0))
        response.raise_for_status()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "JWKS_UNAVAILABLE", "message": "The configured Supabase JWKS could not be fetched."}},
        ) from exc
    try:
        document = response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_JWKS", "message": "The Supabase JWKS response was invalid."}},
        ) from exc
    if not isinstance(document, dict) or not isinstance(document.get("keys"), list):
        _raise_auth_error("INVALID_JWKS", "The Supabase JWKS response did not contain a valid keys list.")
    return document


class JWKSKeyCache:
    def __init__(self, jwks_url: str, cache_ttl_seconds: int = 300):
        self.jwks_url = jwks_url
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}

    def get_signing_key(self, token: str):
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            _raise_auth_error("INVALID_TOKEN", "The JWT does not include a key identifier.")

        cached = self._cache.get(kid)
        if cached and time.monotonic() - cached[0] < self.cache_ttl_seconds:
            return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(cached[1]))

        document = _fetch_jwks_document(self.jwks_url)
        for jwk in document.get("keys", []):
            if jwk.get("kid") == kid:
                self._cache[kid] = (time.monotonic(), jwk)
                return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))

        _raise_auth_error("UNKNOWN_KEY_ID", "The token signing key is not available in the configured JWKS set.")


def _build_auth_context(payload: dict[str, Any]) -> dict[str, Any]:
    role = _normalise_role(payload.get("app_role") or payload.get("role"))
    explicit_permissions = payload.get("permissions") or []
    permissions = get_permissions_for_role(role, explicit_permissions)
    provider = payload.get("app_metadata", {}).get("provider") if isinstance(payload.get("app_metadata"), dict) else payload.get("provider")
    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "role": role,
        "provider": provider or "supabase",
        "account_status": "active",
        "permissions": sorted(permissions),
        "claims": payload,
    }


def _decode_supabase_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    if not token:
        _raise_auth_error("AUTHENTICATION_REQUIRED", "Authentication credentials were not provided.")

    try:
        header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "message": "The provided authentication token is malformed."}},
        ) from exc

    kid = header.get("kid")
    if not kid:
        _raise_auth_error("INVALID_TOKEN", "The JWT does not include a key identifier.")

    cache = JWKSKeyCache(settings.supabase_jwks_url, settings.jwt_cache_ttl_seconds)
    try:
        signing_key = cache.get_signing_key(token)
        payload = jwt.decode(
            token,
            key=signing_key,
            algorithms=[header.get("alg", "RS256")],
            audience=settings.supabase_jwt_audience,
            issuer=settings.supabase_jwt_issuer,
            options={"require": ["exp", "sub", "iss", "aud"]},
        )
    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "message": "The provided authentication token could not be verified."}},
        ) from exc

    if not payload.get("sub"):
        _raise_auth_error("INVALID_TOKEN", "The token does not contain a valid subject claim.")
    return payload


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
):
    token = _extract_bearer_token(credentials)
    payload = _decode_supabase_token(token)
    return _build_auth_context(payload)


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
):
    if credentials is None:
        return None
    return await get_current_user(credentials)
