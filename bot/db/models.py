from sqlalchemy import Column, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    telegram_id = Column(Integer, primary_key=True)
    telegram_username = Column(Text, nullable=True)
    telegram_name = Column(Text, nullable=True)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    id_token = Column(Text, nullable=True)
    token_expires_at = Column(Float, nullable=True)
    scopes = Column(Text, nullable=True)
    authentik_username = Column(Text, nullable=True)
    accessible_accounts = Column(Text, nullable=True)  # JSON array
    selected_account = Column(Text, nullable=True)
    is_admin = Column(Integer, default=0)
    created_at = Column(Text, server_default="CURRENT_TIMESTAMP")
    last_active_at = Column(Text, nullable=True)


class OAuthState(Base):
    __tablename__ = "oauth_states"

    state = Column(Text, primary_key=True)
    telegram_id = Column(Integer, nullable=False)
    chat_id = Column(Integer, nullable=False)
    code_verifier = Column(Text, nullable=False)
    created_at = Column(Text, server_default="CURRENT_TIMESTAMP")


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    telegram_id = Column(
        Integer,
        ForeignKey("users.telegram_id"),
        primary_key=True,
    )
    event_type = Column(Text, primary_key=True)
    enabled = Column(Integer, default=1)
