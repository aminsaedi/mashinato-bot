"""Vehicle listing and detail handlers."""

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.factory import PageCB, VehicleCB
from bot.db.models import User
from bot.keyboards.builders import back_to_menu_button, pagination_keyboard
from bot.services.api_client import APIError, CarAPI
from bot.texts import fa

logger = logging.getLogger(__name__)
router = Router()

VEHICLES_PER_PAGE = 10


async def show_vehicles_list(callback: CallbackQuery, user: User, page: int = 0, **kwargs) -> None:
    api = CarAPI(user.access_token)
    try:
        result = await api.list_vehicles()
        vehicles = result if isinstance(result, list) else result.get("vehicles", [])
    except APIError as e:
        await callback.message.edit_text(
            fa.ERROR_API.format(error=e.detail),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
        await callback.answer()
        return

    if not vehicles:
        await callback.message.edit_text(
            fa.VEHICLES_EMPTY,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
        await callback.answer()
        return

    total = len(vehicles)
    total_pages = max(1, (total + VEHICLES_PER_PAGE - 1) // VEHICLES_PER_PAGE)
    page = min(page, total_pages - 1)
    start = page * VEHICLES_PER_PAGE
    page_vehicles = vehicles[start : start + VEHICLES_PER_PAGE]

    text = f"{fa.VEHICLES_TITLE}\n\n"
    item_buttons: list[list[InlineKeyboardButton]] = []
    for v in page_vehicles:
        vid = v.get("vehicleId", v.get("vehicle_id", 0))
        model = v.get("model", "?")
        number = v.get("vehicleNb", v.get("vehicle_nb", "?"))
        text += f"🚙 {model} #{number}\n"
        item_buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{model} #{number}",
                    callback_data=VehicleCB(action="detail", vehicle_id=vid).pack(),
                )
            ]
        )

    await callback.message.edit_text(
        text,
        reply_markup=pagination_keyboard("vehicles", page, total_pages, item_buttons),
    )
    await callback.answer()


@router.callback_query(PageCB.filter(F.section == "vehicles"))
async def vehicles_page(
    callback: CallbackQuery, callback_data: PageCB, user: User, **kwargs
) -> None:
    await show_vehicles_list(callback, user, page=callback_data.page)


@router.callback_query(VehicleCB.filter(F.action == "detail"))
async def vehicle_detail(
    callback: CallbackQuery, callback_data: VehicleCB, user: User, **kwargs
) -> None:
    api = CarAPI(user.access_token)
    try:
        v = await api.get_vehicle(callback_data.vehicle_id)
        model = v.get("model", "?")
        number = v.get("vehicleNb", v.get("vehicle_nb", "?"))
        loc = v.get("currentVehicleLocation", {}) or {}
        lat = loc.get("latitude")
        lng = loc.get("longitude")
        location_str = f"{lat}, {lng}" if lat and lng else "?"
        propulsion_id = v.get("vehiclePropulsionTypeId")
        fuel = {1: "بنزینی", 2: "برقی", 3: "هیبریدی"}.get(propulsion_id, str(propulsion_id or "?"))
        battery = v.get("energyLevelPercentage", "N/A")

        text = fa.VEHICLE_DETAIL.format(
            model=model, number=number, location=location_str, fuel_type=fuel, battery=battery
        )
    except APIError as e:
        text = fa.ERROR_API.format(error=e.detail)
        lat, lng = None, None

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
    )
    if lat and lng:
        await callback.message.answer_location(latitude=lat, longitude=lng)
    await callback.answer()
