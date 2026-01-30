"""Telegram webhook authentication.

The /webhook endpoint is authenticated using Telegram's secret token mechanism.
Telegram sends X-Telegram-Bot-Api-Secret-Token header with each webhook request.

Security (SEC-002):
- Verifies X-Telegram-Bot-Api-Secret-Token header
- Prevents unauthorized webhook calls
- More secure than Bearer token (doesn't expose bot token)
"""

from typing import Annotated

from fastapi import Header, HTTPException, status

from src.config import get_settings
from src.errors.exceptions import ERR_AUTH_FAILED, ERR_AUTH_MISSING
from src.logging import get_logger

logger = get_logger(__name__)


async def verify_telegram_webhook(
    x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None,
) -> bool:
    """Verify Telegram webhook authentication via secret token.

    Telegram's recommended webhook authentication uses a secret token
    that you set when registering the webhook. Telegram includes this
    token in the X-Telegram-Bot-Api-Secret-Token header with each request.

    This is more secure than Bearer token auth because:
    - The bot token itself is never transmitted
    - Each webhook can have a unique secret
    - Easier to rotate without changing bot token

    Security Implementation (SEC-002):
    - Checks X-Telegram-Bot-Api-Secret-Token header presence
    - Verifies token matches configured TELEGRAM_SECRET_TOKEN
    - Returns 401 Unauthorized if missing or invalid
    - Logs failed authentication attempts

    Args:
        x_telegram_bot_api_secret_token: Secret token from Telegram webhook header.

    Returns:
        True if authentication successful.

    Raises:
        HTTPException: If authentication fails (401).

    Example:
        Set webhook with secret token:
        ```bash
        curl -X POST https://api.telegram.org/bot<TOKEN>/setWebhook \
          -d url=https://your-app.com/webhook \
          -d secret_token=your-secret-here
        ```

    References:
        https://core.telegram.org/bots/api#setwebhook
    """
    if not x_telegram_bot_api_secret_token:
        logger.warning("Telegram webhook called without secret token header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Telegram-Bot-Api-Secret-Token header",
            headers={"error_code": ERR_AUTH_MISSING},
        )

    # Get configured secret token from environment
    settings = get_settings()
    expected_token = settings.telegram_secret_token

    if not expected_token:
        logger.error("TELEGRAM_SECRET_TOKEN not configured in environment")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret token not configured",
        )

    # Constant-time comparison to prevent timing attacks
    if not _secure_compare(x_telegram_bot_api_secret_token, expected_token):
        logger.warning("Telegram webhook called with invalid secret token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid secret token",
            headers={"error_code": ERR_AUTH_FAILED},
        )

    return True


def _secure_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks.

    Standard string comparison (==) can leak information about string
    similarity through timing differences. This implementation always
    compares all characters.

    Args:
        a: First string.
        b: Second string.

    Returns:
        True if strings are equal, False otherwise.
    """
    if len(a) != len(b):
        return False

    result = 0
    for char_a, char_b in zip(a, b, strict=True):
        result |= ord(char_a) ^ ord(char_b)

    return result == 0
