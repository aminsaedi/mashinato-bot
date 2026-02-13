"""Admin monitoring dashboard handler."""

import json
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


@router.callback_query(AdminCB.filter(F.action == "monitoring"))
async def show_monitoring(callback: CallbackQuery, user: User, **kwargs) -> None:
    if not user.is_admin:
        await callback.answer(fa.ADMIN_NOT_AUTHORIZED, show_alert=True)
        return

    api = CarAPI(user.access_token)
    try:
        dashboard = await api.get_dashboard()

        text = "📊 داشبورد مانیتورینگ\n\n"

        # Droplets section
        droplets = dashboard.get("droplets", {})
        if droplets:
            text += "💧 دراپلت‌ها:\n"
            text += f"  کل: {droplets.get('total', '?')}\n"
            cost = droplets.get("estimated_cost_per_hour_cents", 0)
            text += f"  هزینه/ساعت: {cost}¢\n\n"

        # IPv6 section
        ipv6 = dashboard.get("ipv6_pool", {})
        if ipv6:
            text += "🌐 IPv6:\n"
            text += f"  کل: {ipv6.get('total_ips', '?')}\n"
            text += f"  فعال: {ipv6.get('active_ips', '?')}\n"
            text += f"  مسدود: {ipv6.get('blocked_ips', '?')}\n"
            avg_lat = ipv6.get("average_latency_ms", "?")
            text += f"  تأخیر: {avg_lat}ms\n\n"

        # Coordinator section
        coordinator = dashboard.get("coordinator", {})
        if coordinator:
            text += "📡 هماهنگ‌کننده:\n"
            active = coordinator.get("active_agents", "?")
            total = coordinator.get("total_agents", "?")
            text += f"  ایجنت‌ها: {active}/{total}\n"

    except APIError as e:
        text = fa.ERROR_API.format(error=e.detail)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📦 کش",
                    callback_data=AdminCB(action="cache").pack(),
                ),
                InlineKeyboardButton(
                    text="📈 متریک جستجو",
                    callback_data=AdminCB(action="search_metrics").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔄 بروزرسانی",
                    callback_data=AdminCB(action="monitoring").pack(),
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


@router.callback_query(AdminCB.filter(F.action == "cache"))
async def show_cache(callback: CallbackQuery, user: User, **kwargs) -> None:
    if not user.is_admin:
        await callback.answer(fa.ADMIN_NOT_AUTHORIZED, show_alert=True)
        return

    api = CarAPI(user.access_token)
    try:
        result = await api.get_cache_tracking()
        text = "📦 وضعیت کش:\n\n"
        text += json.dumps(result, ensure_ascii=False, indent=2)[:2000]
    except APIError as e:
        text = fa.ERROR_API.format(error=e.detail)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fa.BACK,
                    callback_data=AdminCB(action="monitoring").pack(),
                )
            ],
            [back_to_menu_button()],
        ]
    )
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(AdminCB.filter(F.action == "search_metrics"))
async def show_search_metrics(callback: CallbackQuery, user: User, **kwargs) -> None:
    if not user.is_admin:
        await callback.answer(fa.ADMIN_NOT_AUTHORIZED, show_alert=True)
        return

    api = CarAPI(user.access_token)
    try:
        result = await api.get_search_metrics()
        text = "📈 متریک‌های جستجو:\n\n"
        if isinstance(result, dict):
            for account, metrics in result.items():
                text += f"👤 {account}:\n"
                if isinstance(metrics, dict):
                    for k, v in metrics.items():
                        text += f"  {k}: {v}\n"
                text += "\n"
        if not result:
            text += "داده‌ای موجود نیست."
    except APIError as e:
        text = fa.ERROR_API.format(error=e.detail)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fa.BACK,
                    callback_data=AdminCB(action="monitoring").pack(),
                )
            ],
            [back_to_menu_button()],
        ]
    )
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
