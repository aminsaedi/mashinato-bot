"""Admin system handlers: health, version, admin panel."""

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


async def show_admin_panel(callback: CallbackQuery, user: User, **kwargs) -> None:
    if not user.is_admin:
        await callback.answer(fa.ADMIN_NOT_AUTHORIZED, show_alert=True)
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fa.ADMIN_DISPATCHER,
                    callback_data=AdminCB(action="dispatcher").pack(),
                ),
                InlineKeyboardButton(
                    text=fa.ADMIN_DROPLETS,
                    callback_data=AdminCB(action="droplets").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fa.ADMIN_IPV6,
                    callback_data=AdminCB(action="ipv6").pack(),
                ),
                InlineKeyboardButton(
                    text=fa.ADMIN_MONITORING,
                    callback_data=AdminCB(action="monitoring").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fa.ADMIN_HEALTH,
                    callback_data=AdminCB(action="health").pack(),
                ),
                InlineKeyboardButton(
                    text=fa.ADMIN_VERSION,
                    callback_data=AdminCB(action="version").pack(),
                ),
            ],
            [back_to_menu_button()],
        ]
    )
    await callback.message.edit_text(fa.ADMIN_TITLE, reply_markup=kb)
    await callback.answer()


@router.callback_query(AdminCB.filter(F.action == "health"))
async def admin_health(callback: CallbackQuery, user: User, **kwargs) -> None:
    if not user.is_admin:
        await callback.answer(fa.ADMIN_NOT_AUTHORIZED, show_alert=True)
        return

    api = CarAPI(user.access_token)
    try:
        result = await api.health_detail()
        status = result.get("status", "?")
        icon = {"healthy": "💚", "degraded": "🟡", "unhealthy": "🔴"}.get(status, "❓")
        text = f"{icon} وضعیت: {status}\n"
        if result.get("version"):
            text += f"📌 نسخه: {result['version']}\n"

        checks = result.get("checks", {})
        for name, check in checks.items():
            c_status = check.get("status", "?")
            c_icon = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "❌"}.get(c_status, "❓")
            text += f"{c_icon} {name}: {c_status}\n"

        if result.get("active_searches") is not None:
            text += f"\n🔍 جستجوهای فعال: {result['active_searches']}"
        if result.get("active_optimizations") is not None:
            text += f"\n📊 بهینه‌سازی‌های فعال: {result['active_optimizations']}"
        if result.get("connected_agents") is not None:
            text += f"\n📡 ایجنت‌های متصل: {result['connected_agents']}"
    except APIError as e:
        text = fa.ERROR_API.format(error=e.detail)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
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


@router.callback_query(AdminCB.filter(F.action == "version"))
async def admin_version(callback: CallbackQuery, user: User, **kwargs) -> None:
    if not user.is_admin:
        await callback.answer(fa.ADMIN_NOT_AUTHORIZED, show_alert=True)
        return

    api = CarAPI(user.access_token)
    try:
        result = await api.get_version()
        text = (
            f"📌 اطلاعات نسخه\n\n"
            f"Commit: <code>{result.get('commit_sha', '?')}</code>\n"
            f"Build: {result.get('build_time', '?')}"
        )
    except APIError as e:
        text = fa.ERROR_API.format(error=e.detail)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
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


@router.callback_query(AdminCB.filter(F.action == "panel"))
async def back_to_admin(callback: CallbackQuery, user: User, **kwargs) -> None:
    await show_admin_panel(callback, user)
