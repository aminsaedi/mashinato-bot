"""Admin dispatcher handlers."""

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


@router.callback_query(AdminCB.filter(F.action == "dispatcher"))
async def show_dispatcher(callback: CallbackQuery, user: User, **kwargs) -> None:
    if not user.is_admin:
        await callback.answer(fa.ADMIN_NOT_AUTHORIZED, show_alert=True)
        return

    api = CarAPI(user.access_token)
    try:
        health = await api.get_dispatcher_health()
        agents = await api.list_agents()

        text = "📡 وضعیت دیسپچر\n\n"
        text += f"وضعیت: {health.get('status', '?')}\n"

        agent_list = agents.get("agents", [])
        text += f"ایجنت‌ها: {agents.get('total_count', len(agent_list))}\n\n"

        for agent in agent_list[:10]:
            aid = agent.get("agent_id", "?")
            hostname = agent.get("hostname", "?")
            status = agent.get("status", "?")
            ips = len(agent.get("ipv6_addresses", []))
            icon = "🟢" if status == "active" else "🔴"
            text += f"{icon} {aid} ({hostname}) - {ips} IPs\n"

    except APIError as e:
        text = fa.ERROR_API.format(error=e.detail)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 بروزرسانی",
                    callback_data=AdminCB(action="dispatcher").pack(),
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
