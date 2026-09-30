from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from fastapi import Request


def get_request_id(request: Request) -> str:
    return request.headers.get("X-Request-ID", "unknown-request")


async def get_db_session() -> AsyncGenerator[Any, None]:
    """Database dependency placeholder for SQLAlchemy session management."""
    yield None
