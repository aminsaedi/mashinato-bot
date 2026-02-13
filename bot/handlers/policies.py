"""Account policies management handlers."""

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from bot.callbacks.factory import PolicyCB, SettingsCB
from bot.db.models import User
from bot.keyboards.builders import back_to_menu_button
from bot.services.api_client import APIError, CarAPI
from bot.texts import fa

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(SettingsCB.filter(F.action == "policies"))
async def show_policies(callback: CallbackQuery, user: User, **kwargs) -> None:
    api = CarAPI(user.access_token)
    try:
        result = await api.list_policies()
        policies = result.get("policies", [])
    except APIError as e:
        await callback.message.edit_text(
            fa.ERROR_API.format(error=e.detail),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
        await callback.answer()
        return

    if not policies:
        await callback.message.edit_text(
            fa.POLICIES_EMPTY,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
        await callback.answer()
        return

    text = f"{fa.POLICIES_TITLE}\n\n"
    for p in policies:
        account = p.get("account_name", "?")
        action = p.get("action", "?")
        denied = "🚫" if p.get("denied") else "✅"
        text += f"{denied} {account}: {action}\n"

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
    )
    await callback.answer()


@router.callback_query(PolicyCB.filter(F.action == "toggle"))
async def toggle_policy(
    callback: CallbackQuery, callback_data: PolicyCB, user: User, **kwargs
) -> None:
    await callback.answer("عملکرد در حال توسعه", show_alert=True)
