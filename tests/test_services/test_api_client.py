"""Tests for API client."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("BOT_TOKEN", "test:token")
os.environ.setdefault("DATABASE_PATH", ":memory:")

from bot.services.api_client import APIError, CarAPI


def test_api_error():
    err = APIError(404, "Not found")
    assert err.status_code == 404
    assert err.detail == "Not found"
    assert "404" in str(err)


def test_car_api_headers():
    api = CarAPI("test-token")
    headers = api._headers()
    assert headers["Authorization"] == "Bearer test-token"
    assert "X-Request-ID" in headers
    assert headers["Content-Type"] == "application/json"


@pytest.mark.asyncio
async def test_car_api_get_me():
    api = CarAPI("test-token")
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"username": "test"}'
        mock_response.json.return_value = {"username": "test"}
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        result = await api.get_me()
        assert result == {"username": "test"}


@pytest.mark.asyncio
async def test_car_api_error_handling():
    api = CarAPI("test-token")
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.json.side_effect = Exception("not json")
        mock_response.content = b"error"
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        with pytest.raises(APIError) as exc_info:
            await api.get_me()
        assert exc_info.value.status_code == 500
