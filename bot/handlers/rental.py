"""Rental management handlers."""

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from bot.callbacks.factory import RentalCB
from bot.db.models import User
from bot.keyboards.builders import back_to_menu_button
from bot.keyboards.rental import (
    no_rental_keyboard,
    rental_actions_keyboard,
    rental_cancel_confirm_keyboard,
)
from bot.services.api_client import APIError, CarAPI
from bot.texts import fa

logger = logging.getLogger(__name__)
router = Router()


def format_rental(rental: dict) -> str:
    """Format rental data into Persian text."""
    vehicle = rental.get("vehicle", rental)
    model = vehicle.get("model", vehicle.get("vehicleModel", "?"))
    number = vehicle.get("vehicle_nb", vehicle.get("vehicleNumber", "?"))
    status = rental.get("status", rental.get("rentalStatus", "?"))

    lines = [fa.RENTAL_TITLE]
    lines.append(fa.RENTAL_VEHICLE.format(model=model, number=number))
    if "startTime" in rental or "start_time" in rental:
        lines.append(
            fa.RENTAL_START_TIME.format(time=rental.get("startTime", rental.get("start_time", "")))
        )
    if "endTime" in rental or "end_time" in rental:
        lines.append(
            fa.RENTAL_END_TIME.format(time=rental.get("endTime", rental.get("end_time", "")))
        )
    lines.append(fa.RENTAL_STATUS.format(status=status))
    return "\n".join(lines)


async def show_current_rental(callback: CallbackQuery, user: User, **kwargs) -> None:
    account = user.selected_account
    if not account:
        await callback.answer(fa.NO_ACCOUNTS, show_alert=True)
        return

    api = CarAPI(user.access_token)
    try:
        rental = await api.get_current_rental(account)
        if not rental or rental.get("message"):
            await callback.message.edit_text(
                fa.RENTAL_NO_ACTIVE,
                reply_markup=no_rental_keyboard(),
            )
        else:
            await callback.message.edit_text(
                format_rental(rental),
                reply_markup=rental_actions_keyboard(account),
            )
    except APIError as e:
        if e.status_code == 404:
            await callback.message.edit_text(
                fa.RENTAL_NO_ACTIVE,
                reply_markup=no_rental_keyboard(),
            )
        else:
            await callback.message.edit_text(
                fa.ERROR_API.format(error=e.detail),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
            )
    await callback.answer()


@router.callback_query(RentalCB.filter(F.action == "start_trip"))
async def start_trip(
    callback: CallbackQuery, callback_data: RentalCB, user: User, **kwargs
) -> None:
    api = CarAPI(user.access_token)
    try:
        await api.start_trip(callback_data.account)
        await callback.message.edit_text(
            fa.RENTAL_TRIP_STARTED,
            reply_markup=rental_actions_keyboard(callback_data.account),
        )
    except APIError as e:
        await callback.message.edit_text(
            fa.ERROR_API.format(error=e.detail),
            reply_markup=rental_actions_keyboard(callback_data.account),
        )
    await callback.answer()


@router.callback_query(RentalCB.filter(F.action == "end_trip"))
async def end_trip(callback: CallbackQuery, callback_data: RentalCB, user: User, **kwargs) -> None:
    api = CarAPI(user.access_token)
    try:
        await api.end_trip(callback_data.account)
        await callback.message.edit_text(
            fa.RENTAL_TRIP_ENDED,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
    except APIError as e:
        await callback.message.edit_text(
            fa.ERROR_API.format(error=e.detail),
            reply_markup=rental_actions_keyboard(callback_data.account),
        )
    await callback.answer()


@router.callback_query(RentalCB.filter(F.action == "extend"))
async def extend_rental(
    callback: CallbackQuery, callback_data: RentalCB, user: User, **kwargs
) -> None:
    api = CarAPI(user.access_token)
    try:
        result = await api.extend_rental(callback_data.account)
        msg = result.get("message", fa.RENTAL_EXTENDED.format(time=""))
        await callback.message.edit_text(
            msg,
            reply_markup=rental_actions_keyboard(callback_data.account),
        )
    except APIError as e:
        await callback.message.edit_text(
            fa.ERROR_API.format(error=e.detail),
            reply_markup=rental_actions_keyboard(callback_data.account),
        )
    await callback.answer()


@router.callback_query(RentalCB.filter(F.action == "fuel_card"))
async def fuel_card(callback: CallbackQuery, callback_data: RentalCB, user: User, **kwargs) -> None:
    api = CarAPI(user.access_token)
    try:
        result = await api.get_fuel_card(callback_data.account)
        pin = result.get("pin", result.get("cardNumber", "?"))
        await callback.message.edit_text(
            fa.RENTAL_FUEL_PIN.format(pin=pin),
            reply_markup=rental_actions_keyboard(callback_data.account),
        )
    except APIError as e:
        await callback.message.edit_text(
            fa.ERROR_API.format(error=e.detail),
            reply_markup=rental_actions_keyboard(callback_data.account),
        )
    await callback.answer()


@router.callback_query(RentalCB.filter(F.action == "cancel"))
async def cancel_rental_prompt(
    callback: CallbackQuery, callback_data: RentalCB, user: User, **kwargs
) -> None:
    await callback.message.edit_text(
        fa.RENTAL_CANCEL_CONFIRM,
        reply_markup=rental_cancel_confirm_keyboard(callback_data.account),
    )
    await callback.answer()


@router.callback_query(RentalCB.filter(F.action == "cancel_yes"))
async def cancel_rental_confirmed(
    callback: CallbackQuery, callback_data: RentalCB, user: User, **kwargs
) -> None:
    api = CarAPI(user.access_token)
    try:
        await api.cancel_rental(callback_data.account)
        await callback.message.edit_text(
            fa.RENTAL_CANCELLED,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
    except APIError as e:
        await callback.message.edit_text(
            fa.ERROR_API.format(error=e.detail),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
    await callback.answer()
