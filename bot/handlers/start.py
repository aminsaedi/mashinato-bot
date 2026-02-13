"""Start command and login prompt."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.db.models import User
from bot.keyboards.main_menu import main_menu_keyboard
from bot.services.auth_service import create_login_state
from bot.texts import fa

router = Router()


async def send_login_prompt(message: Message, text: str | None = None) -> None:
    """Send login prompt with OAuth URL button."""
    if not message.from_user:
        return
    url = await create_login_state(message.from_user.id, message.chat.id)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=fa.LOGIN_BUTTON, url=url)]]
    )
    await message.answer(
        text or f"{fa.WELCOME}\n{fa.LOGIN_REQUIRED}",
        reply_markup=keyboard,
    )


@router.message(CommandStart())
async def cmd_start(message: Message, user: User | None = None, **kwargs) -> None:
    if user and user.access_token:
        account = user.selected_account or user.authentik_username or ""
        await message.answer(
            f"{fa.WELCOME}\n{fa.ACTIVE_ACCOUNT.format(account=account)}",
            reply_markup=main_menu_keyboard(is_admin=bool(user.is_admin)),
        )
    else:
        await send_login_prompt(message)
