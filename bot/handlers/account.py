"""Account management handlers."""

import json
import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select as sa_select

from bot.callbacks.factory import AccountCB
from bot.db.models import User
from bot.db.session import async_session
from bot.keyboards.account import account_list_keyboard
from bot.keyboards.builders import back_to_menu_button
from bot.keyboards.main_menu import main_menu_keyboard
from bot.services.api_client import APIError, CarAPI
from bot.texts import fa

logger = logging.getLogger(__name__)
router = Router()


def get_accounts(user: User) -> list[str]:
    try:
        return json.loads(user.accessible_accounts or "[]")
    except (json.JSONDecodeError, TypeError):
        return []


async def show_accounts(callback: CallbackQuery, user: User, **kwargs) -> None:
    accounts = get_accounts(user)
    if not accounts:
        from aiogram.types import InlineKeyboardMarkup

        await callback.message.edit_text(
            fa.NO_ACCOUNTS,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        fa.SELECT_ACCOUNT,
        reply_markup=account_list_keyboard(accounts),
    )
    await callback.answer()


@router.callback_query(AccountCB.filter(F.action == "select"))
async def select_account(
    callback: CallbackQuery,
    callback_data: AccountCB,
    user: User,
    **kwargs,
) -> None:
    account = callback_data.account

    async with async_session() as session:
        result = await session.execute(sa_select(User).where(User.telegram_id == user.telegram_id))
        db_user = result.scalar_one_or_none()
        if db_user:
            db_user.selected_account = account
            await session.commit()
            user.selected_account = account

    await callback.message.edit_text(
        f"{fa.ACCOUNT_SWITCHED.format(account=account)}\n"
        f"{fa.MAIN_MENU_TITLE}\n{fa.ACTIVE_ACCOUNT.format(account=account)}",
        reply_markup=main_menu_keyboard(is_admin=bool(user.is_admin)),
    )
    await callback.answer()


@router.callback_query(AccountCB.filter(F.action == "status"))
async def account_status(
    callback: CallbackQuery,
    callback_data: AccountCB,
    user: User,
    **kwargs,
) -> None:
    account = callback_data.account or user.selected_account
    if not account:
        await callback.answer(fa.NO_ACCOUNTS, show_alert=True)
        return

    api = CarAPI(user.access_token)
    try:
        status = await api.get_account_status(account)
        text = f"{fa.ACCOUNT_STATUS_TITLE.format(account=account)}\n\n"
        for key, value in status.items():
            text += f"<b>{key}</b>: {value}\n"
    except APIError as e:
        text = fa.ERROR_API.format(error=e.detail)

    from aiogram.types import InlineKeyboardMarkup

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
    )
    await callback.answer()


@router.callback_query(AccountCB.filter(F.action == "next_free"))
async def next_free_time(
    callback: CallbackQuery,
    callback_data: AccountCB,
    user: User,
    **kwargs,
) -> None:
    account = callback_data.account or user.selected_account
    if not account:
        await callback.answer(fa.NO_ACCOUNTS, show_alert=True)
        return

    api = CarAPI(user.access_token)
    try:
        result = await api.get_next_free_time(account)
        time_str = result.get("next_free_time", result.get("message", "?"))
        text = fa.NEXT_FREE_TIME.format(time=time_str)
    except APIError as e:
        text = fa.ERROR_API.format(error=e.detail)

    from aiogram.types import InlineKeyboardMarkup

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
    )
    await callback.answer()
