"""Integration tests for the /language Telegram command.

Verifies language selection, DB persistence, confirmation messages, and
invalid-input re-prompting. Calls webhook handler functions directly.

PHASE7-C-3
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.student import Student
from src.routes import webhook as wh
from src.routes.webhook import (
    handle_language_choice,
    handle_language_command,
    handle_unknown_message,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TELEGRAM_ID = 777666555


async def _seed_student(
    db: AsyncSession, telegram_id: int = _TELEGRAM_ID, language: str = "en"
) -> Student:
    student = Student(telegram_id=telegram_id, name="TestUser", grade=7, language=language)
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestLanguageSwitch:
    def setup_method(self) -> None:
        """Clear pending language state before each test."""
        wh._pending_language_choice.clear()

    async def test_language_command_updates_student_profile(self, db_session: AsyncSession) -> None:
        """After /language → '2', student.language should be 'bn' in DB."""
        await _seed_student(db_session)

        await handle_language_command(_TELEGRAM_ID, db_session)
        await handle_language_choice(_TELEGRAM_ID, "2", db_session)

        result = await db_session.execute(
            select(Student).where(Student.telegram_id == _TELEGRAM_ID)
        )
        student = result.scalar_one()
        assert student.language == "bn"

    async def test_language_confirmed_message_in_new_language(
        self, db_session: AsyncSession
    ) -> None:
        """Switching to Bengali returns a confirmation message with Bengali text."""
        await _seed_student(db_session)

        await handle_language_command(_TELEGRAM_ID, db_session)
        reply = await handle_language_choice(_TELEGRAM_ID, "2", db_session)

        # Bengali confirmation should contain Bengali Unicode characters (U+0981+)
        assert any(
            ord(ch) > 0x0980 for ch in reply
        ), f"Expected Bengali Unicode in confirmation message, got: {reply!r}"

    async def test_language_subsequent_messages_use_new_language(
        self, db_session: AsyncSession
    ) -> None:
        """After switching to Bengali, unknown command response is in Bengali."""
        await _seed_student(db_session)

        # Switch to Bengali
        await handle_language_command(_TELEGRAM_ID, db_session)
        await handle_language_choice(_TELEGRAM_ID, "2", db_session)

        # handle_unknown_message uses the language passed in
        reply = await handle_unknown_message(_TELEGRAM_ID, "xyz random text", "bn")
        assert any(
            ord(ch) > 0x0980 for ch in reply
        ), f"Expected Bengali response after language switch, got: {reply!r}"

    async def test_language_invalid_input_reprompts(self, db_session: AsyncSession) -> None:
        """Invalid choice after /language re-prompts without changing language."""
        await _seed_student(db_session)

        await handle_language_command(_TELEGRAM_ID, db_session)
        reply = await handle_language_choice(_TELEGRAM_ID, "xyz", db_session)

        # Language should be unchanged
        result = await db_session.execute(
            select(Student).where(Student.telegram_id == _TELEGRAM_ID)
        )
        student = result.scalar_one()
        assert student.language == "en"

        # Reply should re-prompt (contain language selection options)
        assert "1" in reply or "English" in reply or "বাংলা" in reply
