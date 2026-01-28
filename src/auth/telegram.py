"""Telegram webhook authentication.

The /webhook endpoint is authenticated using the Telegram bot token
as a Bearer token in the Authorization header.
"""

from typing import Annotated

from fastapi import Header, HTTPException, status

from src.config import get_settings
from src.errors.exceptions import ERR_AUTH_FAILED, ERR_AUTH_MISSING


async def verify_telegram_webhook(authorization: Annotated[str | None, Header()] = None) -> bool:
    """Verify Telegram webhook authentication via Bearer token.

    The Telegram webhook must include:
        Authorization: Bearer <telegram_bot_token>

    Args:
        authorization: Authorization header value.

    Returns:
        True if authentication successful.

    Raises:
        HTTPException: If authentication fails (401).
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"error_code": ERR_AUTH_MISSING},
        )

    # Extract Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format (expected: Bearer <token>)",
            headers={"error_code": ERR_AUTH_FAILED},
        )

    token = parts[1]

    # Verify token matches configured bot token
    settings = get_settings()
    if token != settings.telegram_bot_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bot token",
            headers={"error_code": ERR_AUTH_FAILED},
        )

    return True
