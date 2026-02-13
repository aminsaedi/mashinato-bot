"""Transfer and continue rental handlers."""

import json
import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from bot.callbacks.factory import TransferCB
from bot.db.models import User
from bot.keyboards.account import account_list_keyboard
from bot.keyboards.builders import back_to_menu_button
from bot.services.api_client import APIError, CarAPI
from bot.texts import fa

logger = logging.getLogger(__name__)
router = Router()


def get_other_accounts(user: User) -> list[str]:
    try:
        accounts = json.loads(user.accessible_accounts or "[]")
        return [a for a in accounts if a != user.selected_account]
    except (json.JSONDecodeError, TypeError):
        return []


@router.callback_query(TransferCB.filter(F.action == "select_target"))
async def select_transfer_target(callback: CallbackQuery, user: User, **kwargs) -> None:
    others = get_other_accounts(user)
    if not others:
        await callback.answer(fa.NO_ACCOUNTS, show_alert=True)
        return
    await callback.message.edit_text(
        fa.RENTAL_TRANSFER_SELECT,
        reply_markup=account_list_keyboard(others, action="transfer_to"),
    )
    await callback.answer()


@router.callback_query(TransferCB.filter(F.action == "transfer_to"))
async def do_transfer(
    callback: CallbackQuery, callback_data: TransferCB, user: User, **kwargs
) -> None:
    api = CarAPI(user.access_token)
    try:
        await api.transfer_rental(user.selected_account, callback_data.account)
        await callback.message.edit_text(
            fa.RENTAL_TRANSFERRED.format(account=callback_data.account),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
    except APIError as e:
        await callback.message.edit_text(
            fa.ERROR_API.format(error=e.detail),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
    await callback.answer()


@router.callback_query(TransferCB.filter(F.action == "select_continue"))
async def select_continue_target(callback: CallbackQuery, user: User, **kwargs) -> None:
    others = get_other_accounts(user)
    if not others:
        await callback.answer(fa.NO_ACCOUNTS, show_alert=True)
        return
    await callback.message.edit_text(
        fa.RENTAL_TRANSFER_SELECT,
        reply_markup=account_list_keyboard(others, action="continue_on"),
    )
    await callback.answer()


@router.callback_query(TransferCB.filter(F.action == "continue_on"))
async def do_continue(
    callback: CallbackQuery, callback_data: TransferCB, user: User, **kwargs
) -> None:
    api = CarAPI(user.access_token)
    try:
        await api.continue_rental(user.selected_account, callback_data.account)
        await callback.message.edit_text(
            fa.RENTAL_CONTINUED.format(account=callback_data.account),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
    except APIError as e:
        await callback.message.edit_text(
            fa.ERROR_API.format(error=e.detail),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
    await callback.answer()
