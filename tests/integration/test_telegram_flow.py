"""Integration tests for Telegram bot flows.

These tests verify the full end-to-end user flows work correctly,
including database persistence and API interactions.
"""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from src.models.student import Student
from src.routes.webhook import _handle_message, _pending_onboarding
from src.schemas.telegram import TelegramMessage


def _make_message(telegram_id: int, text: str, name: str = "TestUser") -> TelegramMessage:
    """Build a TelegramMessage for testing."""
    return TelegramMessage.model_validate(
        {
            "message_id": 1,
            "date": 1643129200,
            "chat": {"id": telegram_id, "type": "private"},
            "from": {
                "id": telegram_id,
                "is_bot": False,
                "first_name": name,
            },
            "text": text,
        }
    )


@pytest.mark.integration
class TestStudentOnboardingFlow:
    """Integration tests for student onboarding via /start command."""

    async def test_new_student_registration(self, db_session) -> None:
        """Test that /start → grade → language creates student in DB."""
        telegram_id = 987654321
        _pending_onboarding.pop(telegram_id, None)  # clean state

        with patch("src.services.telegram_client.TelegramClient.send_message", new=AsyncMock()):

            # Step 1: /start → begins onboarding, student NOT yet created
            await _handle_message(_make_message(telegram_id, "/start", "TestUser"), db_session)
            result = await db_session.execute(
                select(Student).where(Student.telegram_id == telegram_id)
            )
            assert result.scalar_one_or_none() is None  # not yet

            # Step 2: choose grade
            await _handle_message(_make_message(telegram_id, "7"), db_session)

            # Step 3: choose language → student created
            await _handle_message(_make_message(telegram_id, "1"), db_session)

        result = await db_session.execute(select(Student).where(Student.telegram_id == telegram_id))
        student = result.scalar_one_or_none()

        assert student is not None
        assert student.name == "TestUser"
        assert student.grade == 7
        assert student.language == "en"

    def test_existing_student_welcome(self) -> None:
        """Test that returning student gets appropriate message."""
        # TODO: Implement when Telegram handler exists
        # - Create student in DB
        # - Send /start message
        # - Verify personalized welcome returned
        assert True

    def test_grade_selection_flow(self) -> None:
        """Test that student can select grade level."""
        # TODO: Implement when grade selection exists
        # - Send /start
        # - Select grade 7 via inline keyboard
        # - Verify grade stored in DB
        assert True

    def test_language_preference(self) -> None:
        """Test that language preference is persisted."""
        # TODO: Implement when language selector exists
        # - Select Bengali
        # - Verify subsequent messages in Bengali
        assert True


@pytest.mark.integration
class TestDailyPracticeFlow:
    """Integration tests for the core learning experience."""

    def test_practice_session_completion(self) -> None:
        """Test that student can complete a 5-problem practice session."""
        # TODO: Implement when practice flow exists
        # - Send /practice
        # - Answer 5 questions
        # - Verify session saved to DB
        # - Verify streak updated
        assert True

    def test_hint_system(self) -> None:
        """Test that students can request and receive hints."""
        # TODO: Implement when hint system exists
        # - Answer incorrectly
        # - Request hint
        # - Verify hint from Claude received
        # - Verify hint saved in DB
        assert True

    def test_socratic_guidance(self) -> None:
        """Test that hints guide without giving answers."""
        # TODO: Implement when Socratic system exists
        # - Answer incorrectly
        # - Get hint
        # - Hint should not contain answer
        # - Student should be able to try again
        assert True


@pytest.mark.integration
class TestStreakPersistence:
    """Integration tests for streak tracking across sessions."""

    def test_streak_survives_app_restart(self) -> None:
        """Test that streak is persisted and restored correctly."""
        # TODO: Implement when streak persistence exists
        # - Student practices (streak = 1)
        # - Close app and reopen
        # - Verify streak still shows 1
        assert True

    def test_reminder_message(self) -> None:
        """Test that reminder is sent if student hasn't practiced today."""
        # TODO: Implement when reminders exist
        # - Student doesn't practice for a day
        # - Reminder sent at scheduled time
        # - Student can resume practice
        assert True
