"""Telegram webhook endpoint.

Security (SEC-002):
- Webhook is protected by X-Telegram-Bot-Api-Secret-Token verification
- All requests must include valid secret token
- Prevents unauthorized webhook calls
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.telegram import verify_telegram_webhook
from src.database import get_session
from src.logging import get_logger
from src.schemas.telegram import TelegramMessage, TelegramUpdate, WebhookResponse
from src.services import StudentService, TelegramClient

router = APIRouter()
logger = get_logger(__name__)


@router.post("/webhook", response_model=WebhookResponse, tags=["Telegram"])
async def telegram_webhook(
    update: TelegramUpdate,
    _authenticated: bool = Depends(verify_telegram_webhook),
    db: AsyncSession = Depends(get_session),
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

    # Process message if present
    message_id: int | None = None
    try:
        if update.message and update.message.text:
            await _handle_message(update.message, db)
            message_id = update.message.message_id
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        # Still return 200 to avoid Telegram retrying

    return WebhookResponse(status="ok", message_id=message_id)


async def _handle_message(message: TelegramMessage, db: AsyncSession) -> None:
    """Handle text message - MINIMAL IMPLEMENTATION.

    Args:
        message: Telegram message object
        db: Database session
    """
    text = message.text or ""
    chat_id = message.chat.id
    telegram_id = message.from_.id
    first_name = message.from_.first_name

    # Initialize services
    telegram = TelegramClient()
    student_service = StudentService()

    # Simple command routing
    if text.startswith("/start"):
        # Register student
        student = await student_service.get_or_create(db, telegram_id, first_name)
        welcome_msg = (
            f"Welcome to Dars, {student.name}! 🎓\n\n"
            f"I'm your AI tutor. Send /practice to start learning!"
        )
        await telegram.send_message(chat_id, welcome_msg)
        logger.info(f"Handled /start for user {telegram_id}")

    elif text.startswith("/practice"):
        # Stub response for Phase 3
        await telegram.send_message(
            chat_id,
            "Practice sessions are coming in Phase 3! Stay tuned. 📚",
        )
        logger.info(f"Handled /practice stub for user {telegram_id}")

    else:
        # Unknown command
        await telegram.send_message(
            chat_id,
            "I don't understand that command yet. Try /start to begin!",
        )
        logger.info(f"Unknown command from user {telegram_id}: {text}")
