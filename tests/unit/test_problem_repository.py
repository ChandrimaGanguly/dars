"""
Unit + integration tests for ProblemRepository.

Uses SQLite in-memory via the db_session fixture from tests/conftest.py.
Coverage target: ≥80% of src/repositories/problem_repository.py.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.models.base import Base
from src.models.problem import Problem
from src.models.response import Response
from src.models.session import Session, SessionStatus
from src.models.student import Student
from src.repositories.problem_repository import ProblemRepository

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


def _make_problem(
    grade: int = 7,
    topic: str = "percentages",
    difficulty: int = 1,
    question_en: str = "What is 25%% of 80?",
    **kwargs: Any,
) -> Problem:
    """Return an unsaved Problem instance with sane defaults."""
    return Problem(
        grade=grade,
        topic=topic,
        difficulty=difficulty,
        question_en=question_en,
        question_bn="৮০ এর ২৫% কত?",
        answer="20",
        hints=[
            {
                "hint_number": 1,
                "text_en": "Think.",
                "text_bn": "চিন্তা করো।",
                "is_ai_generated": False,
            }
        ],
        answer_type="numeric",
        **kwargs,
    )


async def _persist(db: AsyncSession, obj: Any) -> Any:
    """Add obj to session, flush, and return it."""
    db.add(obj)
    await db.flush()
    return obj


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGetProblemsByGrade:
    """Tests for ProblemRepository.get_problems_by_grade()."""

    @pytest.mark.asyncio
    async def test_returns_problems_for_grade(self, db: AsyncSession) -> None:
        """Should return only problems matching the given grade."""
        repo = ProblemRepository()
        await _persist(db, _make_problem(grade=7, topic="percentages", question_en="Q grade 7?"))
        await _persist(db, _make_problem(grade=6, topic="decimals", question_en="Q grade 6?"))

        results = await repo.get_problems_by_grade(db, grade=7)
        assert len(results) == 1
        assert results[0].grade == 7

    @pytest.mark.asyncio
    async def test_filters_by_difficulty(self, db: AsyncSession) -> None:
        """difficulty filter should narrow results."""
        repo = ProblemRepository()
        await _persist(db, _make_problem(difficulty=1, question_en="Easy Q?"))
        await _persist(db, _make_problem(difficulty=3, question_en="Hard Q?"))

        results = await repo.get_problems_by_grade(db, grade=7, difficulty=3)
        assert len(results) == 1
        assert results[0].difficulty == 3

    @pytest.mark.asyncio
    async def test_filters_by_topic(self, db: AsyncSession) -> None:
        """topic filter should narrow results."""
        repo = ProblemRepository()
        await _persist(db, _make_problem(topic="percentages", question_en="Percent Q?"))
        await _persist(db, _make_problem(topic="algebra", question_en="Algebra Q?"))

        results = await repo.get_problems_by_grade(db, grade=7, topic="algebra")
        assert len(results) == 1
        assert results[0].topic == "algebra"

    @pytest.mark.asyncio
    async def test_excludes_ids(self, db: AsyncSession) -> None:
        """exclude_ids should remove specific problems from results."""
        repo = ProblemRepository()
        p1 = await _persist(db, _make_problem(question_en="Q1?"))
        p2 = await _persist(db, _make_problem(question_en="Q2?"))
        await db.commit()

        results = await repo.get_problems_by_grade(db, grade=7, exclude_ids=[p1.problem_id])
        returned_ids = {p.problem_id for p in results}
        assert p1.problem_id not in returned_ids
        assert p2.problem_id in returned_ids

    @pytest.mark.asyncio
    async def test_empty_grade_returns_empty_list(self, db: AsyncSession) -> None:
        """Grade with no problems should return empty list."""
        repo = ProblemRepository()
        results = await repo.get_problems_by_grade(db, grade=8)
        assert results == []


class TestGetRecentlySeenProblemIds:
    """Tests for ProblemRepository.get_recently_seen_problem_ids()."""

    @pytest.mark.asyncio
    async def test_returns_empty_for_student_with_no_sessions(self, db: AsyncSession) -> None:
        """New student with no sessions should return empty list."""
        repo = ProblemRepository()
        result = await repo.get_recently_seen_problem_ids(db, student_id=999)
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_problems_from_recent_session(self, db: AsyncSession) -> None:
        """Should return problem IDs from responses within the look-back window."""
        repo = ProblemRepository()

        # Create student + problem.
        student = Student(telegram_id=1001, name="Test", grade=7, language="en")
        db.add(student)
        await db.flush()

        problem = _make_problem(question_en="Test problem?")
        db.add(problem)
        await db.flush()

        # Create a session and response within the last 7 days.
        now = datetime.now(UTC)
        session = Session(
            student_id=student.student_id,
            date=now,
            status=SessionStatus.COMPLETED,
            problem_ids=[problem.problem_id],
            expires_at=now + timedelta(hours=1),
            created_at=now,
        )
        db.add(session)
        await db.flush()

        response = Response(
            session_id=session.session_id,
            problem_id=problem.problem_id,
            student_answer="20",
            is_correct=True,
            hints_used=0,
            time_spent_seconds=30,
            evaluated_at=now,
            confidence_level="high",
            hints_viewed=[],
        )
        db.add(response)
        await db.flush()

        result = await repo.get_recently_seen_problem_ids(db, student_id=student.student_id)
        assert problem.problem_id in result

    @pytest.mark.asyncio
    async def test_excludes_old_sessions(self, db: AsyncSession) -> None:
        """Problems from sessions older than the window should not be returned."""
        repo = ProblemRepository()

        student = Student(telegram_id=1002, name="Test2", grade=7, language="en")
        db.add(student)
        await db.flush()

        problem = _make_problem(question_en="Old problem?")
        db.add(problem)
        await db.flush()

        # Session created 10 days ago (outside default 7-day window).
        old_date = datetime.now(UTC) - timedelta(days=10)
        session = Session(
            student_id=student.student_id,
            date=old_date,
            status=SessionStatus.COMPLETED,
            problem_ids=[problem.problem_id],
            expires_at=old_date + timedelta(hours=1),
            created_at=old_date,
        )
        db.add(session)
        await db.flush()

        response = Response(
            session_id=session.session_id,
            problem_id=problem.problem_id,
            student_answer="20",
            is_correct=True,
            hints_used=0,
            time_spent_seconds=30,
            evaluated_at=old_date,
            confidence_level="high",
            hints_viewed=[],
        )
        db.add(response)
        await db.flush()

        result = await repo.get_recently_seen_problem_ids(db, student_id=student.student_id, days=7)
        assert problem.problem_id not in result


class TestGetProblemById:
    """Tests for ProblemRepository.get_problem_by_id()."""

    @pytest.mark.asyncio
    async def test_returns_problem_when_found(self, db: AsyncSession) -> None:
        """Should return the correct Problem when it exists."""
        repo = ProblemRepository()
        problem = await _persist(db, _make_problem(question_en="Found me?"))
        await db.flush()

        result = await repo.get_problem_by_id(db, problem.problem_id)
        assert result is not None
        assert result.problem_id == problem.problem_id
        assert result.question_en == "Found me?"

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, db: AsyncSession) -> None:
        """Should return None for a non-existent problem_id."""
        repo = ProblemRepository()
        result = await repo.get_problem_by_id(db, 99999)
        assert result is None


class TestGetTopicsForGrade:
    """Tests for ProblemRepository.get_topics_for_grade()."""

    @pytest.mark.asyncio
    async def test_returns_distinct_topics(self, db: AsyncSession) -> None:
        """Should return unique sorted topics for the grade."""
        repo = ProblemRepository()
        await _persist(db, _make_problem(topic="algebra", question_en="Alg Q1?"))
        await _persist(db, _make_problem(topic="algebra", question_en="Alg Q2?"))
        await _persist(db, _make_problem(topic="percentages", question_en="Pct Q1?"))

        topics = await repo.get_topics_for_grade(db, grade=7)
        assert topics == ["algebra", "percentages"]

    @pytest.mark.asyncio
    async def test_returns_empty_for_grade_with_no_problems(self, db: AsyncSession) -> None:
        """Should return empty list if grade has no problems."""
        repo = ProblemRepository()
        topics = await repo.get_topics_for_grade(db, grade=8)
        assert topics == []


class TestGetProblemCountByGrade:
    """Tests for ProblemRepository.get_problem_count_by_grade()."""

    @pytest.mark.asyncio
    async def test_correct_count(self, db: AsyncSession) -> None:
        """Should count only problems for the given grade."""
        repo = ProblemRepository()
        await _persist(db, _make_problem(grade=7, question_en="G7 Q1?"))
        await _persist(db, _make_problem(grade=7, question_en="G7 Q2?"))
        await _persist(db, _make_problem(grade=6, question_en="G6 Q1?"))

        count_7 = await repo.get_problem_count_by_grade(db, grade=7)
        count_6 = await repo.get_problem_count_by_grade(db, grade=6)
        assert count_7 == 2
        assert count_6 == 1

    @pytest.mark.asyncio
    async def test_zero_for_empty_grade(self, db: AsyncSession) -> None:
        """Should return 0 for a grade with no problems."""
        repo = ProblemRepository()
        count = await repo.get_problem_count_by_grade(db, grade=8)
        assert count == 0
