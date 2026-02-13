import hashlib
import hmac
import json
import logging

from aiohttp import web

from bot.config import settings

logger = logging.getLogger(__name__)


async def health_handler(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def oauth_callback_handler(request: web.Request) -> web.Response:
    """Handle OAuth2 callback from Authentik."""
    from bot.services.auth_service import handle_oauth_callback

    code = request.query.get("code")
    state = request.query.get("state")
    error = request.query.get("error")

    if error:
        logger.warning("OAuth error: %s - %s", error, request.query.get("error_description"))
        return web.Response(
            text="<html><body><h1>خطا در ورود</h1><p>لطفاً دوباره تلاش کنید.</p></body></html>",
            content_type="text/html",
        )

    if not code or not state:
        return web.Response(
            text="<html><body><h1>درخواست نامعتبر</h1></body></html>",
            content_type="text/html",
            status=400,
        )

    bot = request.app["bot"]
    try:
        await handle_oauth_callback(bot, code, state)
    except Exception:
        logger.exception("OAuth callback failed")
        return web.Response(
            text="<html><body><h1>خطا در ورود</h1><p>لطفاً دوباره تلاش کنید.</p></body></html>",
            content_type="text/html",
            status=500,
        )

    return web.Response(
        text=(
            "<html><body style='text-align:center;font-family:sans-serif;padding:50px'>"
            "<h1>✅ با موفقیت وارد شدید!</h1>"
            "<p>می‌توانید این صفحه را ببندید و به تلگرام برگردید.</p>"
            "</body></html>"
        ),
        content_type="text/html",
    )


async def webhook_receiver_handler(request: web.Request) -> web.Response:
    """Receive webhook notifications from car-api-py."""
    body = await request.read()

    if settings.webhook_secret:
        signature = request.headers.get("X-Webhook-Signature", "")
        timestamp = request.headers.get("X-Webhook-Timestamp", "")
        # Backend signs "{timestamp}.{payload}" and sends "sha256={hex}"
        message = f"{timestamp}.{body.decode()}"
        expected = hmac.new(
            settings.webhook_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        received = signature.removeprefix("sha256=")
        if not hmac.compare_digest(received, expected):
            logger.warning("Webhook signature mismatch")
            return web.json_response({"error": "invalid signature"}, status=401)

    data = json.loads(body)

    from bot.notifications.dispatcher import dispatch_notification

    bot = request.app["bot"]
    try:
        await dispatch_notification(bot, data)
    except Exception:
        logger.exception("Failed to dispatch notification")
        return web.json_response({"error": "dispatch failed"}, status=500)

    return web.json_response({"status": "ok"})


def create_app(bot=None) -> web.Application:
    app = web.Application()
    if bot:
        app["bot"] = bot
    app.router.add_get("/health", health_handler)
    app.router.add_get("/oauth/callback", oauth_callback_handler)
    app.router.add_post("/webhooks/notify", webhook_receiver_handler)
    return app
