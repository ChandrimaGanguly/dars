"""Telegram webhook endpoint.

Security (SEC-002):
- Webhook is protected by X-Telegram-Bot-Api-Secret-Token verification
- All requests must include valid secret token
- Prevents unauthorized webhook calls
"""

from fastapi import APIRouter, Depends

from src.auth.telegram import verify_telegram_webhook
from src.logging import get_logger
from src.schemas.telegram import TelegramUpdate, WebhookResponse

router = APIRouter()
logger = get_logger(__name__)


@router.post("/webhook", response_model=WebhookResponse, tags=["Telegram"])
async def telegram_webhook(
    update: TelegramUpdate,
    _authenticated: bool = Depends(verify_telegram_webhook),
) -> WebhookResponse:
    """Receive and process Telegram bot updates.

    This endpoint receives updates from the Telegram Bot API via webhook.
    It processes commands, messages, and callback queries.

    Security (SEC-002):
    - Requires X-Telegram-Bot-Api-Secret-Token header
    - Token must match TELEGRAM_SECRET_TOKEN environment variable
    - Returns 401 if missing or invalid

    Setup Instructions:
    1. Generate a random secret token (min 8 chars, recommend 32+)
    2. Set TELEGRAM_SECRET_TOKEN environment variable
    3. Register webhook with Telegram:
       ```bash
       curl -X POST https://api.telegram.org/bot<TOKEN>/setWebhook \
         -d url=https://your-app.com/webhook \
         -d secret_token=<your-secret-token>
       ```

    Args:
        update: Telegram update object containing message or callback data.
        _authenticated: Authentication dependency (injected by FastAPI).

    Returns:
        WebhookResponse confirming processing.

    Raises:
        HTTPException: If authentication fails (401) or processing fails.

    Example Request:
        POST /webhook
        Headers:
            X-Telegram-Bot-Api-Secret-Token: your-secret-here
        Body:
            {"update_id": 123, "message": {...}}
    """
    logger.info(f"Received Telegram update: {update.update_id}")

    # TODO: Implement webhook processing
    # - Route to appropriate message handler
    # - Handle /start, /practice, /streak, /help commands
    # - Process callback queries from inline buttons
    # - Send responses via Telegram API

    message_id = None
    if update.message:
        message_id = update.message.message_id
        logger.debug(f"Message from user {update.message.from_.id}: {update.message.text}")
    elif update.callback_query:
        # Callback queries don't have message_id directly
        logger.debug(f"Callback query from user {update.callback_query.from_.id}")

    return WebhookResponse(status="ok", message_id=message_id)
