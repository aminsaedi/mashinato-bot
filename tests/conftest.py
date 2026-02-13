"""Test fixtures."""

import os
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.db.models import Base

# Override settings before importing anything that uses them
os.environ.setdefault("BOT_TOKEN", "test:token")
os.environ.setdefault("DATABASE_PATH", ":memory:")


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture
def mock_bot():
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def mock_api_client():
    with patch("bot.services.api_client.CarAPI") as mock:
        client = AsyncMock()
        mock.return_value = client
        yield client


@pytest.fixture
def sample_user():
    from bot.db.models import User

    return User(
        telegram_id=12345,
        telegram_username="testuser",
        telegram_name="Test User",
        access_token="test-access-token",
        refresh_token="test-refresh-token",
        token_expires_at=9999999999.0,
        authentik_username="testuser",
        accessible_accounts='["amin", "sanaz"]',
        selected_account="amin",
        is_admin=0,
    )


@pytest.fixture
def admin_user():
    from bot.db.models import User

    return User(
        telegram_id=99999,
        telegram_username="admin",
        telegram_name="Admin",
        access_token="admin-access-token",
        refresh_token="admin-refresh-token",
        token_expires_at=9999999999.0,
        authentik_username="admin",
        accessible_accounts='["amin", "sanaz"]',
        selected_account="amin",
        is_admin=1,
    )
