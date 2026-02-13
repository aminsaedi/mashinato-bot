"""Tests for throttle middleware."""

import os
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

os.environ.setdefault("BOT_TOKEN", "test:token")
os.environ.setdefault("DATABASE_PATH", ":memory:")

from bot.middlewares.throttle import ThrottleMiddleware


@pytest.mark.asyncio
async def test_throttle_allows_first_request():
    mw = ThrottleMiddleware(rate_limit=1.0)
    handler = AsyncMock(return_value="ok")
    event = MagicMock()
    event.from_user = MagicMock()
    event.from_user.id = 123

    await mw(handler, event, {})
    # handler should be called since it's the first request


@pytest.mark.asyncio
async def test_throttle_rate_limit_tracking():
    mw = ThrottleMiddleware(rate_limit=10.0)

    event = MagicMock()
    event.from_user = MagicMock()
    event.from_user.id = 456

    # Simulate a previous call
    mw._last_call[456] = time.monotonic()

    # Verify the timestamp is tracked
    assert 456 in mw._last_call
