"""Main menu keyboard."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.factory import MenuCB
from bot.texts import fa


def main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=fa.MENU_RENTAL,
                callback_data=MenuCB(action="rental").pack(),
            ),
            InlineKeyboardButton(
                text=fa.MENU_SEARCH,
                callback_data=MenuCB(action="search").pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text=fa.MENU_OPTIMIZATION,
                callback_data=MenuCB(action="optimization").pack(),
            ),
            InlineKeyboardButton(
                text=fa.MENU_VEHICLES,
                callback_data=MenuCB(action="vehicles").pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text=fa.MENU_ACCOUNTS,
                callback_data=MenuCB(action="accounts").pack(),
            ),
            InlineKeyboardButton(
                text=fa.MENU_SETTINGS,
                callback_data=MenuCB(action="settings").pack(),
            ),
        ],
    ]

    if is_admin:
        rows.append(
            [
                InlineKeyboardButton(
                    text=fa.MENU_ADMIN,
                    callback_data=MenuCB(action="admin").pack(),
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=rows)
