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

    payload = data.get("payload", {})

    if event_type.startswith("search."):
        vehicle = payload.get("vehicle", {})
        vehicle_str = f"{vehicle.get('model', '?')} #{vehicle.get('number', '?')}"
        location = payload.get("location", "?")
        if event_type == "search.completed":
            return fa.NOTIF_SEARCH_COMPLETED.format(vehicle=vehicle_str, location=location)

    if event_type.startswith("rental."):
        vehicle = payload.get("vehicle", {})
        vehicle_str = f"{vehicle.get('model', '?')} #{vehicle.get('number', '?')}"
        if event_type == "rental.booked":
            return fa.NOTIF_RENTAL_BOOKED.format(vehicle=vehicle_str)

    if event_type.startswith("optimization."):
        vehicle = payload.get("vehicle", {})
        vehicle_str = f"{vehicle.get('model', '?')} #{vehicle.get('number', '?')}"
        score = payload.get("score", "?")
        if event_type == "optimization.swap":
            return fa.NOTIF_OPTIMIZATION_SWAP.format(vehicle=vehicle_str, score=score)

    return f"🔔 {event_type}\n{json.dumps(payload, ensure_ascii=False, indent=2)[:500]}"


async def dispatch_notification(bot: Bot, data: dict) -> None:
    """Dispatch a webhook event to subscribed users."""
    event_type = data.get("event", data.get("event_type", "unknown"))
    account = data.get("account", data.get("account_name"))

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
