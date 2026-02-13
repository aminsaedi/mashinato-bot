"""Rental action keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.factory import MenuCB, RentalCB, SearchCB
from bot.keyboards.builders import back_to_menu_button
from bot.texts import fa


def rental_actions_keyboard(account: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fa.RENTAL_START_TRIP,
                    callback_data=RentalCB(action="start_trip", account=account).pack(),
                ),
                InlineKeyboardButton(
                    text=fa.RENTAL_EXTEND,
                    callback_data=RentalCB(action="extend", account=account).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fa.RENTAL_FUEL_CARD,
                    callback_data=RentalCB(action="fuel_card", account=account).pack(),
                ),
                InlineKeyboardButton(
                    text=fa.RENTAL_CANCEL,
                    callback_data=RentalCB(action="cancel", account=account).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fa.RENTAL_TRANSFER,
                    callback_data=RentalCB(action="transfer", account=account).pack(),
                ),
                InlineKeyboardButton(
                    text=fa.RENTAL_CONTINUE,
                    callback_data=RentalCB(action="continue", account=account).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fa.RENTAL_END_TRIP,
                    callback_data=RentalCB(action="end_trip", account=account).pack(),
                ),
            ],
            [back_to_menu_button()],
        ]
    )


def no_rental_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fa.MENU_SEARCH,
                    callback_data=SearchCB(action="start").pack(),
                ),
            ],
            [back_to_menu_button()],
        ]
    )


def rental_cancel_confirm_keyboard(account: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fa.CONFIRM,
                    callback_data=RentalCB(action="cancel_yes", account=account).pack(),
                ),
                InlineKeyboardButton(
                    text=fa.CANCEL,
                    callback_data=MenuCB(action="rental").pack(),
                ),
            ]
        ]
    )
