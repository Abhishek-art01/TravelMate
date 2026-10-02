"""Supabase Auth Admin API client (httpx-based, no supabase-py dependency)."""
from __future__ import annotations

import httpx

from app.config import get_settings


class SupabaseAdminClient:
    """Minimal admin client for creating/deleting auth users via Supabase REST API."""

    def __init__(self) -> None:
        settings = get_settings()
        self._base = settings.supabase_url.rstrip("/")
        self._headers = {
            "apikey": settings.supabase_service_role_key,
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # User creation
    # ------------------------------------------------------------------

    def create_user(self, email: str, password: str, display_name: str) -> dict:
        """Create a confirmed auth user. Returns the Supabase user dict."""
        payload = {
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"display_name": display_name},
        }
        resp = httpx.post(
            f"{self._base}/auth/v1/admin/users",
            json=payload,
            headers=self._headers,
            timeout=30,
        )
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"Supabase create_user failed [{resp.status_code}]: {resp.text}"
            )
        return resp.json()

    # ------------------------------------------------------------------
    # User lookup by email
    # ------------------------------------------------------------------

    def find_user_by_email(self, email: str) -> dict | None:
        """Return user dict if email exists, else None."""
        resp = httpx.get(
            f"{self._base}/auth/v1/admin/users",
            params={"page": 1, "per_page": 1000},
            headers=self._headers,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        users = data.get("users", data) if isinstance(data, dict) else data
        for u in users:
            if u.get("email") == email:
                return u
        return None

    # ------------------------------------------------------------------
    # User deletion
    # ------------------------------------------------------------------

    def delete_user(self, supabase_uid: str) -> None:
        """Hard-delete a Supabase auth user by UUID."""
        resp = httpx.delete(
            f"{self._base}/auth/v1/admin/users/{supabase_uid}",
            headers=self._headers,
            timeout=30,
        )
        if resp.status_code not in (200, 204):
            raise RuntimeError(
                f"Supabase delete_user failed [{resp.status_code}]: {resp.text}"
            )
