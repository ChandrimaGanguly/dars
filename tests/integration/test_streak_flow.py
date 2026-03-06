"""Integration tests for the streak tracking service layer.

Verifies end-to-end streak flows: first practice starts a streak, consecutive
days accumulate it, gaps reset it, and milestone detection fires at 7 days.
Uses an in-memory SQLite database — no external services required.

Tests call the repository layer directly (not via HTTP) to avoid Starlette
event-loop isolation issues with async SQLAlchemy.

Own engine/session fixtures are used (with expire_on_commit=False + autoflush=False)
to avoid MissingGreenlet errors triggered by the Streak model's selectin relations.

PHASE4-C-2
"""

from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.models.base import Base
from src.models.streak import Streak
from src.models.student import Student
from src.repositories.streak_repository import StreakRepository

# ---------------------------------------------------------------------------
# Local fixtures (override conftest db_session for this file)
# ---------------------------------------------------------------------------

_TELEGRAM_ID_BASE = 800_000_001  # distinct range from other integration test files
_MILESTONE_DAY = date(2026, 3, 10)  # fixed anchor date for milestone tests


@pytest.fixture
async def engine():
    """In-memory SQLite engine with full schema for this test module."""
    _engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest.fixture
async def db(engine) -> AsyncSession:  # type: ignore[no-untyped-def]
    """Async session with expire_on_commit=False to avoid MissingGreenlet."""
    factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with factory() as session:
        yield session


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_student(db: AsyncSession, telegram_id: int) -> Student:
    """Create and flush a test Student.

    Args:
        db: Async SQLAlchemy session.
        telegram_id: Unique Telegram ID for this student.

    Returns:
        Flushed Student instance.
    """
    student = Student(
        telegram_id=telegram_id,
        name="StreakTestStudent",
        grade=7,
        language="en",
    )
    db.add(student)
    await db.flush()
    return student


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestStreakFirstPractice:
    """Verify streak initialisation on first practice."""

    async def test_first_practice_creates_streak_at_1(self, db: AsyncSession) -> None:
        """First practice session should set current_streak=1."""
        student = await _create_student(db, _TELEGRAM_ID_BASE)
        repo = StreakRepository()

        streak, new_milestones = await repo.record_practice(
            db, student.student_id, date(2026, 3, 1)
        )

        assert streak.current_streak == 1
        assert streak.longest_streak == 1
        assert streak.last_practice_date is not None
        assert new_milestones == []

    async def test_first_practice_creates_streak_row(self, db: AsyncSession) -> None:
        """record_practice must persist a Streak row to the database."""
        student = await _create_student(db, _TELEGRAM_ID_BASE + 1)
        repo = StreakRepository()

        await repo.record_practice(db, student.student_id, date(2026, 3, 1))
        await db.flush()

        streak = await repo.get_for_student(db, student.student_id)
        assert streak is not None
        assert streak.current_streak == 1


@pytest.mark.integration
class TestStreakConsecutiveDays:
    """Verify streak accumulates over consecutive practice days."""

    async def test_two_consecutive_days_streak_2(self, db: AsyncSession) -> None:
        """Practicing on day N and day N+1 gives streak of 2."""
        student = await _create_student(db, _TELEGRAM_ID_BASE + 10)
        repo = StreakRepository()

        await repo.record_practice(db, student.student_id, date(2026, 3, 1))
        streak, _ = await repo.record_practice(db, student.student_id, date(2026, 3, 2))

        assert streak.current_streak == 2

    async def test_five_consecutive_days_streak_5(self, db: AsyncSession) -> None:
        """Five consecutive practice days gives streak=5."""
        student = await _create_student(db, _TELEGRAM_ID_BASE + 11)
        repo = StreakRepository()

        for day_offset in range(5):
            d = date(2026, 3, 1) + timedelta(days=day_offset)
            streak, _ = await repo.record_practice(db, student.student_id, d)

        assert streak.current_streak == 5
        assert streak.longest_streak == 5

    async def test_gap_resets_streak_to_1(self, db: AsyncSession) -> None:
        """Missing a day resets the streak to 1 on the next practice."""
        student = await _create_student(db, _TELEGRAM_ID_BASE + 12)
        repo = StreakRepository()

        for day_offset in range(3):
            d = date(2026, 3, 1) + timedelta(days=day_offset)
            await repo.record_practice(db, student.student_id, d)

        # Gap of 2 days (3 March → 6 March, skipping 5 March)
        streak, _ = await repo.record_practice(db, student.student_id, date(2026, 3, 6))

        assert streak.current_streak == 1

    async def test_longest_streak_preserved_after_reset(self, db: AsyncSession) -> None:
        """longest_streak is not reduced when current_streak resets."""
        student = await _create_student(db, _TELEGRAM_ID_BASE + 13)
        repo = StreakRepository()

        for day_offset in range(4):
            d = date(2026, 2, 1) + timedelta(days=day_offset)
            await repo.record_practice(db, student.student_id, d)

        # Gap then new session
        streak, _ = await repo.record_practice(db, student.student_id, date(2026, 3, 1))

        assert streak.current_streak == 1
        assert streak.longest_streak == 4

    async def test_same_day_is_idempotent(self, db: AsyncSession) -> None:
        """Calling record_practice twice on the same day does not increment streak."""
        student = await _create_student(db, _TELEGRAM_ID_BASE + 14)
        repo = StreakRepository()

        streak1, _ = await repo.record_practice(db, student.student_id, date(2026, 3, 1))
        streak2, _ = await repo.record_practice(db, student.student_id, date(2026, 3, 1))

        assert streak1.current_streak == streak2.current_streak == 1


@pytest.mark.integration
class TestStreakMilestoneDetection:
    """Verify milestone fires at 7 days and is not double-counted."""

    async def test_7_day_streak_fires_milestone(self, db: AsyncSession) -> None:
        """Completing 7 consecutive practice days triggers the 7-day milestone."""
        student = await _create_student(db, _TELEGRAM_ID_BASE + 20)
        repo = StreakRepository()

        all_new_milestones: list[int] = []
        streak_ref = None
        for day_offset in range(7):
            d = _MILESTONE_DAY - timedelta(days=6 - day_offset)
            streak_ref, new = await repo.record_practice(db, student.student_id, d)
            all_new_milestones.extend(new)

        assert streak_ref is not None
        assert streak_ref.current_streak == 7
        assert 7 in all_new_milestones
        assert 7 in streak_ref.milestones_achieved

    async def test_7_day_milestone_not_double_counted(self, db: AsyncSession) -> None:
        """After hitting the 7-day milestone, subsequent days must not re-fire it."""
        student = await _create_student(db, _TELEGRAM_ID_BASE + 21)
        repo = StreakRepository()

        for day_offset in range(7):
            d = _MILESTONE_DAY - timedelta(days=6 - day_offset)
            await repo.record_practice(db, student.student_id, d)

        _, day_8_milestones = await repo.record_practice(
            db, student.student_id, _MILESTONE_DAY + timedelta(days=1)
        )

        assert 7 not in day_8_milestones

    async def test_no_milestone_below_threshold(self, db: AsyncSession) -> None:
        """A 5-day streak should not trigger any milestone."""
        student = await _create_student(db, _TELEGRAM_ID_BASE + 22)
        repo = StreakRepository()

        all_milestones: list[int] = []
        for day_offset in range(5):
            d = _MILESTONE_DAY + timedelta(days=day_offset)
            _, new = await repo.record_practice(db, student.student_id, d)
            all_milestones.extend(new)

        assert all_milestones == []


@pytest.mark.integration
class TestStreakRepositoryGetOrCreate:
    """Verify get_or_create behaviour — mirrors what the GET /streak endpoint reads."""

    async def test_get_or_create_returns_zero_streak_for_new_student(
        self, db: AsyncSession
    ) -> None:
        """A brand-new student has current_streak=0 and no milestones."""
        student = await _create_student(db, _TELEGRAM_ID_BASE + 30)
        repo = StreakRepository()

        streak = await repo.get_or_create(db, student.student_id)

        assert isinstance(streak, Streak)
        assert streak.student_id == student.student_id
        assert streak.current_streak == 0
        assert streak.longest_streak == 0
        assert streak.milestones_achieved == []

    async def test_get_or_create_is_idempotent(self, db: AsyncSession) -> None:
        """Calling get_or_create twice returns the same row without duplication."""
        student = await _create_student(db, _TELEGRAM_ID_BASE + 31)
        repo = StreakRepository()

        s1 = await repo.get_or_create(db, student.student_id)
        s2 = await repo.get_or_create(db, student.student_id)

        assert s1.student_id == s2.student_id
        assert s1.current_streak == s2.current_streak

    async def test_streak_data_reflects_practice_history(self, db: AsyncSession) -> None:
        """After record_practice calls, get_or_create returns up-to-date streak data.

        This mirrors what the GET /streak endpoint would return.
        """
        student = await _create_student(db, _TELEGRAM_ID_BASE + 32)
        repo = StreakRepository()

        for day_offset in range(3):
            d = date(2026, 3, 1) + timedelta(days=day_offset)
            await repo.record_practice(db, student.student_id, d)

        streak = await repo.get_or_create(db, student.student_id)

        assert streak.current_streak == 3
        assert streak.longest_streak == 3
        assert streak.last_practice_date is not None

    async def test_milestones_achieved_persisted(self, db: AsyncSession) -> None:
        """Milestones written by record_practice are returned by get_or_create."""
        student = await _create_student(db, _TELEGRAM_ID_BASE + 33)
        repo = StreakRepository()

        for day_offset in range(7):
            d = _MILESTONE_DAY + timedelta(days=day_offset)
            await repo.record_practice(db, student.student_id, d)

        streak = await repo.get_or_create(db, student.student_id)
        assert 7 in streak.milestones_achieved
