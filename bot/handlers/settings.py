"""Bot settings handler."""

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.factory import SettingsCB
from bot.db.models import User
from bot.keyboards.builders import back_to_menu_button
from bot.services.api_client import APIError, CarAPI
from bot.texts import fa

logger = logging.getLogger(__name__)
router = Router()


async def show_settings(callback: CallbackQuery, user: User, **kwargs) -> None:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fa.SETTINGS_WEBHOOKS,
                    callback_data=SettingsCB(action="webhooks").pack(),
                ),
                InlineKeyboardButton(
                    text=fa.SETTINGS_AUDIT,
                    callback_data=SettingsCB(action="audit").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fa.SETTINGS_POLICIES,
                    callback_data=SettingsCB(action="policies").pack(),
                ),
                InlineKeyboardButton(
                    text=fa.SETTINGS_SUBSCRIPTIONS,
                    callback_data=SettingsCB(action="subscriptions").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fa.SETTINGS_INTERVALS,
                    callback_data=SettingsCB(action="intervals").pack(),
                ),
                InlineKeyboardButton(
                    text=fa.SETTINGS_NOTIFICATIONS,
                    callback_data=SettingsCB(action="notifications").pack(),
                ),
            ],
            [back_to_menu_button()],
        ]
    )
    await callback.message.edit_text(fa.SETTINGS_TITLE, reply_markup=kb)
    await callback.answer()


@router.callback_query(SettingsCB.filter(F.action == "intervals"))
async def show_intervals(callback: CallbackQuery, user: User, **kwargs) -> None:
    api = CarAPI(user.access_token)
    try:
        result = await api.get_poll_intervals()
        text = "⏱️ فواصل زمانی:\n\n"
        for key, value in result.items():
            text += f"<b>{key}</b>: {value}\n"
    except APIError as e:
        text = fa.ERROR_API.format(error=e.detail)

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
    )
    await callback.answer()


@router.callback_query(SettingsCB.filter(F.action == "notifications"))
async def show_notifications(callback: CallbackQuery, user: User, **kwargs) -> None:
    text = "🔔 تنظیمات اعلان‌ها\n\nبه‌زودی..."
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
    )
    await callback.answer()
