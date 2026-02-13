"""Login/logout command handlers."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.db.models import User
from bot.handlers.start import send_login_prompt
from bot.services.auth_service import logout_user
from bot.texts import fa

router = Router()


@router.message(Command("login"))
async def cmd_login(message: Message, user: User | None = None, **kwargs) -> None:
    if user and user.access_token:
        await message.answer(fa.LOGIN_SUCCESS)
        return
    await send_login_prompt(message)


@router.message(Command("logout"))
async def cmd_logout(message: Message, user: User | None = None, **kwargs) -> None:
    if not message.from_user:
        return
    if user and user.access_token:
        await logout_user(message.from_user.id)
        await message.answer(fa.LOGOUT_SUCCESS)
    else:
        await message.answer(fa.LOGIN_REQUIRED)
