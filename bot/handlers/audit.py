"""Audit log browser with filters and pagination."""

import contextlib
import json
import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.factory import AuditCB, PageCB, SettingsCB
from bot.db.models import User
from bot.keyboards.builders import back_to_menu_button, pagination_keyboard
from bot.services.api_client import APIError, CarAPI
from bot.texts import fa

logger = logging.getLogger(__name__)
router = Router()

LOGS_PER_PAGE = 10


@router.callback_query(SettingsCB.filter(F.action == "audit"))
async def show_audit_logs(callback: CallbackQuery, user: User, page: int = 0, **kwargs) -> None:
    api = CarAPI(user.access_token)
    try:
        result = await api.list_audit_logs(
            limit=LOGS_PER_PAGE,
            offset=page * LOGS_PER_PAGE,
        )
        logs = result.get("logs", [])
        total = result.get("total", len(logs))
    except APIError as e:
        await callback.message.edit_text(
            fa.ERROR_API.format(error=e.detail),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
        await callback.answer()
        return

    if not logs and page == 0:
        await callback.message.edit_text(
            fa.AUDIT_EMPTY,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
        await callback.answer()
        return

    text = f"{fa.AUDIT_TITLE}\n\n"
    item_buttons: list[list[InlineKeyboardButton]] = []
    for log in logs:
        log_id = log.get("id", 0)
        action = log.get("action", "?")
        status = log.get("response_status", "?")
        text += f"📋 #{log_id} - {action} [{status}]\n"
        item_buttons.append(
            [
                InlineKeyboardButton(
                    text=f"#{log_id} {action}",
                    callback_data=AuditCB(action="detail", log_id=log_id).pack(),
                )
            ]
        )

    total_pages = max(1, (total + LOGS_PER_PAGE - 1) // LOGS_PER_PAGE)
    await callback.message.edit_text(
        text,
        reply_markup=pagination_keyboard("audit", page, total_pages, item_buttons),
    )
    await callback.answer()


@router.callback_query(PageCB.filter(F.section == "audit"))
async def audit_page(callback: CallbackQuery, callback_data: PageCB, user: User, **kwargs) -> None:
    await show_audit_logs(callback, user, page=callback_data.page)


@router.callback_query(AuditCB.filter(F.action == "detail"))
async def audit_detail(
    callback: CallbackQuery, callback_data: AuditCB, user: User, **kwargs
) -> None:
    api = CarAPI(user.access_token)
    try:
        log = await api.get_audit_log(callback_data.log_id)
        text = fa.AUDIT_DETAIL.format(
            id=log.get("id", "?"),
            user=log.get("user_account", "?"),
            action=log.get("action", "?"),
            timestamp=log.get("timestamp", "?"),
            status=log.get("response_status", "?"),
        )
        if log.get("duration_ms"):
            text += f"\n⏱ مدت: {log['duration_ms']}ms"
        if log.get("request_body"):
            body = log["request_body"]
            if isinstance(body, str):
                with contextlib.suppress(json.JSONDecodeError):
                    body = json.loads(body)
            if isinstance(body, dict):
                body_str = json.dumps(body, ensure_ascii=False, indent=2)
            else:
                body_str = str(body)
            if len(body_str) > 500:
                body_str = body_str[:500] + "..."
            text += f"\n\n📤 درخواست:\n<pre>{body_str}</pre>"
    except APIError as e:
        text = fa.ERROR_API.format(error=e.detail)

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
    )
    await callback.answer()
