"""OAuth2 PKCE authentication with Authentik."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import time
from datetime import datetime

import httpx
import jwt
from aiogram import Bot
from sqlalchemy import delete, select

from bot.config import settings
from bot.db.models import OAuthState, User
from bot.db.session import async_session
from bot.keyboards.main_menu import main_menu_keyboard
from bot.texts import fa

logger = logging.getLogger(__name__)


def generate_pkce() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge (S256)."""
    verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def build_authorize_url(state: str, code_challenge: str) -> str:
    """Build the Authentik authorization URL."""
    params = {
        "client_id": settings.oauth_client_id,
        "redirect_uri": settings.oauth_redirect_uri,
        "response_type": "code",
        "scope": "openid profile email groups offline_access",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{settings.oauth_authorize_url}?{qs}"


async def create_login_state(telegram_id: int, chat_id: int) -> str:
    """Create an OAuth state and return the authorize URL."""
    state = base64.urlsafe_b64encode(os.urandom(24)).decode()
    verifier, challenge = generate_pkce()

    async with async_session() as session:
        oauth_state = OAuthState(
            state=state,
            telegram_id=telegram_id,
            chat_id=chat_id,
            code_verifier=verifier,
        )
        session.add(oauth_state)
        await session.commit()

    return build_authorize_url(state, challenge)


async def handle_oauth_callback(bot: Bot, code: str, state: str) -> None:
    """Exchange auth code for tokens, store user, notify via Telegram."""
    async with async_session() as session:
        result = await session.execute(select(OAuthState).where(OAuthState.state == state))
        oauth_state = result.scalar_one_or_none()

        if not oauth_state:
            raise ValueError("Invalid or expired OAuth state")

        telegram_id = oauth_state.telegram_id
        chat_id = oauth_state.chat_id
        code_verifier = oauth_state.code_verifier

        # Exchange code for tokens
        token_data = await exchange_code(code, code_verifier)

        # Decode JWT to extract claims
        id_token = token_data.get("id_token", "")
        claims = jwt.decode(id_token, options={"verify_signature": False})

        username = claims.get("preferred_username", claims.get("sub", "unknown"))
        groups = claims.get("groups", [])

        # Extract accessible accounts from groups (format: "communauto:name")
        accounts = list(dict.fromkeys(
            g.split(":", 1)[1]
            for g in groups
            if g.startswith("communauto:") and g != f"communauto:{settings.admin_group}"
        ))
        is_admin = settings.admin_group in groups or f"communauto:{settings.admin_group}" in groups

        # Store/update user
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()

        now = datetime.utcnow().isoformat()
        expires_at = time.time() + token_data.get("expires_in", 3600)

        if user:
            user.access_token = token_data["access_token"]
            user.refresh_token = token_data.get("refresh_token")
            user.id_token = id_token
            user.token_expires_at = expires_at
            user.scopes = token_data.get("scope", "")
            user.authentik_username = username
            user.accessible_accounts = json.dumps(accounts)
            user.is_admin = int(is_admin)
            user.last_active_at = now
            if not user.selected_account and accounts:
                user.selected_account = accounts[0]
        else:
            user = User(
                telegram_id=telegram_id,
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                id_token=id_token,
                token_expires_at=expires_at,
                scopes=token_data.get("scope", ""),
                authentik_username=username,
                accessible_accounts=json.dumps(accounts),
                selected_account=accounts[0] if accounts else None,
                is_admin=int(is_admin),
                last_active_at=now,
            )
            session.add(user)

        # Clean up OAuth state
        await session.execute(delete(OAuthState).where(OAuthState.state == state))
        await session.commit()

    # Notify user in Telegram
    acct = user.selected_account or username
    msg = f"{fa.LOGIN_SUCCESS}\n{fa.ACTIVE_ACCOUNT.format(account=acct)}"
    await bot.send_message(
        chat_id,
        msg,
        reply_markup=main_menu_keyboard(is_admin=bool(is_admin)),
    )


async def exchange_code(code: str, code_verifier: str) -> dict:
    """Exchange authorization code for tokens at Authentik token endpoint."""
    data = {
        "grant_type": "authorization_code",
        "client_id": settings.oauth_client_id,
        "client_secret": settings.oauth_client_secret,
        "code": code,
        "redirect_uri": settings.oauth_redirect_uri,
        "code_verifier": code_verifier,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(settings.oauth_token_url, data=data)
        resp.raise_for_status()
        return resp.json()


async def refresh_tokens(user: User) -> bool:
    """Refresh the user's access token using their refresh token."""
    if not user.refresh_token:
        return False

    data = {
        "grant_type": "refresh_token",
        "client_id": settings.oauth_client_id,
        "client_secret": settings.oauth_client_secret,
        "refresh_token": user.refresh_token,
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(settings.oauth_token_url, data=data)
            resp.raise_for_status()
            token_data = resp.json()
    except Exception:
        logger.warning("Token refresh failed for user %s", user.telegram_id)
        return False

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == user.telegram_id))
        db_user = result.scalar_one_or_none()
        if db_user:
            db_user.access_token = token_data["access_token"]
            if "refresh_token" in token_data:
                db_user.refresh_token = token_data["refresh_token"]
            db_user.token_expires_at = time.time() + token_data.get("expires_in", 3600)
            db_user.last_active_at = datetime.utcnow().isoformat()
            await session.commit()
            # Update the in-memory user object too
            user.access_token = db_user.access_token
            user.refresh_token = db_user.refresh_token
            user.token_expires_at = db_user.token_expires_at

    return True


async def get_user(telegram_id: int) -> User | None:
    """Get user from database."""
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()


async def logout_user(telegram_id: int) -> None:
    """Remove user tokens (logout)."""
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.access_token = None
            user.refresh_token = None
            user.id_token = None
            user.token_expires_at = None
            await session.commit()
