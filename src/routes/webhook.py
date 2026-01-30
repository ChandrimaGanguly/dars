"""Telegram webhook endpoint."""

from fastapi import APIRouter

from src.schemas.telegram import TelegramUpdate, WebhookResponse

router = APIRouter()


@router.post("/webhook", response_model=WebhookResponse, tags=["Telegram"])
async def telegram_webhook(update: TelegramUpdate) -> WebhookResponse:
    """Receive and process Telegram bot updates.

    This endpoint receives updates from the Telegram Bot API via webhook.
    It processes commands, messages, and callback queries.

    Args:
        update: Telegram update object containing message or callback data.

    Returns:
        WebhookResponse confirming processing.

    Raises:
        HTTPException: If webhook processing fails.
    """
    # TODO: Implement webhook processing
    # - Route to appropriate message handler
    # - Handle /start, /practice, /streak, /help commands
    # - Process callback queries from inline buttons
    # - Send responses via Telegram API

    message_id = None
    if update.message:
        message_id = update.message.message_id
    elif update.callback_query:
        # Callback queries don't have message_id directly
        pass

    return WebhookResponse(status="ok", message_id=message_id)
