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


STATE_LABELS = {
    "Upcoming": "رزرو شده",
    "Started": "در حال سفر",
    "Completed": "تکمیل شده",
    "Cancelled": "لغو شده",
}


def _fmt_time(iso: str | None) -> str:
    """Extract HH:MM from ISO datetime string."""
    if not iso:
        return "?"
    try:
        # "2026-02-13T16:04:18Z" → "16:04"
        return iso.split("T")[1][:5]
    except (IndexError, AttributeError):
        return str(iso)


def format_rental(rental: dict) -> str:
    """Format rental data into Persian text."""
    vehicle = rental.get("vehicle", {})
    model = vehicle.get("model") or vehicle.get("make") or "?"
    number = vehicle.get("vehicleNb", vehicle.get("vehicle_nb", "?"))
    state = rental.get("state", rental.get("status", "?"))
    state_fa = STATE_LABELS.get(state, state)

    lines = [fa.RENTAL_TITLE]
    lines.append(fa.RENTAL_VEHICLE.format(model=model, number=number))

    start = rental.get("reservedStartDate", rental.get("startTime"))
    end = rental.get("reservedEndDate", rental.get("endTime"))
    if start:
        lines.append(fa.RENTAL_START_TIME.format(time=_fmt_time(start)))
    if end:
        lines.append(fa.RENTAL_END_TIME.format(time=_fmt_time(end)))

    lines.append(fa.RENTAL_STATUS.format(status=state_fa))
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
            # Send vehicle location if available
            vehicle = rental.get("vehicle", {})
            loc = vehicle.get("vehicleLocation", {})
            lat = loc.get("latitude")
            lng = loc.get("longitude")
            if lat and lng:
                await callback.message.answer_location(latitude=lat, longitude=lng)
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
