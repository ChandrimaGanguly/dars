"""
Unit + integration tests for SessionRepository.

Uses SQLite in-memory via in-test engine setup.
Coverage target: ≥80% of src/repositories/session_repository.py.
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.models.base import Base
from src.models.problem import Problem
from src.models.session import Session, SessionStatus
from src.models.student import Student
from src.repositories.session_repository import SessionRepository

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


async def _make_student(db: AsyncSession, telegram_id: int = 1001) -> Student:
    """Create and flush a test student."""
    student = Student(telegram_id=telegram_id, name="Test Student", grade=7, language="en")
    db.add(student)
    await db.flush()
    return student


def _make_problem_obj(
    grade: int = 7,
    topic: str = "percentages",
    question_en: str = "Test problem?",
) -> Problem:
    """Return an unsaved Problem instance."""
    return Problem(
        grade=grade,
        topic=topic,
        difficulty=1,
        question_en=question_en,
        question_bn="পরীক্ষামূলক সমস্যা?",
        answer="20",
        hints=[
            {"hint_number": 1, "text_en": "Hint.", "text_bn": "ইঙ্গিত।", "is_ai_generated": False}
        ],
        answer_type="numeric",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCreateSession:
    """Tests for SessionRepository.create_session()."""

    @pytest.mark.asyncio
    async def test_creates_session_with_correct_fields(self, db: AsyncSession) -> None:
        """create_session should persist and return a session with expected defaults."""
        repo = SessionRepository()
        student = await _make_student(db)

        session = await repo.create_session(
            db, student_id=student.student_id, problem_ids=[1, 2, 3, 4, 5]
        )

        assert session.session_id is not None
        assert session.student_id == student.student_id
        assert session.problem_ids == [1, 2, 3, 4, 5]
        assert session.status == SessionStatus.IN_PROGRESS
        assert session.problems_correct == 0
        assert session.total_time_seconds == 0

    @pytest.mark.asyncio
    async def test_session_expires_30_minutes_from_now(self, db: AsyncSession) -> None:
        """Session expires_at should be ~30 minutes in the future."""
        repo = SessionRepository()
        student = await _make_student(db, telegram_id=1002)
        before = datetime.now(UTC)
        session = await repo.create_session(db, student_id=student.student_id, problem_ids=[1])
        after = datetime.now(UTC)

        # expires_at should be between 29 and 31 minutes in the future.
        lower = before + timedelta(minutes=29)
        upper = after + timedelta(minutes=31)
        # SQLite stores tz-naive; normalise for comparison.
        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        assert lower <= expires_at <= upper


class TestGetActiveSessionForToday:
    """Tests for SessionRepository.get_active_session_for_today()."""

    @pytest.mark.asyncio
    async def test_returns_none_for_student_with_no_sessions(self, db: AsyncSession) -> None:
        """Should return None if student has no sessions."""
        repo = SessionRepository()
        result = await repo.get_active_session_for_today(db, student_id=9999)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_active_session_created_today(self, db: AsyncSession) -> None:
        """Should return the in_progress session created today."""
        repo = SessionRepository()
        student = await _make_student(db, telegram_id=1003)
        created_session = await repo.create_session(
            db, student_id=student.student_id, problem_ids=[1]
        )
        await db.flush()

        result = await repo.get_active_session_for_today(db, student_id=student.student_id)
        assert result is not None
        assert result.session_id == created_session.session_id

    @pytest.mark.asyncio
    async def test_returns_none_for_completed_session(self, db: AsyncSession) -> None:
        """A completed session from today should not be returned as 'active'."""
        repo = SessionRepository()
        student = await _make_student(db, telegram_id=1004)
        session = await repo.create_session(db, student_id=student.student_id, problem_ids=[1])
        # Mark it complete.
        await repo.mark_session_complete(db, session)

        result = await repo.get_active_session_for_today(db, student_id=student.student_id)
        assert result is None


class TestGetSessionById:
    """Tests for SessionRepository.get_session_by_id()."""

    @pytest.mark.asyncio
    async def test_returns_session_when_found(self, db: AsyncSession) -> None:
        """Should return the correct session."""
        repo = SessionRepository()
        student = await _make_student(db, telegram_id=1005)
        session = await repo.create_session(db, student_id=student.student_id, problem_ids=[1, 2])
        await db.flush()

        result = await repo.get_session_by_id(db, session.session_id)
        assert result is not None
        assert result.session_id == session.session_id

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, db: AsyncSession) -> None:
        """Should return None for a non-existent session_id."""
        repo = SessionRepository()
        result = await repo.get_session_by_id(db, 99999)
        assert result is None


class TestMarkSessionComplete:
    """Tests for SessionRepository.mark_session_complete()."""

    @pytest.mark.asyncio
    async def test_status_becomes_completed(self, db: AsyncSession) -> None:
        """Status should change from in_progress to completed."""
        repo = SessionRepository()
        student = await _make_student(db, telegram_id=1006)
        session = await repo.create_session(db, student_id=student.student_id, problem_ids=[1])
        assert session.status == SessionStatus.IN_PROGRESS

        completed = await repo.mark_session_complete(db, session)
        assert completed.status == SessionStatus.COMPLETED
        assert completed.completed_at is not None

    @pytest.mark.asyncio
    async def test_completed_at_is_set(self, db: AsyncSession) -> None:
        """completed_at should be set to approximately now."""
        repo = SessionRepository()
        student = await _make_student(db, telegram_id=1007)
        session = await repo.create_session(db, student_id=student.student_id, problem_ids=[1])
        before = datetime.now(UTC)
        completed = await repo.mark_session_complete(db, session)
        after = datetime.now(UTC)

        completed_at = completed.completed_at
        if completed_at and completed_at.tzinfo is None:
            completed_at = completed_at.replace(tzinfo=UTC)
        assert completed_at is not None
        assert before <= completed_at <= after


class TestIncrementCorrectCount:
    """Tests for SessionRepository.increment_correct_count()."""

    @pytest.mark.asyncio
    async def test_increments_by_one(self, db: AsyncSession) -> None:
        """problems_correct should go from 0 to 1."""
        repo = SessionRepository()
        student = await _make_student(db, telegram_id=1008)
        session = await repo.create_session(db, student_id=student.student_id, problem_ids=[1])
        assert session.problems_correct == 0

        updated = await repo.increment_correct_count(db, session)
        assert updated.problems_correct == 1

    @pytest.mark.asyncio
    async def test_increments_multiple_times(self, db: AsyncSession) -> None:
        """Incrementing multiple times should accumulate correctly."""
        repo = SessionRepository()
        student = await _make_student(db, telegram_id=1009)
        session = await repo.create_session(
            db, student_id=student.student_id, problem_ids=[1, 2, 3]
        )
        await repo.increment_correct_count(db, session)
        await repo.increment_correct_count(db, session)
        updated = await repo.increment_correct_count(db, session)
        assert updated.problems_correct == 3


class TestExpireStaleSessions:
    """Tests for SessionRepository.expire_stale_sessions()."""

    @pytest.mark.asyncio
    async def test_expired_sessions_are_abandoned(self, db: AsyncSession) -> None:
        """Sessions past expires_at should be marked abandoned."""
        repo = SessionRepository()
        student = await _make_student(db, telegram_id=1010)

        # Create a session that already expired (expires_at in the past).
        now = datetime.now(UTC)
        stale_session = Session(
            student_id=student.student_id,
            date=now - timedelta(hours=2),
            status=SessionStatus.IN_PROGRESS,
            problem_ids=[1],
            expires_at=now - timedelta(hours=1),
            total_time_seconds=0,
            problems_correct=0,
            created_at=now - timedelta(hours=2),
        )
        db.add(stale_session)
        await db.flush()

        count = await repo.expire_stale_sessions(db)
        assert count == 1

        refreshed = await repo.get_session_by_id(db, stale_session.session_id)
        assert refreshed is not None
        assert refreshed.status == SessionStatus.ABANDONED

    @pytest.mark.asyncio
    async def test_active_sessions_not_expired(self, db: AsyncSession) -> None:
        """Sessions that are not past expires_at must remain in_progress."""
        repo = SessionRepository()
        student = await _make_student(db, telegram_id=1011)

        # Session that expires in the future.
        session = await repo.create_session(db, student_id=student.student_id, problem_ids=[1])
        await db.flush()

        count = await repo.expire_stale_sessions(db)
        assert count == 0

        refreshed = await repo.get_session_by_id(db, session.session_id)
        assert refreshed is not None
        assert refreshed.status == SessionStatus.IN_PROGRESS


class TestGetCompletedSessionsForStudent:
    """Tests for SessionRepository.get_completed_sessions_for_student()."""

    @pytest.mark.asyncio
    async def test_returns_completed_sessions_only(self, db: AsyncSession) -> None:
        """Only completed sessions should be returned."""
        repo = SessionRepository()
        student = await _make_student(db, telegram_id=1012)

        # Create one in_progress and one completed session.
        s_active = await repo.create_session(db, student_id=student.student_id, problem_ids=[1])
        s_done = await repo.create_session(db, student_id=student.student_id, problem_ids=[2])
        await repo.mark_session_complete(db, s_done)

        results = await repo.get_completed_sessions_for_student(db, student_id=student.student_id)
        ids = {s.session_id for s in results}
        assert s_done.session_id in ids
        assert s_active.session_id not in ids

    @pytest.mark.asyncio
    async def test_limit_is_respected(self, db: AsyncSession) -> None:
        """limit parameter should cap the number of sessions returned."""
        repo = SessionRepository()
        student = await _make_student(db, telegram_id=1013)

        for i in range(5):
            s = await repo.create_session(db, student_id=student.student_id, problem_ids=[i + 1])
            await repo.mark_session_complete(db, s)

        results = await repo.get_completed_sessions_for_student(
            db, student_id=student.student_id, limit=3
        )
        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_returns_empty_for_student_with_no_completed_sessions(
        self, db: AsyncSession
    ) -> None:
        """Should return empty list if student has no completed sessions."""
        repo = SessionRepository()
        student = await _make_student(db, telegram_id=1014)
        # Leave the session in_progress.
        await repo.create_session(db, student_id=student.student_id, problem_ids=[1])

        results = await repo.get_completed_sessions_for_student(db, student_id=student.student_id)
        assert results == []
