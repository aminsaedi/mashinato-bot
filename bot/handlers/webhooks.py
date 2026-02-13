"""Webhook CRUD, test, and delivery handlers."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.callbacks.factory import PageCB, SettingsCB, WebhookCB
from bot.db.models import User
from bot.keyboards.builders import back_to_menu_button, pagination_keyboard
from bot.services.api_client import APIError, CarAPI
from bot.states.webhook import WebhookForm
from bot.texts import fa

logger = logging.getLogger(__name__)
router = Router()

WEBHOOKS_PER_PAGE = 5


@router.callback_query(SettingsCB.filter(F.action == "webhooks"))
async def show_webhooks(callback: CallbackQuery, user: User, page: int = 0, **kwargs) -> None:
    api = CarAPI(user.access_token)
    try:
        result = await api.list_webhooks(skip=page * WEBHOOKS_PER_PAGE, limit=WEBHOOKS_PER_PAGE)
        webhooks = result.get("webhooks", [])
        total = result.get("total", len(webhooks))
    except APIError as e:
        await callback.message.edit_text(
            fa.ERROR_API.format(error=e.detail),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
        await callback.answer()
        return

    if not webhooks and page == 0:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=fa.WEBHOOK_CREATE,
                        callback_data=WebhookCB(action="create").pack(),
                    )
                ],
                [back_to_menu_button()],
            ]
        )
        await callback.message.edit_text(fa.WEBHOOK_EMPTY, reply_markup=kb)
        await callback.answer()
        return

    text = f"{fa.WEBHOOK_TITLE}\n\n"
    item_buttons: list[list[InlineKeyboardButton]] = []
    for wh in webhooks:
        name = wh.get("name", "?")
        active = fa.ENABLED if wh.get("is_active") else fa.DISABLED
        text += f"{active} {name}\n"
        wid = wh.get("id", 0)
        item_buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{active} {name}",
                    callback_data=WebhookCB(action="detail", webhook_id=wid).pack(),
                )
            ]
        )

    item_buttons.append(
        [
            InlineKeyboardButton(
                text=fa.WEBHOOK_CREATE,
                callback_data=WebhookCB(action="create").pack(),
            )
        ]
    )

    total_pages = max(1, (total + WEBHOOKS_PER_PAGE - 1) // WEBHOOKS_PER_PAGE)
    await callback.message.edit_text(
        text,
        reply_markup=pagination_keyboard("webhooks", page, total_pages, item_buttons),
    )
    await callback.answer()


@router.callback_query(PageCB.filter(F.section == "webhooks"))
async def webhooks_page(
    callback: CallbackQuery, callback_data: PageCB, user: User, **kwargs
) -> None:
    await show_webhooks(callback, user, page=callback_data.page)


@router.callback_query(WebhookCB.filter(F.action == "detail"))
async def webhook_detail(
    callback: CallbackQuery, callback_data: WebhookCB, user: User, **kwargs
) -> None:
    api = CarAPI(user.access_token)
    try:
        wh = await api.get_webhook(callback_data.webhook_id)
        text = (
            f"🔔 <b>{wh.get('name', '?')}</b>\n"
            f"URL: {wh.get('url', '?')}\n"
            f"وضعیت: {fa.ENABLED if wh.get('is_active') else fa.DISABLED}\n"
            f"رویدادها: {', '.join(wh.get('events', []))}\n"
        )
        if wh.get("last_triggered_at"):
            text += f"آخرین فعال‌سازی: {wh['last_triggered_at']}\n"
        if wh.get("last_error"):
            text += f"خطا: {wh['last_error']}\n"
    except APIError as e:
        text = fa.ERROR_API.format(error=e.detail)

    wid = callback_data.webhook_id
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 تغییر وضعیت",
                    callback_data=WebhookCB(action="toggle", webhook_id=wid).pack(),
                ),
                InlineKeyboardButton(
                    text="🧪 تست",
                    callback_data=WebhookCB(action="test", webhook_id=wid).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📋 تحویل‌ها",
                    callback_data=WebhookCB(action="deliveries", webhook_id=wid).pack(),
                ),
                InlineKeyboardButton(
                    text="🗑 حذف",
                    callback_data=WebhookCB(action="delete", webhook_id=wid).pack(),
                ),
            ],
            [back_to_menu_button()],
        ]
    )
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(WebhookCB.filter(F.action == "toggle"))
async def toggle_webhook(
    callback: CallbackQuery, callback_data: WebhookCB, user: User, **kwargs
) -> None:
    api = CarAPI(user.access_token)
    try:
        await api.toggle_webhook(callback_data.webhook_id)
        await callback.answer(fa.WEBHOOK_UPDATED, show_alert=True)
        # Refresh detail
        await webhook_detail(callback, callback_data, user)
    except APIError as e:
        await callback.answer(fa.ERROR_API.format(error=e.detail), show_alert=True)


@router.callback_query(WebhookCB.filter(F.action == "test"))
async def test_webhook(
    callback: CallbackQuery, callback_data: WebhookCB, user: User, **kwargs
) -> None:
    api = CarAPI(user.access_token)
    try:
        result = await api.test_webhook(callback_data.webhook_id)
        success = result.get("success", False)
        status = result.get("status_code", "?")
        duration = result.get("duration_ms", "?")
        text = f"{'✅' if success else '❌'} وضعیت: {status} | زمان: {duration}ms"
        await callback.answer(text, show_alert=True)
    except APIError as e:
        await callback.answer(fa.ERROR_API.format(error=e.detail), show_alert=True)


@router.callback_query(WebhookCB.filter(F.action == "delete"))
async def delete_webhook(
    callback: CallbackQuery, callback_data: WebhookCB, user: User, **kwargs
) -> None:
    api = CarAPI(user.access_token)
    try:
        await api.delete_webhook(callback_data.webhook_id)
        await callback.message.edit_text(
            fa.WEBHOOK_DELETED,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
    except APIError as e:
        await callback.message.edit_text(
            fa.ERROR_API.format(error=e.detail),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
    await callback.answer()


@router.callback_query(WebhookCB.filter(F.action == "deliveries"))
async def webhook_deliveries(
    callback: CallbackQuery, callback_data: WebhookCB, user: User, **kwargs
) -> None:
    api = CarAPI(user.access_token)
    try:
        result = await api.list_webhook_deliveries(callback_data.webhook_id)
        deliveries = result.get("deliveries", [])
        if not deliveries:
            await callback.message.edit_text(
                "تحویلی یافت نشد.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
            )
        else:
            text = "📋 تحویل‌ها:\n\n"
            for d in deliveries[:10]:
                status = d.get("status_code", "?")
                event = d.get("event_type", "?")
                ts = d.get("created_at", "?")
                icon = "✅" if 200 <= (status if isinstance(status, int) else 0) < 300 else "❌"
                text += f"{icon} {event} → {status} ({ts})\n"
            await callback.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
            )
    except APIError as e:
        await callback.message.edit_text(
            fa.ERROR_API.format(error=e.detail),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
    await callback.answer()


@router.callback_query(WebhookCB.filter(F.action == "create"))
async def create_webhook_start(callback: CallbackQuery, state: FSMContext, **kwargs) -> None:
    await state.set_state(WebhookForm.enter_name)
    await callback.message.edit_text(fa.WEBHOOK_NAME_PROMPT)
    await callback.answer()


@router.message(WebhookForm.enter_name)
async def webhook_enter_name(message: Message, state: FSMContext, **kwargs) -> None:
    name = message.text.strip() if message.text else ""
    if not name:
        await message.answer(fa.WEBHOOK_NAME_PROMPT)
        return
    await state.update_data(name=name)
    await state.set_state(WebhookForm.enter_url)
    await message.answer(fa.WEBHOOK_URL_PROMPT)


@router.message(WebhookForm.enter_url)
async def webhook_enter_url(message: Message, state: FSMContext, user: User, **kwargs) -> None:
    url = message.text.strip() if message.text else ""
    if not url or not url.startswith("http"):
        await message.answer(fa.WEBHOOK_URL_PROMPT)
        return

    data = await state.get_data()
    api = CarAPI(user.access_token)
    try:
        await api.create_webhook(
            {"name": data["name"], "url": url, "events": [], "is_active": True}
        )
        await message.answer(
            fa.WEBHOOK_CREATED,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_to_menu_button()]]),
        )
    except APIError as e:
        await message.answer(fa.ERROR_API.format(error=e.detail))

    await state.clear()
