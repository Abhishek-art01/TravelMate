from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import UserAccount
from app.models.user import User

SUPPORTED_PROVIDERS = {"email", "google", "apple", "facebook", "linkedin", "github", "x", "supabase"}


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _verified_provider(auth_context: dict) -> str:
    provider = str(auth_context.get("provider") or "supabase").lower()
    return provider if provider in SUPPORTED_PROVIDERS else "supabase"


async def resolve_travelmate_user(session: AsyncSession, auth_context: dict) -> User:
    """Idempotently map a signature-verified Supabase subject to a local user."""
    subject = auth_context.get("user_id")
    if not isinstance(subject, str) or not subject:
        raise ValueError("A verified Supabase subject is required")

    provider = _verified_provider(auth_context)
    account_result = await session.execute(
        select(UserAccount).where(
            UserAccount.provider == provider,
            UserAccount.provider_subject == subject,
        )
    )
    account = account_result.scalar_one_or_none()
    if account is not None:
        user_result = await session.execute(select(User).where(User.id == account.user_id))
        user = user_result.scalar_one_or_none()
        if user is not None:
            return user

    user_result = await session.execute(select(User).where(User.auth_provider_user_id == subject))
    user = user_result.scalar_one_or_none()
    now = _timestamp()
    if user is None:
        user = User(
            id=str(uuid4()),
            auth_provider_user_id=subject,
            account_status="active",
            created_at=now,
            updated_at=now,
        )
        session.add(user)
        await session.flush()

    if account is None:
        claims = auth_context.get("claims") if isinstance(auth_context.get("claims"), dict) else {}
        session.add(UserAccount(
            id=str(uuid4()),
            user_id=user.id,
            provider=provider,
            provider_subject=subject,
            email=auth_context.get("email"),
            email_verified=bool(claims.get("email_verified", False)),
            created_at=now,
            updated_at=now,
        ))

    try:
        await session.commit()
        await session.refresh(user)
        return user
    except IntegrityError:
        await session.rollback()
        winner_result = await session.execute(select(User).where(User.auth_provider_user_id == subject))
        winner = winner_result.scalar_one_or_none()
        if winner is not None:
            return winner
        raise
