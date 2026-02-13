"""Account selection keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.factory import AccountCB
from bot.keyboards.builders import back_to_menu_button
from bot.texts import fa


def account_list_keyboard(accounts: list[str], action: str = "select") -> InlineKeyboardMarkup:
    """Build keyboard with account buttons."""
    rows = []
    for i in range(0, len(accounts), 2):
        row = []
        for acc in accounts[i : i + 2]:
            row.append(
                InlineKeyboardButton(
                    text=acc,
                    callback_data=AccountCB(action=action, account=acc).pack(),
                )
            )
        rows.append(row)
    rows.append([back_to_menu_button()])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def account_actions_keyboard(account: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=fa.ACCOUNT_STATUS_TITLE.format(account=""),
                    callback_data=AccountCB(action="status", account=account).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=fa.NEXT_FREE_TIME.format(time=""),
                    callback_data=AccountCB(action="next_free", account=account).pack(),
                ),
            ],
            [back_to_menu_button()],
        ]
    )
