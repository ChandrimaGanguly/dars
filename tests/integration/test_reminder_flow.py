"""Integration tests for the daily reminder flow.

PHASE6-C-1 (REQ-011)

Uses in-memory SQLite (db_session fixture) with src.scheduler.get_session_factory
patched to yield the test session, so send_daily_reminders() queries the same
in-memory DB that the test populates.

TelegramClient.send_message is patched to avoid real HTTP calls.
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.streak import Streak
from src.models.student import Student
from src.scheduler import send_daily_reminders

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_factory(db: AsyncSession) -> MagicMock:
    """Return a mock session factory whose async context manager yields db."""
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=db)
    cm.__aexit__ = AsyncMock(return_value=None)
    factory = MagicMock(return_value=cm)
    return factory


async def _create_student(
    db: AsyncSession,
    telegram_id: int = 100,
    language: str = "en",
) -> Student:
    student = Student(
        telegram_id=telegram_id,
        name="Test Student",
        grade=7,
        language=language,
    )
    db.add(student)
    await db.flush()
    return student


async def _create_streak(
    db: AsyncSession,
    student_id: int,
    current: int = 5,
    last_date: date | None = None,
) -> Streak:
    streak = Streak(
        student_id=student_id,
        current_streak=current,
        longest_streak=max(current, 5),
        last_practice_date=last_date or (date.today() - timedelta(days=1)),
        milestones_achieved=[],
    )
    db.add(streak)
    await db.flush()
    return streak


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestReminderFlow:
    @pytest.mark.asyncio
    async def test_reminder_sent_to_student_who_has_not_practiced_today(
        self, db_session: AsyncSession
    ) -> None:
        """Students with last_practice_date=yesterday receive one reminder."""
        student = await _create_student(db_session, telegram_id=101)
        student_id = student.student_id
        await _create_streak(
            db_session,
            student_id=student_id,
            current=3,
            last_date=date.today() - timedelta(days=1),
        )

        factory = _make_factory(db_session)
        mock_send = AsyncMock(return_value=True)

        with (
            patch("src.scheduler.get_session_factory", return_value=factory),
            patch("src.scheduler.TelegramClient") as mock_telegram_cls,
        ):
            mock_telegram_cls.return_value.send_message = mock_send
            await send_daily_reminders()

        mock_send.assert_called_once()
        called_chat_id = mock_send.call_args.args[0]
        assert called_chat_id == 101

    @pytest.mark.asyncio
    async def test_no_reminder_to_student_who_practiced_today(
        self, db_session: AsyncSession
    ) -> None:
        """Students with last_practice_date=today are skipped."""
        student = await _create_student(db_session, telegram_id=102)
        student_id = student.student_id
        await _create_streak(
            db_session,
            student_id=student_id,
            current=5,
            last_date=date.today(),
        )

        factory = _make_factory(db_session)
        mock_send = AsyncMock(return_value=True)

        with (
            patch("src.scheduler.get_session_factory", return_value=factory),
            patch("src.scheduler.TelegramClient") as mock_telegram_cls,
        ):
            mock_telegram_cls.return_value.send_message = mock_send
            await send_daily_reminders()

        mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_zero_streak_gets_motivational_not_at_risk_message(
        self, db_session: AsyncSession
    ) -> None:
        """Students with current_streak=0 get a motivational message, not 'at risk'."""
        student = await _create_student(db_session, telegram_id=103)
        student_id = student.student_id
        await _create_streak(
            db_session,
            student_id=student_id,
            current=0,
            last_date=date.today() - timedelta(days=1),
        )

        factory = _make_factory(db_session)
        mock_send = AsyncMock(return_value=True)

        with (
            patch("src.scheduler.get_session_factory", return_value=factory),
            patch("src.scheduler.TelegramClient") as mock_telegram_cls,
        ):
            mock_telegram_cls.return_value.send_message = mock_send
            await send_daily_reminders()

        mock_send.assert_called_once()
        _chat_id, msg = mock_send.call_args.args
        assert "at risk" not in msg

    @pytest.mark.asyncio
    async def test_reminder_message_matches_student_language_bengali(
        self, db_session: AsyncSession
    ) -> None:
        """Bengali students receive a message containing Bengali Unicode characters."""
        student = await _create_student(db_session, telegram_id=104, language="bn")
        student_id = student.student_id
        await _create_streak(
            db_session,
            student_id=student_id,
            current=4,
            last_date=date.today() - timedelta(days=1),
        )

        factory = _make_factory(db_session)
        mock_send = AsyncMock(return_value=True)

        with (
            patch("src.scheduler.get_session_factory", return_value=factory),
            patch("src.scheduler.TelegramClient") as mock_telegram_cls,
        ):
            mock_telegram_cls.return_value.send_message = mock_send
            await send_daily_reminders()

        mock_send.assert_called_once()
        _chat_id, msg = mock_send.call_args.args
        assert any(ord(c) > 0x0980 for c in msg), "Expected Bengali Unicode in message"

    @pytest.mark.asyncio
    async def test_telegram_failure_does_not_crash_scheduler(
        self, db_session: AsyncSession
    ) -> None:
        """A send failure on one student is logged and processing continues for others."""
        student_a = await _create_student(db_session, telegram_id=105)
        student_b = await _create_student(db_session, telegram_id=106)
        yesterday = date.today() - timedelta(days=1)
        await _create_streak(db_session, student_id=student_a.student_id, last_date=yesterday)
        await _create_streak(db_session, student_id=student_b.student_id, last_date=yesterday)

        factory = _make_factory(db_session)
        # First call raises, second succeeds
        mock_send = AsyncMock(side_effect=[Exception("Telegram down"), True])

        with (
            patch("src.scheduler.get_session_factory", return_value=factory),
            patch("src.scheduler.TelegramClient") as mock_telegram_cls,
        ):
            mock_telegram_cls.return_value.send_message = mock_send
            # Must not raise
            await send_daily_reminders()

        # Both students were attempted
        assert mock_send.call_count == 2

        # Only the successful student's reminder is recorded (failed send must not write row)
        from sqlalchemy import select

        from src.models.sent_message import SentMessage

        rows = (await db_session.execute(select(SentMessage))).scalars().all()
        assert (
            len(rows) == 1
        ), f"Expected exactly 1 SentMessage row (successful student only), got {len(rows)}"
