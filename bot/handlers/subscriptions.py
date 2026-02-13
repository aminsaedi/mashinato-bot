"""Subscription management handlers."""

import json
import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.factory import SettingsCB, SubscriptionCB
from bot.db.models import User
from bot.keyboards.builders import back_to_menu_button
from bot.services.api_client import APIError, CarAPI
from bot.texts import fa

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(SettingsCB.filter(F.action == "subscriptions"))
async def show_subscriptions(callback: CallbackQuery, user: User, **kwargs) -> None:
    api = CarAPI(user.access_token)
    try:
        result = await api.list_subscriptions()
        subs = result.get("subscriptions", [])
    except APIError as e:
        await callback.message.edit_text(
            fa.ERROR_API.format(error=e.detail),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
        await callback.answer()
        return

    text = f"{fa.SUBSCRIPTIONS_TITLE}\n\n"
    rows: list[list[InlineKeyboardButton]] = []
    for s in subs:
        account = s.get("account_name", "?")
        has_sub = s.get("has_subscription", False)
        icon = fa.ENABLED if has_sub else fa.DISABLED
        text += f"{icon} {account}\n"
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{icon} {account}",
                    callback_data=SubscriptionCB(action="toggle", account=account).pack(),
                )
            ]
        )

    if not subs:
        # Show accounts that could have subscriptions
        try:
            accounts = json.loads(user.accessible_accounts or "[]")
        except (json.JSONDecodeError, TypeError):
            accounts = []
        for acc in accounts:
            text += f"{fa.DISABLED} {acc}\n"
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"{fa.DISABLED} {acc}",
                        callback_data=SubscriptionCB(action="toggle", account=acc).pack(),
                    )
                ]
            )

    rows.append([back_to_menu_button()])
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await callback.answer()


@router.callback_query(SubscriptionCB.filter(F.action == "toggle"))
async def toggle_subscription(
    callback: CallbackQuery, callback_data: SubscriptionCB, user: User, **kwargs
) -> None:
    api = CarAPI(user.access_token)
    try:
        # Get current state
        result = await api.list_subscriptions()
        subs = result.get("subscriptions", [])
        current_subs = {s["account_name"]: s.get("has_subscription", False) for s in subs}
        current = current_subs.get(callback_data.account, False)

        await api.set_subscription(callback_data.account, not current)
        await callback.answer(fa.WEBHOOK_UPDATED, show_alert=True)
        await show_subscriptions(callback, user)
    except APIError as e:
        await callback.answer(fa.ERROR_API.format(error=e.detail), show_alert=True)
