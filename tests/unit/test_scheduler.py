"""Unit tests for the APScheduler setup and send_daily_reminders job.

PHASE6-C-3 (REQ-011)

Tests verify:
- Scheduler registers the daily_reminders job at 12:30 UTC
- send_daily_reminders skips students who already practiced today
- send_daily_reminders sends reminders to students who missed
"""

import asyncio
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch


class TestSchedulerJobRegistration:
    async def test_scheduler_registers_daily_reminders_job(self) -> None:
        """start_scheduler() should register 'daily_reminders' cron job at 12:30 UTC."""
        from src.scheduler import scheduler, start_scheduler, stop_scheduler

        start_scheduler()
        try:
            job = scheduler.get_job("daily_reminders")
            assert job is not None, "daily_reminders job not found"

            # Verify cron trigger fields: hour=12, minute=30
            trigger = job.trigger
            fields_by_name = {f.name: f for f in trigger.fields}
            hour_expr = str(fields_by_name["hour"])
            minute_expr = str(fields_by_name["minute"])
            assert hour_expr == "12", f"Expected hour=12, got {hour_expr}"
            assert minute_expr == "30", f"Expected minute=30, got {minute_expr}"
        finally:
            stop_scheduler()


class TestSendDailyReminders:
    def _make_student(
        self, student_id: int = 1, telegram_id: int = 100, language: str = "en"
    ) -> MagicMock:
        s = MagicMock()
        s.student_id = student_id
        s.telegram_id = telegram_id
        s.language = language
        return s

    def _make_streak(self, current: int = 3, last_date: date | None = None) -> MagicMock:
        sk = MagicMock()
        sk.current_streak = current
        sk.last_practice_date = last_date or (date.today() - timedelta(days=1))
        return sk

    def _make_db_session(self, students: list[MagicMock]) -> MagicMock:
        """Build a mock async DB session whose execute() returns the given student list.

        .scalars().all() returns the student list (used by the initial Student query).
        .scalar_one_or_none() returns None (used by the double-fire SentMessage guard,
        meaning no reminder has been sent today yet).
        """
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = students
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_result.scalar_one_or_none.return_value = None  # no reminder sent yet today

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)
        return mock_db

    def _make_session_factory(self, mock_db: MagicMock) -> MagicMock:
        """Wrap mock_db in a factory whose async context manager yields it."""
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_db)
        cm.__aexit__ = AsyncMock(return_value=None)
        factory = MagicMock(return_value=cm)
        return factory

    def test_skips_student_who_practiced_today(self) -> None:
        """Students with last_practice_date == today receive no reminder."""
        student = self._make_student()
        streak = self._make_streak(current=5, last_date=date.today())
        mock_db = self._make_db_session([student])
        factory = self._make_session_factory(mock_db)

        with (
            patch("src.scheduler.get_session_factory", return_value=factory),
            patch("src.scheduler.StreakRepository") as mock_repo_cls,
            patch("src.scheduler.TelegramClient") as mock_telegram_cls,
        ):
            mock_repo_cls.return_value.get_for_student = AsyncMock(return_value=streak)
            mock_telegram = AsyncMock()
            mock_telegram_cls.return_value = mock_telegram

            from src.scheduler import send_daily_reminders

            asyncio.run(send_daily_reminders())

            mock_telegram.send_message.assert_not_called()

    def test_sends_reminder_to_student_who_missed(self) -> None:
        """Students with last_practice_date < today receive a reminder."""
        student = self._make_student(telegram_id=42)
        yesterday = date.today() - timedelta(days=1)
        streak = self._make_streak(current=3, last_date=yesterday)
        mock_db = self._make_db_session([student])
        factory = self._make_session_factory(mock_db)

        with (
            patch("src.scheduler.get_session_factory", return_value=factory),
            patch("src.scheduler.StreakRepository") as mock_repo_cls,
            patch("src.scheduler.TelegramClient") as mock_telegram_cls,
        ):
            mock_repo_cls.return_value.get_for_student = AsyncMock(return_value=streak)
            mock_send = AsyncMock(return_value=True)
            mock_telegram_cls.return_value.send_message = mock_send

            from src.scheduler import send_daily_reminders

            asyncio.run(send_daily_reminders())

            mock_send.assert_called_once()
            _chat_id, msg = mock_send.call_args.args
            assert _chat_id == 42
            assert "at risk" in msg

    def test_zero_streak_sends_motivational_not_at_risk(self) -> None:
        """Students with current_streak=0 get motivational message without 'at risk'."""
        student = self._make_student(telegram_id=99)
        yesterday = date.today() - timedelta(days=1)
        streak = self._make_streak(current=0, last_date=yesterday)
        mock_db = self._make_db_session([student])
        factory = self._make_session_factory(mock_db)

        with (
            patch("src.scheduler.get_session_factory", return_value=factory),
            patch("src.scheduler.StreakRepository") as mock_repo_cls,
            patch("src.scheduler.TelegramClient") as mock_telegram_cls,
        ):
            mock_repo_cls.return_value.get_for_student = AsyncMock(return_value=streak)
            mock_send = AsyncMock(return_value=True)
            mock_telegram_cls.return_value.send_message = mock_send

            from src.scheduler import send_daily_reminders

            asyncio.run(send_daily_reminders())

            mock_send.assert_called_once()
            _chat_id, msg = mock_send.call_args.args
            assert "at risk" not in msg
            assert "streak" in msg.lower() or "ধারা" in msg

    def test_bengali_message_for_bn_student(self) -> None:
        """Bengali students receive reminders in Bengali."""
        student = self._make_student(telegram_id=77, language="bn")
        yesterday = date.today() - timedelta(days=1)
        streak = self._make_streak(current=5, last_date=yesterday)
        mock_db = self._make_db_session([student])
        factory = self._make_session_factory(mock_db)

        with (
            patch("src.scheduler.get_session_factory", return_value=factory),
            patch("src.scheduler.StreakRepository") as mock_repo_cls,
            patch("src.scheduler.TelegramClient") as mock_telegram_cls,
        ):
            mock_repo_cls.return_value.get_for_student = AsyncMock(return_value=streak)
            mock_send = AsyncMock(return_value=True)
            mock_telegram_cls.return_value.send_message = mock_send

            from src.scheduler import send_daily_reminders

            asyncio.run(send_daily_reminders())

            _chat_id, msg = mock_send.call_args.args
            # Bengali message must contain Bengali Unicode characters
            assert any(ord(c) > 0x0980 for c in msg), "Expected Bengali Unicode in message"

    def test_send_failure_does_not_crash_job(self) -> None:
        """A Telegram send failure is logged but does not crash the scheduler job."""
        student = self._make_student(telegram_id=55)
        yesterday = date.today() - timedelta(days=1)
        streak = self._make_streak(current=2, last_date=yesterday)
        mock_db = self._make_db_session([student])
        factory = self._make_session_factory(mock_db)

        with (
            patch("src.scheduler.get_session_factory", return_value=factory),
            patch("src.scheduler.StreakRepository") as mock_repo_cls,
            patch("src.scheduler.TelegramClient") as mock_telegram_cls,
        ):
            mock_repo_cls.return_value.get_for_student = AsyncMock(return_value=streak)
            mock_telegram_cls.return_value.send_message = AsyncMock(
                side_effect=Exception("Network error")
            )

            from src.scheduler import send_daily_reminders

            # Must not raise
            asyncio.run(send_daily_reminders())

    def test_double_fire_guard_skips_already_reminded_student(self) -> None:
        """Student with a SentMessage reminder row for today is skipped (double-fire guard)."""
        student = self._make_student(telegram_id=66)
        yesterday = date.today() - timedelta(days=1)
        streak = self._make_streak(current=3, last_date=yesterday)
        mock_db = self._make_db_session([student])
        # Override: scalar_one_or_none returns a truthy mock — reminder already sent today
        mock_db.execute.return_value.scalar_one_or_none.return_value = MagicMock()
        factory = self._make_session_factory(mock_db)

        with (
            patch("src.scheduler.get_session_factory", return_value=factory),
            patch("src.scheduler.StreakRepository") as mock_repo_cls,
            patch("src.scheduler.TelegramClient") as mock_telegram_cls,
        ):
            mock_repo_cls.return_value.get_for_student = AsyncMock(return_value=streak)
            mock_send = AsyncMock()
            mock_telegram_cls.return_value.send_message = mock_send

            from src.scheduler import send_daily_reminders

            asyncio.run(send_daily_reminders())

        # Guard fired — send_message must NOT have been called
        mock_send.assert_not_called()
