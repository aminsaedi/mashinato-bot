from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram Bot
    bot_token: str

    # Car API
    api_base_url: str = "https://kuber-carapi.aminamin.xyz"

    # OAuth2 / Authentik
    oauth_client_id: str = "mashinato-bot"
    oauth_client_secret: str = ""
    oauth_authorize_url: str = "https://kuber-auth.aminamin.xyz/application/o/authorize/"
    oauth_token_url: str = "https://kuber-auth.aminamin.xyz/application/o/token/"
    oauth_userinfo_url: str = "https://kuber-auth.aminamin.xyz/application/o/userinfo/"
    oauth_redirect_uri: str = "https://kuber-mashinato-bot.aminamin.xyz/oauth/callback"

    # Webhook server
    webhook_secret: str = ""
    webhook_server_host: str = "0.0.0.0"
    webhook_server_port: int = 8080

    # Database
    database_path: str = "data/bot.db"

    # Admin
    admin_group: str = "mashinato-admin"

    # Logging
    log_level: str = "INFO"

    @property
    def database_url(self) -> str:
        path = Path(self.database_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{path}"


settings = Settings()
