"""Search flow keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.factory import SearchCB
from bot.keyboards.builders import back_to_menu_button
from bot.texts import fa

RADIUS_PRESETS = [
    ("500m", "500"),
    ("1km", "1000"),
    ("2km", "2000"),
    ("5km", "5000"),
    ("10km", "10000"),
]


def radius_keyboard() -> InlineKeyboardMarkup:
    rows = []
    row: list[InlineKeyboardButton] = []
    for label, value in RADIUS_PRESETS:
        row.append(
            InlineKeyboardButton(
                text=label,
                callback_data=SearchCB(action="radius", value=value).pack(),
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
                text=fa.SEARCH_CUSTOM_RADIUS,
                callback_data=SearchCB(action="radius", value="custom").pack(),
            )
        ]
    )
    rows.append([back_to_menu_button()])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def filters_keyboard(filters: dict[str, bool]) -> InlineKeyboardMarkup:
    """Build toggle-able filter buttons."""
    filter_labels = {
        "no_prius": fa.SEARCH_FILTER_NO_PRIUS,
        "no_ev": fa.SEARCH_FILTER_NO_EV,
        "snow_car": fa.SEARCH_FILTER_SNOW,
    }
    rows = []
    for key, label in filter_labels.items():
        enabled = filters.get(key, False)
        icon = fa.ENABLED if enabled else fa.DISABLED
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{icon} {label}",
                    callback_data=SearchCB(action="filter", value=key).pack(),
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=fa.SEARCH_START,
                callback_data=SearchCB(action="confirm").pack(),
            )
        ]
    )
    rows.append([back_to_menu_button()])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def search_status_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fa.SEARCH_STOP,
                    callback_data=SearchCB(action="stop").pack(),
                ),
            ],
            [back_to_menu_button()],
        ]
    )
