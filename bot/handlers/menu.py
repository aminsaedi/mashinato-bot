"""Main menu navigation handler."""

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.callbacks.factory import MenuCB
from bot.db.models import User
from bot.keyboards.main_menu import main_menu_keyboard
from bot.texts import fa

router = Router()


@router.callback_query(MenuCB.filter(F.action == "main"))
async def show_main_menu(callback: CallbackQuery, user: User, **kwargs) -> None:
    account = user.selected_account or user.authentik_username or ""
    text = f"{fa.MAIN_MENU_TITLE}\n{fa.ACTIVE_ACCOUNT.format(account=account)}"
    await callback.message.edit_text(
        text,
        reply_markup=main_menu_keyboard(is_admin=bool(user.is_admin)),
    )
    await callback.answer()


@router.callback_query(MenuCB.filter(F.action == "rental"))
async def menu_rental(callback: CallbackQuery, user: User, **kwargs) -> None:
    from bot.handlers.rental import show_current_rental

    await show_current_rental(callback, user)


@router.callback_query(MenuCB.filter(F.action == "search"))
async def menu_search(callback: CallbackQuery, user: User, **kwargs) -> None:
    from bot.handlers.search import show_search_menu

    await show_search_menu(callback, user)


@router.callback_query(MenuCB.filter(F.action == "optimization"))
async def menu_optimization(callback: CallbackQuery, user: User, **kwargs) -> None:
    from bot.handlers.optimization import show_optimization_menu

    await show_optimization_menu(callback, user)


@router.callback_query(MenuCB.filter(F.action == "vehicles"))
async def menu_vehicles(callback: CallbackQuery, user: User, **kwargs) -> None:
    from bot.handlers.vehicles import show_vehicles_list

    await show_vehicles_list(callback, user)


@router.callback_query(MenuCB.filter(F.action == "accounts"))
async def menu_accounts(callback: CallbackQuery, user: User, **kwargs) -> None:
    from bot.handlers.account import show_accounts

    await show_accounts(callback, user)


@router.callback_query(MenuCB.filter(F.action == "settings"))
async def menu_settings(callback: CallbackQuery, user: User, **kwargs) -> None:
    from bot.handlers.settings import show_settings

    await show_settings(callback, user)


@router.callback_query(MenuCB.filter(F.action == "admin"))
async def menu_admin(callback: CallbackQuery, user: User, **kwargs) -> None:
    from bot.handlers.admin.system import show_admin_panel

    if not user.is_admin:
        await callback.answer(fa.ADMIN_NOT_AUTHORIZED, show_alert=True)
        return
    await show_admin_panel(callback, user)
