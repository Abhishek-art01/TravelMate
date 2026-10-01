from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.dependencies import get_db_session
from app.core.security import get_current_user, get_current_user_optional
from app.db.base import Base
from app.main import app
from app.models.interest import Interest


@pytest.fixture
def profile_api(tmp_path) -> Iterator[tuple[TestClient, dict[str, str]]]:
    database_path = tmp_path / "travelmate-test.sqlite3"
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}", poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def create_schema() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with factory() as session:
            for code, name in (
                ("food_walks", "Food walks"),
                ("hiking", "Hiking"),
                ("photography", "Photography"),
                ("heritage", "Heritage"),
                ("art_design", "Art and design"),
                ("live_music", "Live music"),
                ("beaches", "Beaches"),
                ("local_culture", "Local culture"),
            ):
                session.add(Interest(id=f"catalog-{code}", code=code, name=name, active=True))
            await session.commit()

    asyncio.run(create_schema())
    auth_identity = {"user_id": "supabase-user-a", "email": "person@example.com", "role": "user", "provider": "email", "claims": {}}

    async def database_session() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            yield session

    async def authenticated_identity() -> dict[str, str]:
        return auth_identity

    existing_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db_session] = database_session
    app.dependency_overrides[get_current_user] = authenticated_identity
    app.dependency_overrides[get_current_user_optional] = authenticated_identity
    try:
        with TestClient(app) as client:
            yield client, auth_identity
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(existing_overrides)
        asyncio.run(engine.dispose())
