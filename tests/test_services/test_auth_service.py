"""Tests for auth service."""

import os

os.environ.setdefault("BOT_TOKEN", "test:token")
os.environ.setdefault("DATABASE_PATH", ":memory:")

from bot.services.auth_service import build_authorize_url, generate_pkce


def test_generate_pkce():
    verifier, challenge = generate_pkce()
    assert len(verifier) > 20
    assert len(challenge) > 20
    assert verifier != challenge


def test_build_authorize_url():
    url = build_authorize_url("test-state", "test-challenge")
    assert "test-state" in url
    assert "test-challenge" in url
    assert "response_type=code" in url
    assert "code_challenge_method=S256" in url
