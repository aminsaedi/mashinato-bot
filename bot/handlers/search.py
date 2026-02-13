"""Search wizard and status handlers."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from bot.callbacks.factory import SearchCB
from bot.db.models import User
from bot.keyboards.builders import back_to_menu_button
from bot.keyboards.search import filters_keyboard, radius_keyboard, search_status_keyboard
from bot.services.api_client import APIError, CarAPI
from bot.states.search import SearchForm
from bot.texts import fa

logger = logging.getLogger(__name__)
router = Router()


async def show_search_menu(callback: CallbackQuery, user: User, **kwargs) -> None:
    """Show search status or start new search."""
    account = user.selected_account
    if not account:
        await callback.answer(fa.NO_ACCOUNTS, show_alert=True)
        return

    api = CarAPI(user.access_token)
    try:
        status = await api.get_search_status(account)
        s = status.get("status", "")
        if s in ("running", "completed"):
            text = f"{fa.SEARCH_STATUS_TITLE}\n"
            text += f"{fa.RENTAL_STATUS.format(status=s)}\n"
            params = status.get("params", {})
            if params:
                point = params.get("point", {})
                text += fa.SEARCH_SUMMARY.format(
                    lat=point.get("latitude", "?"),
                    lng=point.get("longitude", "?"),
                    radius=params.get("radius", "?"),
                    filters=", ".join(k for k, v in params.get("filters", {}).items() if v) or "-",
                )
            if s == "completed" and status.get("result"):
                text += f"\n\n{fa.SEARCH_STATUS_FOUND}"
            await callback.message.edit_text(text, reply_markup=search_status_keyboard())
            await callback.answer()
            return
    except APIError:
        pass

    # No active search - offer to start one
    from aiogram.types import InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fa.SEARCH_START,
                    callback_data=SearchCB(action="start").pack(),
                )
            ],
            [back_to_menu_button()],
        ]
    )
    await callback.message.edit_text(fa.SEARCH_TITLE, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(SearchCB.filter(F.action == "start"))
async def start_search_wizard(
    callback: CallbackQuery, state: FSMContext, user: User, **kwargs
) -> None:
    """Start the search wizard - request location."""
    await state.set_state(SearchForm.send_location)
    await state.update_data(
        account=user.selected_account,
        filters={
            "no_prius": True,
            "no_ev": False,
            "snow_car": False,
        },
    )
    await callback.message.edit_text(fa.SEARCH_SEND_LOCATION)
    await callback.answer()


@router.message(SearchForm.send_location)
async def receive_location(message: Message, state: FSMContext, **kwargs) -> None:
    """Receive location from user (shared location or text coordinates)."""
    lat, lng = None, None

    if message.location:
        lat = message.location.latitude
        lng = message.location.longitude
    elif message.text:
        parts = message.text.replace(",", " ").split()
        if len(parts) == 2:
            try:
                lat, lng = float(parts[0]), float(parts[1])
            except ValueError:
                await message.answer(fa.SEARCH_SEND_LOCATION)
                return
        else:
            await message.answer(fa.SEARCH_SEND_LOCATION)
            return
    else:
        await message.answer(fa.SEARCH_SEND_LOCATION)
        return

    await state.update_data(latitude=lat, longitude=lng)
    await state.set_state(SearchForm.select_radius)
    await message.answer(fa.SEARCH_SELECT_RADIUS, reply_markup=radius_keyboard())


@router.callback_query(SearchCB.filter(F.action == "radius"), SearchForm.select_radius)
async def select_radius(
    callback: CallbackQuery, callback_data: SearchCB, state: FSMContext, **kwargs
) -> None:
    if callback_data.value == "custom":
        await state.set_state(SearchForm.custom_radius)
        await callback.message.edit_text(fa.SEARCH_RADIUS_PROMPT)
        await callback.answer()
        return

    radius_m = int(callback_data.value)
    await state.update_data(radius=radius_m / 1000)  # Convert to km for API
    await state.set_state(SearchForm.select_filters)

    data = await state.get_data()
    await callback.message.edit_text(
        fa.SEARCH_FILTERS_TITLE,
        reply_markup=filters_keyboard(data.get("filters", {})),
    )
    await callback.answer()


@router.message(SearchForm.custom_radius)
async def custom_radius(message: Message, state: FSMContext, **kwargs) -> None:
    try:
        radius_m = int(message.text.strip())
        if radius_m <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer(fa.SEARCH_RADIUS_PROMPT)
        return

    await state.update_data(radius=radius_m / 1000)
    await state.set_state(SearchForm.select_filters)

    data = await state.get_data()
    await message.answer(
        fa.SEARCH_FILTERS_TITLE,
        reply_markup=filters_keyboard(data.get("filters", {})),
    )


@router.callback_query(SearchCB.filter(F.action == "filter"), SearchForm.select_filters)
async def toggle_filter(
    callback: CallbackQuery, callback_data: SearchCB, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    filters = data.get("filters", {})
    key = callback_data.value
    filters[key] = not filters.get(key, False)
    await state.update_data(filters=filters)

    await callback.message.edit_reply_markup(reply_markup=filters_keyboard(filters))
    await callback.answer()


@router.callback_query(SearchCB.filter(F.action == "confirm"), SearchForm.select_filters)
async def confirm_search(callback: CallbackQuery, state: FSMContext, user: User, **kwargs) -> None:
    data = await state.get_data()
    account = data.get("account", user.selected_account)

    params = {
        "point": {"latitude": data["latitude"], "longitude": data["longitude"]},
        "radius": data["radius"],
        "filters": data.get("filters", {}),
    }

    api = CarAPI(user.access_token)
    try:
        await api.start_search(account, params)
        await callback.message.edit_text(
            fa.SEARCH_STARTED,
            reply_markup=search_status_keyboard(),
        )
    except APIError as e:
        await callback.message.edit_text(
            fa.ERROR_API.format(error=e.detail),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )

    await state.clear()
    await callback.answer()


@router.callback_query(SearchCB.filter(F.action == "stop"))
async def stop_search(callback: CallbackQuery, user: User, **kwargs) -> None:
    account = user.selected_account
    if not account:
        await callback.answer(fa.NO_ACCOUNTS, show_alert=True)
        return

    api = CarAPI(user.access_token)
    try:
        await api.stop_search(account)
        await callback.message.edit_text(
            fa.SEARCH_STOPPED,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
    except APIError as e:
        await callback.message.edit_text(
            fa.ERROR_API.format(error=e.detail),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
    await callback.answer()


@router.callback_query(SearchCB.filter(F.action == "status"))
async def search_status(callback: CallbackQuery, user: User, **kwargs) -> None:
    await show_search_menu(callback, user)
