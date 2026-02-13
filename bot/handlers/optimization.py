"""Optimization wizard and status handlers."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.callbacks.factory import OptimizationCB
from bot.db.models import User
from bot.keyboards.builders import back_to_menu_button
from bot.services.api_client import APIError, CarAPI
from bot.states.optimization import OptimizationForm
from bot.texts import fa

logger = logging.getLogger(__name__)
router = Router()

WEIGHT_PRESETS = {
    "balanced": (0.5, 0.5),
    "distance": (0.7, 0.3),
    "preference": (0.3, 0.7),
}

IMPROVEMENT_PRESETS = [5, 10, 15, 20]


async def show_optimization_menu(callback: CallbackQuery, user: User, **kwargs) -> None:
    account = user.selected_account
    if not account:
        await callback.answer(fa.NO_ACCOUNTS, show_alert=True)
        return

    api = CarAPI(user.access_token)
    try:
        status = await api.get_optimization_status(account)
        s = status.get("status", "")
        if s in ("running", "completed"):
            text = f"{fa.OPT_STATUS_TITLE}\n"
            text += f"{fa.RENTAL_STATUS.format(status=s)}\n"
            if status.get("current_vehicle"):
                cv = status["current_vehicle"]
                text += f"\n🚗 فعلی: {cv.get('model', '?')} (امتیاز: {cv.get('total_score', '?')})"
            if status.get("best_candidate"):
                bc = status["best_candidate"]
                bm = bc.get("model", "?")
                bs = bc.get("total_score", "?")
                text += f"\n⭐ بهترین: {bm} (امتیاز: {bs})"

            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=fa.SEARCH_STOP,
                            callback_data=OptimizationCB(action="stop").pack(),
                        )
                    ],
                    [back_to_menu_button()],
                ]
            )
            await callback.message.edit_text(text, reply_markup=kb)
            await callback.answer()
            return
    except APIError:
        pass

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fa.SEARCH_START,
                    callback_data=OptimizationCB(action="start").pack(),
                )
            ],
            [back_to_menu_button()],
        ]
    )
    await callback.message.edit_text(fa.OPT_TITLE, reply_markup=kb)
    await callback.answer()


@router.callback_query(OptimizationCB.filter(F.action == "start"))
async def start_opt_wizard(
    callback: CallbackQuery, state: FSMContext, user: User, **kwargs
) -> None:
    await state.set_state(OptimizationForm.select_weights)
    await state.update_data(account=user.selected_account)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fa.OPT_BALANCED,
                    callback_data=OptimizationCB(action="weight", value="balanced").pack(),
                ),
                InlineKeyboardButton(
                    text=fa.OPT_DISTANCE,
                    callback_data=OptimizationCB(action="weight", value="distance").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fa.OPT_PREFERENCE,
                    callback_data=OptimizationCB(action="weight", value="preference").pack(),
                ),
                InlineKeyboardButton(
                    text=fa.OPT_CUSTOM,
                    callback_data=OptimizationCB(action="weight", value="custom").pack(),
                ),
            ],
            [back_to_menu_button()],
        ]
    )
    await callback.message.edit_text(fa.OPT_SELECT_WEIGHTS, reply_markup=kb)
    await callback.answer()


@router.callback_query(OptimizationCB.filter(F.action == "weight"), OptimizationForm.select_weights)
async def select_weights(
    callback: CallbackQuery, callback_data: OptimizationCB, state: FSMContext, **kwargs
) -> None:
    if callback_data.value == "custom":
        await state.set_state(OptimizationForm.custom_weights)
        await callback.message.edit_text("نسبت وزن فاصله را وارد کنید (0 تا 100):")
        await callback.answer()
        return

    dist_w, pref_w = WEIGHT_PRESETS[callback_data.value]
    await state.update_data(distance_weight=dist_w, preference_weight=pref_w)
    await _show_improvement_step(callback, state)


@router.message(OptimizationForm.custom_weights)
async def custom_weights(message: Message, state: FSMContext, **kwargs) -> None:
    try:
        val = int(message.text.strip())
        if not 0 <= val <= 100:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer("عدد بین 0 تا 100 وارد کنید:")
        return

    dist_w = val / 100
    pref_w = 1.0 - dist_w
    await state.update_data(distance_weight=dist_w, preference_weight=pref_w)

    # Build improvement step inline
    await state.set_state(OptimizationForm.min_improvement)
    rows = []
    row: list[InlineKeyboardButton] = []
    for val in IMPROVEMENT_PRESETS:
        row.append(
            InlineKeyboardButton(
                text=str(val),
                callback_data=OptimizationCB(action="improve", value=str(val)).pack(),
            )
        )
    rows.append(row)
    rows.append(
        [
            InlineKeyboardButton(
                text=fa.OPT_CUSTOM,
                callback_data=OptimizationCB(action="improve", value="custom").pack(),
            )
        ]
    )
    rows.append([back_to_menu_button()])
    await message.answer(
        fa.OPT_MIN_IMPROVEMENT,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


async def _show_improvement_step(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OptimizationForm.min_improvement)
    rows = []
    row: list[InlineKeyboardButton] = []
    for val in IMPROVEMENT_PRESETS:
        row.append(
            InlineKeyboardButton(
                text=str(val),
                callback_data=OptimizationCB(action="improve", value=str(val)).pack(),
            )
        )
    rows.append(row)
    rows.append(
        [
            InlineKeyboardButton(
                text=fa.OPT_CUSTOM,
                callback_data=OptimizationCB(action="improve", value="custom").pack(),
            )
        ]
    )
    rows.append([back_to_menu_button()])
    await callback.message.edit_text(
        fa.OPT_MIN_IMPROVEMENT,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await callback.answer()


@router.callback_query(
    OptimizationCB.filter(F.action == "improve"), OptimizationForm.min_improvement
)
async def select_improvement(
    callback: CallbackQuery, callback_data: OptimizationCB, state: FSMContext, **kwargs
) -> None:
    if callback_data.value == "custom":
        await state.set_state(OptimizationForm.custom_improvement)
        await callback.message.edit_text("حداقل بهبود امتیاز را وارد کنید:")
        await callback.answer()
        return

    await state.update_data(min_improvement=int(callback_data.value))
    await _show_preferences_step(callback, state)


@router.message(OptimizationForm.custom_improvement)
async def custom_improvement(message: Message, state: FSMContext, **kwargs) -> None:
    try:
        val = int(message.text.strip())
        if val <= 0:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer("عدد مثبت وارد کنید:")
        return

    await state.update_data(min_improvement=val)
    await state.set_state(OptimizationForm.select_preferences)

    prefs = {"awd": True, "model": True, "propulsion": False, "promotion": True, "battery": True}
    await state.update_data(preferences=prefs)
    await message.answer(
        fa.OPT_PREFERENCES_TITLE,
        reply_markup=_preferences_keyboard(prefs),
    )


async def _show_preferences_step(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OptimizationForm.select_preferences)
    prefs = {"awd": True, "model": True, "propulsion": False, "promotion": True, "battery": True}
    await state.update_data(preferences=prefs)
    await callback.message.edit_text(
        fa.OPT_PREFERENCES_TITLE,
        reply_markup=_preferences_keyboard(prefs),
    )
    await callback.answer()


def _preferences_keyboard(prefs: dict[str, bool]) -> InlineKeyboardMarkup:
    labels = {
        "awd": fa.OPT_AWD,
        "model": fa.OPT_MODEL,
        "propulsion": fa.OPT_PROPULSION,
        "promotion": fa.OPT_PROMOTIONS,
        "battery": fa.OPT_BATTERY,
    }
    rows = []
    row: list[InlineKeyboardButton] = []
    for key, label in labels.items():
        icon = fa.ENABLED if prefs.get(key) else fa.DISABLED
        row.append(
            InlineKeyboardButton(
                text=f"{icon} {label}",
                callback_data=OptimizationCB(action="pref", value=key).pack(),
            )
        )
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(
        [
            InlineKeyboardButton(
                text=fa.CONFIRM,
                callback_data=OptimizationCB(action="confirm").pack(),
            )
        ]
    )
    rows.append([back_to_menu_button()])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(
    OptimizationCB.filter(F.action == "pref"), OptimizationForm.select_preferences
)
async def toggle_preference(
    callback: CallbackQuery, callback_data: OptimizationCB, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    prefs = data.get("preferences", {})
    key = callback_data.value
    prefs[key] = not prefs.get(key, False)
    await state.update_data(preferences=prefs)
    await callback.message.edit_reply_markup(reply_markup=_preferences_keyboard(prefs))
    await callback.answer()


@router.callback_query(
    OptimizationCB.filter(F.action == "confirm"), OptimizationForm.select_preferences
)
async def confirm_optimization(
    callback: CallbackQuery, state: FSMContext, user: User, **kwargs
) -> None:
    data = await state.get_data()
    account = data.get("account", user.selected_account)
    prefs = data.get("preferences", {})

    params = {
        "scoring_weights": {
            "distance_weight": data.get("distance_weight", 0.5),
            "vehicle_preference_weight": data.get("preference_weight", 0.5),
        },
        "min_score_improvement": data.get("min_improvement", 10),
        "preference_overrides": {
            "enable_awd_preference": prefs.get("awd", True),
            "enable_model_preference": prefs.get("model", True),
            "enable_propulsion_preference": prefs.get("propulsion", False),
            "enable_promotion_preference": prefs.get("promotion", True),
            "enable_battery_preference": prefs.get("battery", True),
        },
    }

    api = CarAPI(user.access_token)
    try:
        await api.start_optimization(account, params)
        await callback.message.edit_text(
            fa.OPT_STARTED,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=fa.SEARCH_STOP,
                            callback_data=OptimizationCB(action="stop").pack(),
                        )
                    ],
                    [back_to_menu_button()],
                ]
            ),
        )
    except APIError as e:
        await callback.message.edit_text(
            fa.ERROR_API.format(error=e.detail),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )

    await state.clear()
    await callback.answer()


@router.callback_query(OptimizationCB.filter(F.action == "stop"))
async def stop_optimization(callback: CallbackQuery, user: User, **kwargs) -> None:
    account = user.selected_account
    if not account:
        await callback.answer(fa.NO_ACCOUNTS, show_alert=True)
        return

    api = CarAPI(user.access_token)
    try:
        await api.stop_optimization(account)
        await callback.message.edit_text(
            fa.OPT_STOPPED,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
    except APIError as e:
        await callback.message.edit_text(
            fa.ERROR_API.format(error=e.detail),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
    await callback.answer()
