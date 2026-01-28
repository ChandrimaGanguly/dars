"""Unit tests for authentication middleware.

Tests:
- Telegram webhook authentication
- Admin authentication
- Student authentication
"""

import pytest
from fastapi import HTTPException

from src.auth.admin import verify_admin
from src.auth.student import verify_student
from src.auth.telegram import verify_telegram_webhook


@pytest.mark.unit
class TestTelegramAuth:
    """Tests for Telegram webhook authentication."""

    @pytest.mark.asyncio
    async def test_verify_webhook_valid_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful webhook authentication with valid token."""
        # Mock settings with test token
        test_token = "test_bot_token_123"
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", test_token)
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("TELEGRAM_WEBHOOK_URL", "https://test.com/webhook")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")

        # Reset settings singleton
        import src.config

        src.config._settings = None

        # Test with valid Bearer token
        result = await verify_telegram_webhook(authorization=f"Bearer {test_token}")
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_webhook_missing_header(self) -> None:
        """Test webhook authentication fails with missing Authorization header."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_telegram_webhook(authorization=None)

        assert exc_info.value.status_code == 401
        assert "Missing Authorization header" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_webhook_invalid_format(self) -> None:
        """Test webhook authentication fails with invalid header format."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_telegram_webhook(authorization="InvalidFormat")

        assert exc_info.value.status_code == 401
        assert "Invalid Authorization header format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_webhook_wrong_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test webhook authentication fails with wrong token."""
        # Mock settings
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "correct_token")
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("TELEGRAM_WEBHOOK_URL", "https://test.com/webhook")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")

        # Reset settings singleton
        import src.config

        src.config._settings = None

        with pytest.raises(HTTPException) as exc_info:
            await verify_telegram_webhook(authorization="Bearer wrong_token")

        assert exc_info.value.status_code == 401
        assert "Invalid bot token" in exc_info.value.detail


@pytest.mark.unit
class TestAdminAuth:
    """Tests for admin authentication."""

    @pytest.mark.asyncio
    async def test_verify_admin_valid_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful admin authentication with valid ID."""
        # Mock settings with test admin IDs
        monkeypatch.setenv("ADMIN_TELEGRAM_IDS", "123456,789012")
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        monkeypatch.setenv("TELEGRAM_WEBHOOK_URL", "https://test.com/webhook")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")

        # Reset settings singleton
        import src.config

        src.config._settings = None

        # Test with valid admin ID
        result = await verify_admin(x_admin_id="123456")
        assert result == 123456

    @pytest.mark.asyncio
    async def test_verify_admin_missing_header(self) -> None:
        """Test admin authentication fails with missing X-Admin-ID header."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_admin(x_admin_id=None)

        assert exc_info.value.status_code == 401
        assert "Missing admin credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_admin_invalid_format(self) -> None:
        """Test admin authentication fails with invalid ID format."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_admin(x_admin_id="not_a_number")

        assert exc_info.value.status_code == 400
        assert "must be a valid integer" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_admin_unauthorized_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test admin authentication fails with unauthorized ID."""
        # Mock settings with test admin IDs
        monkeypatch.setenv("ADMIN_TELEGRAM_IDS", "123456,789012")
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        monkeypatch.setenv("TELEGRAM_WEBHOOK_URL", "https://test.com/webhook")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")

        # Reset settings singleton
        import src.config

        src.config._settings = None

        with pytest.raises(HTTPException) as exc_info:
            await verify_admin(x_admin_id="999999")

        assert exc_info.value.status_code == 403
        assert "Not authorized" in exc_info.value.detail


@pytest.mark.unit
class TestStudentAuth:
    """Tests for student authentication."""

    @pytest.mark.asyncio
    async def test_verify_student_valid_id(self) -> None:
        """Test successful student authentication with valid ID."""
        result = await verify_student(x_student_id="123456")
        assert result == 123456

    @pytest.mark.asyncio
    async def test_verify_student_missing_header(self) -> None:
        """Test student authentication fails with missing X-Student-ID header."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_student(x_student_id=None)

        assert exc_info.value.status_code == 401
        assert "Missing student credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_student_invalid_format(self) -> None:
        """Test student authentication fails with invalid ID format."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_student(x_student_id="not_a_number")

        assert exc_info.value.status_code == 400
        assert "must be a valid integer" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_student_negative_id(self) -> None:
        """Test student authentication fails with negative ID."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_student(x_student_id="-123")

        assert exc_info.value.status_code == 400
        assert "Invalid student ID" in exc_info.value.detail
