"""Application configuration management."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://localhost/dars"

    # Telegram
    telegram_bot_token: str = ""

    # Anthropic Claude API
    anthropic_api_key: str = ""

    # Admin
    admin_telegram_ids: str = ""  # Comma-separated list

    # Environment
    environment: str = "development"

    # Logging
    log_level: str = "INFO"

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = False

    def get_admin_ids(self) -> list[int]:
        """Parse and return admin IDs as a list of integers.

        Returns:
            List of admin Telegram IDs.
        """
        if not self.admin_telegram_ids:
            return []
        return [int(id.strip()) for id in self.admin_telegram_ids.split(",") if id.strip()]


_settings: Settings | None = None


def get_settings() -> Settings:
    """Get application settings (singleton pattern).

    Returns:
        Settings instance.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
