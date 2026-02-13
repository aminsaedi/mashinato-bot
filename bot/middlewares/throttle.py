"""Simple per-user rate limiting middleware."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


class ThrottleMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.5):
        self._rate_limit = rate_limit
        self._last_call: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id: int | None = None
        if isinstance(event, (Message, CallbackQuery)) and event.from_user:
            user_id = event.from_user.id

        if user_id is not None:
            now = time.monotonic()
            last = self._last_call.get(user_id, 0)
            if now - last < self._rate_limit:
                if isinstance(event, CallbackQuery):
                    await event.answer()
                return None
            self._last_call[user_id] = now

        return await handler(event, data)
