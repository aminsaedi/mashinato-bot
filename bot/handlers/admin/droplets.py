"""Admin droplet management handlers."""

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


@router.callback_query(AdminCB.filter(F.action == "droplets"))
async def show_droplets(callback: CallbackQuery, user: User, **kwargs) -> None:
    if not user.is_admin:
        await callback.answer(fa.ADMIN_NOT_AUTHORIZED, show_alert=True)
        return

    api = CarAPI(user.access_token)
    try:
        summary = await api.get_droplets_summary()
        droplets = await api.list_droplets()

        text = "💧 دراپلت‌ها\n\n"
        if isinstance(summary, dict):
            text += f"کل: {summary.get('total', '?')}\n"
            by_status = summary.get("by_status", {})
            for status, count in by_status.items():
                text += f"  {status}: {count}\n"
            cost = summary.get("estimated_cost_per_hour_cents", 0)
            text += f"هزینه/ساعت: {cost}¢\n\n"

        if isinstance(droplets, list):
            for d in droplets[:10]:
                name = d.get("name", "?")
                status = d.get("status", "?")
                ip = d.get("ipv4_address", "?")
                icon = "🟢" if status == "active" else "🟡" if status == "provisioning" else "🔴"
                text += f"{icon} {name} ({ip}) - {status}\n"

    except APIError as e:
        text = fa.ERROR_API.format(error=e.detail)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 بروزرسانی",
                    callback_data=AdminCB(action="droplets").pack(),
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
