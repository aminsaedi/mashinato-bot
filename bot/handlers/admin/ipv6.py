"""Admin IPv6 pool management handlers."""

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.factory import AdminCB
from bot.db.models import User
from bot.keyboards.builders import back_to_menu_button
from bot.services.api_client import APIError, CarAPI
from bot.texts import fa

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(AdminCB.filter(F.action == "ipv6"))
async def show_ipv6(callback: CallbackQuery, user: User, **kwargs) -> None:
    if not user.is_admin:
        await callback.answer(fa.ADMIN_NOT_AUTHORIZED, show_alert=True)
        return

    api = CarAPI(user.access_token)
    try:
        stats = await api.get_ipv6_statistics()
        pool = await api.get_pool_status()

        text = "🌐 آمار IPv6\n\n"
        if isinstance(stats, dict):
            for key, value in stats.items():
                text += f"<b>{key}</b>: {value}\n"

        text += "\n📊 وضعیت Pool:\n"
        if isinstance(pool, dict):
            text += f"کل IP‌ها: {pool.get('total_ips', '?')}\n"
            text += f"فعال: {pool.get('active_ips', '?')}\n"
            text += f"مسدود: {pool.get('blocked_ips', '?')}\n"
            text += f"ایجنت‌ها: {pool.get('active_agents', '?')}/{pool.get('total_agents', '?')}\n"

    except APIError as e:
        text = fa.ERROR_API.format(error=e.detail)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔓 رفع انسداد منقضی",
                    callback_data=AdminCB(action="ipv6_unblock").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 بروزرسانی",
                    callback_data=AdminCB(action="ipv6").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text=fa.BACK,
                    callback_data=AdminCB(action="panel").pack(),
                )
            ],
            [back_to_menu_button()],
        ]
    )
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(AdminCB.filter(F.action == "ipv6_unblock"))
async def unblock_expired(callback: CallbackQuery, user: User, **kwargs) -> None:
    if not user.is_admin:
        await callback.answer(fa.ADMIN_NOT_AUTHORIZED, show_alert=True)
        return

    api = CarAPI(user.access_token)
    try:
        result = await api.unblock_expired_ips()
        count = result.get("count", 0)
        await callback.answer(f"✅ {count} IP رفع انسداد شد", show_alert=True)
    except APIError as e:
        await callback.answer(fa.ERROR_API.format(error=e.detail), show_alert=True)
