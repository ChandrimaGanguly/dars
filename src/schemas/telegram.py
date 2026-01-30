"""Telegram webhook schemas."""

from pydantic import BaseModel, Field


class TelegramUser(BaseModel):
    """Telegram user information."""

    id: int = Field(..., description="Telegram user ID")
    is_bot: bool = Field(..., description="Whether user is a bot")
    first_name: str = Field(..., description="User's first name")
    last_name: str | None = Field(None, description="User's last name")
    username: str | None = Field(None, description="User's username")


class TelegramChat(BaseModel):
    """Telegram chat information."""

    id: int = Field(..., description="Chat ID")
    type: str = Field(..., description="Chat type", examples=["private", "group", "supergroup"])


class TelegramMessage(BaseModel):
    """Telegram message object."""

    message_id: int = Field(..., description="Message ID")
    date: int = Field(..., description="Unix timestamp")
    chat: TelegramChat = Field(..., description="Chat information")
    from_: TelegramUser = Field(..., alias="from", description="Sender information")
    text: str | None = Field(None, description="Message text")


class TelegramCallbackQuery(BaseModel):
    """Telegram callback query from inline button."""

    id: str = Field(..., description="Callback query ID")
    from_: TelegramUser = Field(..., alias="from", description="User who pressed button")
    data: str = Field(..., description="Callback data from button")


class TelegramUpdate(BaseModel):
    """Telegram update object received via webhook."""

    update_id: int = Field(..., description="Update ID (unique, sequential)")
    message: TelegramMessage | None = Field(None, description="New incoming message")
    callback_query: TelegramCallbackQuery | None = Field(
        None, description="Callback from inline button"
    )


class WebhookResponse(BaseModel):
    """Response to webhook after processing."""

    status: str = Field(..., description="Processing status", examples=["ok"])
    message_id: int | None = Field(None, description="Message ID processed")
