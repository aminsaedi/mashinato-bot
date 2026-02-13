"""Route webhook events to subscribed Telegram users."""

from __future__ import annotations

import json
import logging
from typing import Any

from aiogram import Bot
from sqlalchemy import select

from bot.db.models import NotificationPreference, User
from bot.db.session import async_session
from bot.texts import fa

logger = logging.getLogger(__name__)

# Event type → message formatter
EVENT_FORMATTERS: dict[str, Any] = {}


def format_event(event_type: str, data: dict) -> str | None:
    """Format a webhook event into a Persian message."""
    formatter = EVENT_FORMATTERS.get(event_type)
    if formatter:
        return formatter(data)

    # Backend sends {"id", "type", "timestamp", "data": {...}}
    payload = data.get("data", data.get("payload", data))

    def _vehicle_str(v: dict) -> str:
        model = v.get("model", "?")
        nb = v.get("vehicle_nb", v.get("number", "?"))
        return f"{model} #{nb}"

    if event_type.startswith("search."):
        vehicle = payload.get("vehicle", {})
        account = payload.get("account", "?")
        if event_type == "search.completed":
            return fa.NOTIF_SEARCH_COMPLETED.format(vehicle=_vehicle_str(vehicle), location=account)
        if event_type == "search.started":
            return f"🔍 جستجو شروع شد\nحساب: {account}"
        if event_type == "search.stopped":
            return f"⏹ جستجو متوقف شد\nحساب: {account}"
        if event_type == "search.error":
            error = payload.get("error", "خطای نامشخص")
            return f"❌ خطا در جستجو\nحساب: {account}\n{error}"

    if event_type.startswith("rental."):
        vehicle = payload.get("vehicle", {})
        account = payload.get("account", "?")
        vs = _vehicle_str(vehicle)
        if event_type in ("rental.created", "rental.booked"):
            return fa.NOTIF_RENTAL_BOOKED.format(vehicle=vs)
        if event_type == "rental.cancelled":
            return f"❌ اجاره لغو شد\n🚗 {vs}\nحساب: {account}"
        if event_type == "rental.trip_started":
            return f"▶️ سفر شروع شد\n🚗 {vs}\nحساب: {account}"
        if event_type == "rental.trip_ended":
            return f"⏹ سفر پایان یافت\n🚗 {vs}\nحساب: {account}"
        if event_type == "rental.extended":
            return f"⏰ اجاره تمدید شد\n🚗 {vs}\nحساب: {account}"
        if event_type == "rental.transferred":
            to_account = payload.get("to_account", "?")
            return f"🔄 اجاره انتقال یافت\n🚗 {vs}\nاز: {account} → به: {to_account}"

    if event_type.startswith("optimization."):
        vehicle = payload.get("vehicle", {})
        score = payload.get("score", "?")
        if event_type == "optimization.swap":
            return fa.NOTIF_OPTIMIZATION_SWAP.format(vehicle=_vehicle_str(vehicle), score=score)

    return f"🔔 {event_type}\n{json.dumps(payload, ensure_ascii=False, indent=2)[:500]}"


async def dispatch_notification(bot: Bot, data: dict) -> None:
    """Dispatch a webhook event to subscribed users.

    The backend sends: {"id": "evt_...", "type": "search.completed",
                        "timestamp": "...", "data": {"account": "...", ...}}
    """
    event_type = data.get("type", data.get("event", data.get("event_type", "unknown")))
    event_data = data.get("data", data)
    account = event_data.get("account", data.get("account", data.get("account_name")))

    message = format_event(event_type, data)
    if not message:
        logger.debug("No message for event %s", event_type)
        return

    async with async_session() as session:
        # Find users who:
        # 1. Have this event enabled (or no preference = default enabled)
        # 2. Have access to the account (if account-specific)
        query = select(User).where(User.access_token.isnot(None))
        result = await session.execute(query)
        users = result.scalars().all()

        for user in users:
            # Check account access
            if account and user.accessible_accounts:
                try:
                    accounts = json.loads(user.accessible_accounts)
                    if account not in accounts:
                        continue
                except (json.JSONDecodeError, TypeError):
                    continue

            # Check notification preference
            pref_query = select(NotificationPreference).where(
                NotificationPreference.telegram_id == user.telegram_id,
                NotificationPreference.event_type == event_type,
            )
            pref_result = await session.execute(pref_query)
            pref = pref_result.scalar_one_or_none()

            if pref and not pref.enabled:
                continue

            try:
                await bot.send_message(user.telegram_id, message)
            except Exception:
                logger.warning(
                    "Failed to send notification to user %s", user.telegram_id, exc_info=True
                )
