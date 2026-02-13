"""Authentication middleware - checks tokens and auto-refreshes."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.services.auth_service import get_user, refresh_tokens
from bot.texts import fa

# Commands that don't require authentication
PUBLIC_COMMANDS = {"/start", "/login", "/help"}


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Extract telegram_id and check if auth is needed
        telegram_id: int | None = None
        skip_auth = False

        if isinstance(event, Message):
            telegram_id = event.from_user.id if event.from_user else None
            if event.text and event.text.split()[0] in PUBLIC_COMMANDS:
                skip_auth = True
        elif isinstance(event, CallbackQuery):
            telegram_id = event.from_user.id if event.from_user else None

        if skip_auth or telegram_id is None:
            return await handler(event, data)

        user = await get_user(telegram_id)

        if not user or not user.access_token:
            # Not authenticated
            if isinstance(event, Message):
                from bot.handlers.start import send_login_prompt

                await send_login_prompt(event)
            elif isinstance(event, CallbackQuery):
                await event.answer(fa.LOGIN_REQUIRED, show_alert=True)
            return None

        # Auto-refresh if token expiring soon (< 60s)
        if user.token_expires_at and user.token_expires_at - time.time() < 60:
            success = await refresh_tokens(user)
            if not success:
                if isinstance(event, Message):
                    from bot.handlers.start import send_login_prompt

                    await send_login_prompt(event, text=fa.SESSION_EXPIRED)
                elif isinstance(event, CallbackQuery):
                    await event.answer(fa.SESSION_EXPIRED, show_alert=True)
                return None

        # Inject user and API client into handler data
        data["user"] = user
        data["account"] = user.selected_account

        return await handler(event, data)
