"""Common endpoints: accessories, vehicle models, zones."""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.db.models import User
from bot.services.api_client import APIError, CarAPI
from bot.texts import fa

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("accessories"))
async def cmd_accessories(message: Message, user: User, **kwargs) -> None:
    api = CarAPI(user.access_token)
    try:
        items = await api.get_accessories()
        if not items:
            await message.answer("لیست لوازم جانبی خالی است.")
            return
        text = "🔧 لوازم جانبی:\n\n"
        for item in items:
            name = item.get("name", item.get("description", "?"))
            text += f"• {name}\n"
        await message.answer(text)
    except APIError as e:
        await message.answer(fa.ERROR_API.format(error=e.detail))


@router.message(Command("models"))
async def cmd_vehicle_models(message: Message, user: User, **kwargs) -> None:
    api = CarAPI(user.access_token)
    try:
        models = await api.get_vehicle_models()
        if not models:
            await message.answer("لیست مدل‌ها خالی است.")
            return
        text = "🚙 مدل‌های خودرو:\n\n"
        for m in models:
            text += f"• {m}\n"
        await message.answer(text)
    except APIError as e:
        await message.answer(fa.ERROR_API.format(error=e.detail))


@router.message(Command("zones"))
async def cmd_zones(message: Message, user: User, **kwargs) -> None:
    api = CarAPI(user.access_token)
    try:
        result = await api.get_zones()
        zones = result.get("zones", []) if isinstance(result, dict) else result
        text = f"🗺 مناطق سرویس‌دهی: {len(zones)} منطقه"
        await message.answer(text)
    except APIError as e:
        await message.answer(fa.ERROR_API.format(error=e.detail))
