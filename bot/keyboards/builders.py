"""Reusable keyboard builder utilities."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.factory import ConfirmCB, MenuCB, PageCB
from bot.texts import fa


def back_to_menu_button() -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=fa.MENU_HOME,
        callback_data=MenuCB(action="main").pack(),
    )


def back_button(callback_data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=fa.BACK, callback_data=callback_data)


def confirm_cancel_keyboard(action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fa.CONFIRM,
                    callback_data=ConfirmCB(action=action, confirmed=True).pack(),
                ),
                InlineKeyboardButton(
                    text=fa.CANCEL,
                    callback_data=ConfirmCB(action=action, confirmed=False).pack(),
                ),
            ]
        ]
    )


def pagination_keyboard(
    section: str,
    current_page: int,
    total_pages: int,
    extra_buttons: list[list[InlineKeyboardButton]] | None = None,
) -> InlineKeyboardMarkup:
    """Build a pagination keyboard with prev/next buttons."""
    rows: list[list[InlineKeyboardButton]] = []

    if extra_buttons:
        rows.extend(extra_buttons)

    nav_row: list[InlineKeyboardButton] = []
    if current_page > 0:
        nav_row.append(
            InlineKeyboardButton(
                text=fa.PAGE_PREV,
                callback_data=PageCB(section=section, page=current_page - 1).pack(),
            )
        )
    nav_row.append(
        InlineKeyboardButton(
            text=fa.PAGE_INFO.format(current=current_page + 1, total=total_pages),
            callback_data="noop",
        )
    )
    if current_page < total_pages - 1:
        nav_row.append(
            InlineKeyboardButton(
                text=fa.PAGE_NEXT,
                callback_data=PageCB(section=section, page=current_page + 1).pack(),
            )
        )
    rows.append(nav_row)
    rows.append([back_to_menu_button()])

    return InlineKeyboardMarkup(inline_keyboard=rows)
