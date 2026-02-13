"""Tests for web server."""

import os
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp.test_utils import TestClient, TestServer

os.environ.setdefault("BOT_TOKEN", "test:token")
os.environ.setdefault("DATABASE_PATH", ":memory:")

from bot.web.server import create_app


@pytest.mark.asyncio
async def test_health_endpoint():
    app = create_app(bot=AsyncMock())
    from aiohttp.test_utils import TestClient, TestServer

    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/health")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_oauth_callback_missing_params():
    app = create_app(bot=AsyncMock())
    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/oauth/callback")
        assert resp.status == 400


@pytest.mark.asyncio
async def test_oauth_callback_error():
    app = create_app(bot=AsyncMock())
    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/oauth/callback?error=access_denied&error_description=test")
        assert resp.status == 200
        text = await resp.text()
        assert "خطا" in text


@pytest.mark.asyncio
async def test_webhook_receiver_no_signature():
    with patch("bot.config.settings") as mock_settings:
        mock_settings.webhook_secret = ""
        mock_settings.webhook_server_host = "0.0.0.0"
        mock_settings.webhook_server_port = 8080

        app = create_app(bot=AsyncMock())

        with patch("bot.notifications.dispatcher.dispatch_notification", new_callable=AsyncMock):
            async with TestClient(TestServer(app)) as client:
                resp = await client.post(
                    "/webhooks/notify",
                    json={"event": "test", "payload": {}},
                )
                assert resp.status == 200
