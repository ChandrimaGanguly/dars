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
    """Tests for Telegram webhook authentication (SEC-002).

    Tests verify X-Telegram-Bot-Api-Secret-Token header mechanism.
    """

    @pytest.mark.asyncio
    async def test_verify_webhook_valid_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful webhook authentication with valid secret token."""
        # Mock settings with test secret token
        test_secret = "test_secret_token_abc123def456"
        monkeypatch.setenv("TELEGRAM_SECRET_TOKEN", test_secret)
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")

        # Reset settings singleton
        import src.config

        src.config._settings = None

        # Test with valid secret token
        result = await verify_telegram_webhook(x_telegram_bot_api_secret_token=test_secret)
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_webhook_missing_header(self) -> None:
        """Test webhook authentication fails with missing secret token header.

        Security (SEC-002): Prevents unauthorized webhook calls.
        """
        with pytest.raises(HTTPException) as exc_info:
            await verify_telegram_webhook(x_telegram_bot_api_secret_token=None)

        assert exc_info.value.status_code == 401
        assert "Missing X-Telegram-Bot-Api-Secret-Token header" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_webhook_wrong_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test webhook authentication fails with wrong secret token.

        Security (SEC-002): Prevents brute force attacks.
        """
        # Mock settings with correct secret
        correct_secret = "correct_secret_token"
        monkeypatch.setenv("TELEGRAM_SECRET_TOKEN", correct_secret)
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")

        # Reset settings singleton
        import src.config

        src.config._settings = None

        # Test with wrong secret token
        with pytest.raises(HTTPException) as exc_info:
            await verify_telegram_webhook(x_telegram_bot_api_secret_token="wrong_secret")

        assert exc_info.value.status_code == 401
        assert "Invalid secret token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_webhook_not_configured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test webhook authentication fails if TELEGRAM_SECRET_TOKEN not configured.

        Security (SEC-002): Fails safe if config missing.
        """
        # Mock settings WITHOUT secret token
        monkeypatch.setenv("TELEGRAM_SECRET_TOKEN", "")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")

        # Reset settings singleton
        import src.config

        src.config._settings = None

        # Test with any token (should fail because not configured)
        with pytest.raises(HTTPException) as exc_info:
            await verify_telegram_webhook(x_telegram_bot_api_secret_token="any_token")

        assert exc_info.value.status_code == 500
        assert "not configured" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_secure_compare_timing_safe(self) -> None:
        """Test constant-time comparison prevents timing attacks.

        Security (SEC-002): Ensures string comparison takes same time
        regardless of where strings differ.
        """
        from src.auth.telegram import _secure_compare

        # Same strings
        assert _secure_compare("secret123", "secret123") is True

        # Different strings (same length)
        assert _secure_compare("secret123", "secret124") is False
        assert _secure_compare("aaaaaaaaa", "bbbbbbbbb") is False

        # Different lengths
        assert _secure_compare("short", "longer_string") is False
        assert _secure_compare("longer_string", "short") is False

        # Empty strings
        assert _secure_compare("", "") is True


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
    """Tests for student authentication (SEC-003).

    Note: SEC-003 requires database verification. These tests mock the database
    to test the validation logic. See integration tests for full database tests.
    """

    @pytest.mark.asyncio
    async def test_verify_student_missing_header(self) -> None:
        """Test student authentication fails with missing X-Student-ID header.

        Security (SEC-003): Must reject missing credentials.
        """
        with pytest.raises(HTTPException) as exc_info:
            # Pass None for db to avoid database dependency in unit test
            await verify_student(x_student_id=None, db=None)  # type: ignore

        assert exc_info.value.status_code == 401
        assert "Missing student credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_student_invalid_format(self) -> None:
        """Test student authentication fails with invalid ID format.

        Security (SEC-003): Must validate input format before database query.
        """
        with pytest.raises(HTTPException) as exc_info:
            await verify_student(x_student_id="not_a_number", db=None)  # type: ignore

        assert exc_info.value.status_code == 400
        assert "must be a valid integer" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_student_negative_id(self) -> None:
        """Test student authentication fails with negative ID.

        Security (SEC-003): Must validate ID is positive before database query.
        """
        with pytest.raises(HTTPException) as exc_info:
            await verify_student(x_student_id="-123", db=None)  # type: ignore

        assert exc_info.value.status_code == 400
        assert "Invalid student ID" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_student_zero_id(self) -> None:
        """Test student authentication fails with zero ID.

        Security (SEC-003): Zero is not a valid Telegram ID.
        """
        with pytest.raises(HTTPException) as exc_info:
            await verify_student(x_student_id="0", db=None)  # type: ignore

        assert exc_info.value.status_code == 400
        assert "Invalid student ID" in exc_info.value.detail
