"""Integration tests for the /streak Telegram UX and non-repeat encouragement.

PHASE6-C-2 (REQ-010, REQ-013)

Tests the calendar view formatter directly and the EncouragementService
non-repeat behaviour against a real in-memory SQLite session.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.sent_message import SentMessage
from src.models.streak import Streak
from src.models.student import Student
from src.routes.webhook import _format_streak_message
from src.services.encouragement import EncouragementService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_streak(current: int = 5, longest: int = 10) -> Streak:
    """Build an unsaved Streak ORM object (no DB needed for formatter tests)."""
    streak = Streak()
    streak.current_streak = current
    streak.longest_streak = longest
    streak.milestones_achieved = []
    return streak


async def _create_student(db: AsyncSession, telegram_id: int = 200) -> Student:
    student = Student(
        telegram_id=telegram_id,
        name="Streak Tester",
        grade=7,
        language="en",
    )
    db.add(student)
    await db.flush()
    return student


# ---------------------------------------------------------------------------
# Tests: _format_streak_message calendar view
# ---------------------------------------------------------------------------


class TestStreakCalendarView:
    def test_calendar_includes_filled_and_empty_circles(self) -> None:
        """Output contains both ● (practiced) and ○ (missed) for a partial week."""
        today = date.today()
        # Practice on last 5 days — 2 gaps (6 and 7 days ago)
        last_7_days = [today - timedelta(days=i) for i in range(4, -1, -1)]
        streak = _make_streak(current=5, longest=10)

        output = _format_streak_message(streak, last_7_days, "en")

        assert "\u25cf" in output, "Expected filled circle ● for practiced days"
        assert "\u25cb" in output, "Expected empty circle ○ for missed days"

    def test_streak_shows_next_milestone_countdown(self) -> None:
        """With current_streak=5, next milestone is 7 and days_away=2."""
        today = date.today()
        last_7_days = [today - timedelta(days=1), today]
        streak = _make_streak(current=5, longest=5)

        output = _format_streak_message(streak, last_7_days, "en")

        assert "7" in output, "Expected milestone '7' in output"
        assert "2 days away" in output, "Expected '2 days away' countdown"

    def test_streak_zero_shows_start_message(self) -> None:
        """Passing streak=None (zero state) shows the 'first streak' prompt."""
        output = _format_streak_message(None, [], "en")

        assert "first streak" in output.lower(), "Expected 'first streak' in zero-streak output"

    def test_all_milestones_achieved_shows_champion_line(self) -> None:
        """Streak > 30 shows 'All milestones achieved' instead of a countdown."""
        today = date.today()
        last_7_days = [today]
        streak = _make_streak(current=35, longest=35)

        output = _format_streak_message(streak, last_7_days, "en")

        assert "milestones achieved" in output.lower()

    def test_bengali_zero_streak_shows_bengali_text(self) -> None:
        """Bengali zero-streak shows Bengali Unicode text."""
        output = _format_streak_message(None, [], "bn")

        assert any(ord(c) > 0x0980 for c in output), "Expected Bengali Unicode"

    def test_bengali_streak_shows_bengali_calendar(self) -> None:
        """Bengali non-zero streak output contains Bengali Unicode."""
        today = date.today()
        last_7_days = [today]
        streak = _make_streak(current=3, longest=3)

        output = _format_streak_message(streak, last_7_days, "bn")

        assert any(ord(c) > 0x0980 for c in output), "Expected Bengali Unicode in calendar"

    def test_calendar_has_seven_day_entries(self) -> None:
        """Calendar row contains exactly 7 day entries (one per day)."""
        today = date.today()
        last_7_days = [today]
        streak = _make_streak(current=1, longest=1)

        output = _format_streak_message(streak, last_7_days, "en")

        # Count total dot characters — one ● or ○ per day
        dot_count = output.count("\u25cf") + output.count("\u25cb")
        assert dot_count == 7, f"Expected 7 calendar dots, got {dot_count}"


# ---------------------------------------------------------------------------
# Tests: non-repeat encouragement (REQ-013)
# ---------------------------------------------------------------------------


class TestEncouragementNonRepeat:
    @pytest.mark.asyncio
    async def test_non_repeat_within_7_days(self, db_session: AsyncSession) -> None:
        """No two consecutive get_unique_correct_message calls return the same key."""
        student = await _create_student(db_session, telegram_id=201)
        student_id = student.student_id
        svc = EncouragementService()

        results: list[str] = []
        for _ in range(4):
            msg = await svc.get_unique_correct_message(
                db=db_session,
                student_id=student_id,
                streak=0,
                language="en",
            )
            results.append(msg)

        # Each call must return a non-empty string (even the 4th forced-repeat)
        for msg in results:
            assert isinstance(msg, str) and len(msg) > 0

        # Inspect SentMessage keys written
        rows = (
            (
                await db_session.execute(
                    select(SentMessage.message_key).where(SentMessage.student_id == student_id)
                )
            )
            .scalars()
            .all()
        )

        # There should be exactly 4 SentMessage rows
        assert len(rows) == 4

        # First 3 keys are all distinct (exhausts the 3-variant pool)
        first_three_keys = rows[:3]
        assert (
            len(set(first_three_keys)) == 3
        ), f"Expected 3 distinct keys in first 3 calls, got {first_three_keys}"

    @pytest.mark.asyncio
    async def test_non_repeat_incorrect_within_7_days(self, db_session: AsyncSession) -> None:
        """get_unique_incorrect_message cycles through all variants before repeating."""
        student = await _create_student(db_session, telegram_id=202)
        student_id = student.student_id
        svc = EncouragementService()

        keys_seen: list[str] = []
        for i in range(3):
            await svc.get_unique_incorrect_message(
                db=db_session,
                student_id=student_id,
                hints_used=i,
                language="en",
            )
            rows = (
                (
                    await db_session.execute(
                        select(SentMessage.message_key).where(SentMessage.student_id == student_id)
                    )
                )
                .scalars()
                .all()
            )
            keys_seen.append(rows[-1])

        # All 3 calls used distinct keys
        assert len(set(keys_seen)) == 3, f"Expected 3 distinct keys, got {keys_seen}"

    @pytest.mark.asyncio
    async def test_sent_message_rows_written_per_call(self, db_session: AsyncSession) -> None:
        """Each call to get_unique_correct_message writes exactly one SentMessage row."""
        student = await _create_student(db_session, telegram_id=203)
        student_id = student.student_id
        svc = EncouragementService()

        for expected_count in range(1, 4):
            await svc.get_unique_correct_message(
                db=db_session,
                student_id=student_id,
                streak=0,
                language="en",
            )
            rows = (
                (
                    await db_session.execute(
                        select(SentMessage).where(SentMessage.student_id == student_id)
                    )
                )
                .scalars()
                .all()
            )
            assert len(rows) == expected_count
