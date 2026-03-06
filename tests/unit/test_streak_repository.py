"""
Unit tests for StreakRepository and StudentRepository.

Covers REQ-009 (streak tracking), REQ-010 (streak display),
REQ-012 (milestone detection), and REQ-004 (difficulty_level).

Uses an in-memory SQLite database (no external services required).
"""

from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.models.base import Base
from src.models.session import Session, SessionStatus
from src.models.streak import Streak
from src.models.student import Student
from src.repositories.streak_repository import StreakRepository
from src.repositories.student_repository import StudentRepository

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def engine():
    """Create a fresh in-memory SQLite engine for each test."""
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
    """Yield a single async session bound to the in-memory engine."""
    factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with factory() as session:
        yield session


async def _make_student(db: AsyncSession, telegram_id: int = 2001) -> Student:
    """Create and flush a test student."""
    student = Student(telegram_id=telegram_id, name="Streak Test", grade=7, language="en")
    db.add(student)
    await db.flush()
    return student


async def _make_completed_session(
    db: AsyncSession,
    student_id: int,
    completed_at: datetime,
) -> Session:
    """Create a completed session with a specific completion time."""
    session = Session(
        student_id=student_id,
        date=completed_at,
        status=SessionStatus.COMPLETED,
        problem_ids=[1, 2, 3, 4, 5],
        expires_at=completed_at + timedelta(minutes=30),
        completed_at=completed_at,
        total_time_seconds=0,
        problems_correct=0,
    )
    db.add(session)
    await db.flush()
    return session


TODAY = date(2026, 3, 5)
YESTERDAY = TODAY - timedelta(days=1)
TWO_DAYS_AGO = TODAY - timedelta(days=2)
EIGHT_DAYS_AGO = TODAY - timedelta(days=8)


# ---------------------------------------------------------------------------
# StreakRepository.get_or_create
# ---------------------------------------------------------------------------


class TestGetOrCreate:
    """Tests for StreakRepository.get_or_create."""

    async def test_creates_streak_for_new_student(self, db: AsyncSession) -> None:
        """Should create a fresh streak row when none exists."""
        student = await _make_student(db)
        repo = StreakRepository()

        streak = await repo.get_or_create(db, student.student_id)

        assert streak.student_id == student.student_id
        assert streak.current_streak == 0
        assert streak.longest_streak == 0
        assert streak.last_practice_date is None
        assert streak.milestones_achieved == []

    async def test_returns_existing_streak(self, db: AsyncSession) -> None:
        """Should return existing streak row unchanged when one exists."""
        student = await _make_student(db)
        # Pre-create a streak
        existing = Streak(
            student_id=student.student_id,
            current_streak=5,
            longest_streak=10,
            milestones_achieved=[],
        )
        db.add(existing)
        await db.flush()

        repo = StreakRepository()
        streak = await repo.get_or_create(db, student.student_id)

        assert streak.current_streak == 5
        assert streak.longest_streak == 10

    async def test_idempotent_on_double_call(self, db: AsyncSession) -> None:
        """Calling get_or_create twice should not duplicate the row."""
        student = await _make_student(db)
        repo = StreakRepository()

        s1 = await repo.get_or_create(db, student.student_id)
        s2 = await repo.get_or_create(db, student.student_id)

        assert s1.student_id == s2.student_id
        assert s1.current_streak == s2.current_streak


# ---------------------------------------------------------------------------
# StreakRepository.record_practice — streak arithmetic
# ---------------------------------------------------------------------------


class TestRecordPracticeStreakArithmetic:
    """Tests for streak increment, reset, and idempotency logic."""

    async def test_first_practice_starts_streak_at_1(self, db: AsyncSession) -> None:
        """First-ever practice should start streak at 1."""
        student = await _make_student(db)
        repo = StreakRepository()

        streak, _ = await repo.record_practice(db, student.student_id, TODAY)

        assert streak.current_streak == 1

    async def test_consecutive_day_increments_streak(self, db: AsyncSession) -> None:
        """Practice on consecutive days should increment the streak."""
        student = await _make_student(db)
        repo = StreakRepository()

        await repo.record_practice(db, student.student_id, YESTERDAY)
        streak, _ = await repo.record_practice(db, student.student_id, TODAY)

        assert streak.current_streak == 2

    async def test_streak_increments_across_multiple_consecutive_days(
        self, db: AsyncSession
    ) -> None:
        """Streak should keep growing over multiple consecutive days."""
        student = await _make_student(db)
        repo = StreakRepository()

        for offset in range(5):
            d = TODAY - timedelta(days=4 - offset)
            streak, _ = await repo.record_practice(db, student.student_id, d)

        assert streak.current_streak == 5

    async def test_missed_day_resets_streak_to_1(self, db: AsyncSession) -> None:
        """Practicing after a gap resets the streak to 1 (not 0)."""
        student = await _make_student(db)
        repo = StreakRepository()

        # Practice 2 days ago (gap — yesterday was missed)
        await repo.record_practice(db, student.student_id, TWO_DAYS_AGO)
        streak, _ = await repo.record_practice(db, student.student_id, TODAY)

        assert streak.current_streak == 1

    async def test_same_day_call_is_no_op(self, db: AsyncSession) -> None:
        """Calling record_practice twice on the same day must not double-count."""
        student = await _make_student(db)
        repo = StreakRepository()

        streak_first, _ = await repo.record_practice(db, student.student_id, TODAY)
        streak_second, _ = await repo.record_practice(db, student.student_id, TODAY)

        assert streak_first.current_streak == streak_second.current_streak == 1

    async def test_same_day_no_op_after_consecutive(self, db: AsyncSession) -> None:
        """Same-day no-op should still return the current streak, not reset it."""
        student = await _make_student(db)
        repo = StreakRepository()

        await repo.record_practice(db, student.student_id, YESTERDAY)
        await repo.record_practice(db, student.student_id, TODAY)
        streak, _ = await repo.record_practice(db, student.student_id, TODAY)  # second call today

        assert streak.current_streak == 2


# ---------------------------------------------------------------------------
# StreakRepository.record_practice — longest_streak tracking
# ---------------------------------------------------------------------------


class TestLongestStreakTracking:
    """Tests that longest_streak is updated correctly."""

    async def test_longest_streak_updated_when_current_exceeds_it(self, db: AsyncSession) -> None:
        """longest_streak should update when current_streak beats it."""
        student = await _make_student(db)
        repo = StreakRepository()

        for offset in range(3):
            d = TODAY - timedelta(days=2 - offset)
            streak, _ = await repo.record_practice(db, student.student_id, d)

        assert streak.current_streak == 3
        assert streak.longest_streak == 3

    async def test_longest_streak_preserved_after_reset(self, db: AsyncSession) -> None:
        """longest_streak should not decrease when current_streak resets."""
        student = await _make_student(db)
        repo = StreakRepository()

        # Build a 5-day streak
        for offset in range(5):
            d = EIGHT_DAYS_AGO + timedelta(days=offset)
            await repo.record_practice(db, student.student_id, d)

        # Gap: start fresh today
        streak, _ = await repo.record_practice(db, student.student_id, TODAY)

        assert streak.current_streak == 1
        assert streak.longest_streak == 5


# ---------------------------------------------------------------------------
# StreakRepository.record_practice — milestone detection (REQ-012)
# ---------------------------------------------------------------------------


class TestMilestoneDetection:
    """Tests for milestone detection at 7, 14, and 30 days."""

    async def _build_streak_to(
        self, db: AsyncSession, student_id: int, days: int
    ) -> tuple[Streak, list[int]]:
        """Helper: build a streak of exactly ``days`` consecutive days ending today."""
        repo = StreakRepository()
        streak: Streak | None = None
        all_new_milestones: list[int] = []
        for offset in range(days):
            d = TODAY - timedelta(days=days - 1 - offset)
            streak, new = await repo.record_practice(db, student_id, d)
            all_new_milestones.extend(new)
        assert streak is not None
        return streak, all_new_milestones

    async def test_milestone_7_detected(self, db: AsyncSession) -> None:
        """7-day milestone should be detected when streak reaches 7."""
        student = await _make_student(db)
        streak, milestones = await self._build_streak_to(db, student.student_id, 7)

        assert streak.current_streak == 7
        assert 7 in milestones
        assert 7 in streak.milestones_achieved

    async def test_milestone_14_detected(self, db: AsyncSession) -> None:
        """14-day milestone should fire at day 14."""
        student = await _make_student(db)
        streak, milestones = await self._build_streak_to(db, student.student_id, 14)

        assert 14 in milestones
        assert 14 in streak.milestones_achieved

    async def test_milestone_30_detected(self, db: AsyncSession) -> None:
        """30-day milestone should fire at day 30."""
        student = await _make_student(db)
        streak, milestones = await self._build_streak_to(db, student.student_id, 30)

        assert 30 in milestones
        assert 30 in streak.milestones_achieved

    async def test_milestone_not_double_counted(self, db: AsyncSession) -> None:
        """Milestones already in milestones_achieved must not appear again."""
        student = await _make_student(db)
        repo = StreakRepository()

        # Build to day 7 (milestone fires)
        _streak, first_milestones = await self._build_streak_to(db, student.student_id, 7)
        assert 7 in first_milestones

        # Day 8 — milestone 7 must NOT fire again
        _, second_milestones = await repo.record_practice(
            db, student.student_id, TODAY + timedelta(days=1)
        )
        assert 7 not in second_milestones

    async def test_no_milestone_before_threshold(self, db: AsyncSession) -> None:
        """No milestone should fire for a 3-day streak."""
        student = await _make_student(db)
        _, milestones = await self._build_streak_to(db, student.student_id, 3)

        assert milestones == []

    async def test_multiple_milestones_fire_correctly(self, db: AsyncSession) -> None:
        """milestones_achieved should contain all previously hit milestones."""
        student = await _make_student(db)
        await self._build_streak_to(db, student.student_id, 14)

        repo = StreakRepository()
        streak = await repo.get_for_student(db, student.student_id)
        assert streak is not None
        assert 7 in streak.milestones_achieved
        assert 14 in streak.milestones_achieved


# ---------------------------------------------------------------------------
# StreakRepository.get_for_student
# ---------------------------------------------------------------------------


class TestGetForStudent:
    """Tests for StreakRepository.get_for_student."""

    async def test_returns_none_when_no_streak(self, db: AsyncSession) -> None:
        """Should return None when no streak row exists."""
        student = await _make_student(db)
        repo = StreakRepository()

        result = await repo.get_for_student(db, student.student_id)

        assert result is None

    async def test_returns_streak_when_exists(self, db: AsyncSession) -> None:
        """Should return the existing streak row."""
        student = await _make_student(db)
        repo = StreakRepository()

        await repo.get_or_create(db, student.student_id)
        result = await repo.get_for_student(db, student.student_id)

        assert result is not None
        assert result.student_id == student.student_id


# ---------------------------------------------------------------------------
# StreakRepository.get_last_7_days
# ---------------------------------------------------------------------------


class TestGetLast7Days:
    """Tests for get_last_7_days — calendar view for /streak endpoint."""

    async def test_returns_empty_for_new_student(self, db: AsyncSession) -> None:
        """Should return empty list when no sessions exist."""
        student = await _make_student(db)
        repo = StreakRepository()

        result = await repo.get_last_7_days(db, student.student_id)

        assert result == []

    async def test_returns_dates_of_completed_sessions(self, db: AsyncSession) -> None:
        """Should return calendar dates where student has completed sessions."""
        student = await _make_student(db)
        repo = StreakRepository()
        today_dt = datetime.now(UTC).replace(hour=10, minute=0, second=0, microsecond=0)
        await _make_completed_session(db, student.student_id, today_dt)

        result = await repo.get_last_7_days(db, student.student_id)

        assert len(result) == 1
        assert result[0] == today_dt.date()

    async def test_deduplicates_multiple_sessions_same_day(self, db: AsyncSession) -> None:
        """Multiple completed sessions on same day should count as one date."""
        student = await _make_student(db)
        repo = StreakRepository()
        today_dt = datetime.now(UTC).replace(hour=9, minute=0, second=0, microsecond=0)
        today_dt2 = today_dt.replace(hour=15)
        await _make_completed_session(db, student.student_id, today_dt)
        await _make_completed_session(db, student.student_id, today_dt2)

        result = await repo.get_last_7_days(db, student.student_id)

        assert len(result) == 1

    async def test_excludes_sessions_older_than_7_days(self, db: AsyncSession) -> None:
        """Sessions from 8+ days ago should not appear in the 7-day window."""
        student = await _make_student(db)
        repo = StreakRepository()
        old_dt = datetime.now(UTC) - timedelta(days=8)
        await _make_completed_session(db, student.student_id, old_dt)

        result = await repo.get_last_7_days(db, student.student_id)

        assert result == []


# ---------------------------------------------------------------------------
# StudentRepository — difficulty level (REQ-004)
# ---------------------------------------------------------------------------


class TestStudentRepositoryDifficulty:
    """Tests for StudentRepository difficulty get/set methods."""

    async def test_new_student_has_default_difficulty_1(self, db: AsyncSession) -> None:
        """New students should have difficulty_level=1 (easy) by default."""
        student = await _make_student(db)

        assert student.difficulty_level == 1

    async def test_get_difficulty_returns_level(self, db: AsyncSession) -> None:
        """get_difficulty should return the student's current level."""
        student = await _make_student(db)
        repo = StudentRepository()

        level = await repo.get_difficulty(db, student.student_id)

        assert level == 1

    async def test_set_difficulty_updates_level(self, db: AsyncSession) -> None:
        """set_difficulty should update and flush the new level."""
        student = await _make_student(db)
        repo = StudentRepository()

        await repo.set_difficulty(db, student, 2)

        assert student.difficulty_level == 2

    async def test_set_difficulty_clamps_above_max(self, db: AsyncSession) -> None:
        """set_difficulty should clamp values above 3 to 3."""
        student = await _make_student(db)
        repo = StudentRepository()

        await repo.set_difficulty(db, student, 99)

        assert student.difficulty_level == 3

    async def test_set_difficulty_clamps_below_min(self, db: AsyncSession) -> None:
        """set_difficulty should clamp values below 1 to 1."""
        student = await _make_student(db)
        repo = StudentRepository()

        await repo.set_difficulty(db, student, 0)

        assert student.difficulty_level == 1

    async def test_get_difficulty_returns_1_for_missing_student(self, db: AsyncSession) -> None:
        """get_difficulty returns 1 (easy) as safe default when student is missing."""
        repo = StudentRepository()

        level = await repo.get_difficulty(db, student_id=99999)

        assert level == 1
