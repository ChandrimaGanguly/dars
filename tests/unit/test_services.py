"""Unit tests for service layer."""

from unittest.mock import AsyncMock, patch

import pytest

from src.services.student_service import StudentService
from src.services.telegram_client import TelegramClient


@pytest.mark.unit
class TestStudentService:
    """Tests for StudentService."""

    async def test_get_or_create_new_student(self, db_session) -> None:
        """Test creating a new student."""
        service = StudentService()

        student = await service.get_or_create(
            db=db_session,
            telegram_id=123456,
            name="TestStudent",
        )

        assert student.telegram_id == 123456
        assert student.name == "TestStudent"
        assert student.grade == 7
        assert student.language == "en"

    async def test_get_or_create_existing_student(self, db_session) -> None:
        """Test returning existing student without duplication."""
        service = StudentService()

        # Create student first time
        student1 = await service.get_or_create(
            db=db_session,
            telegram_id=123456,
            name="TestStudent",
        )

        # Call again with same telegram_id
        student2 = await service.get_or_create(
            db=db_session,
            telegram_id=123456,
            name="DifferentName",  # Should be ignored
        )

        # Should return same student
        assert student1.student_id == student2.student_id
        assert student2.name == "TestStudent"  # Original name preserved


@pytest.mark.unit
class TestTelegramClient:
    """Tests for TelegramClient."""

    async def test_send_message_success(self) -> None:
        """Test sending message successfully."""
        # Mock httpx.AsyncClient
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = lambda: None  # Synchronous no-op

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            # Test
            client = TelegramClient()
            result = await client.send_message(chat_id=123, text="Hello")

            assert result is True
            mock_client.post.assert_called_once()

    async def test_send_message_failure(self) -> None:
        """Test handling send message failure gracefully."""
        # Mock httpx.AsyncClient to raise exception
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("Network error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            # Test
            client = TelegramClient()
            result = await client.send_message(chat_id=123, text="Hello")

            assert result is False
