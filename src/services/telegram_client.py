"""Minimal Telegram Bot API wrapper."""

import httpx

from src.config import get_settings
from src.logging import get_logger

logger = get_logger(__name__)


class TelegramClient:
    """Send messages via Telegram Bot API."""

    def __init__(self) -> None:
        """Initialize Telegram client with bot token from settings."""
        settings = get_settings()
        self.bot_token = settings.telegram_bot_token
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def send_message(self, chat_id: int, text: str) -> bool:
        """Send text message to user.

        Args:
            chat_id: Telegram chat ID
            text: Message text to send

        Returns:
            True if message sent successfully, False otherwise
        """
        url = f"{self.base_url}/sendMessage"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json={"chat_id": chat_id, "text": text},
                    timeout=5.0,
                )
                response.raise_for_status()
                logger.info(f"Message sent to chat {chat_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to send message to {chat_id}: {e}")
            return False
