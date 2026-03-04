"""
Unit + integration tests for ResponseRepository.

Uses SQLite in-memory for each test.
Coverage target: ≥80% of src/repositories/response_repository.py.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.models.base import Base
from src.models.problem import Problem
from src.models.response import ConfidenceLevel
from src.models.session import Session, SessionStatus
from src.models.student import Student
from src.repositories.response_repository import ResponseRepository, _confidence_from_hints

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_student(db: AsyncSession, telegram_id: int = 2001) -> Student:
    """Create and flush a test student."""
    student = Student(telegram_id=telegram_id, name="Response Test", grade=7, language="en")
    db.add(student)
    await db.flush()
    return student


async def _make_problem(
    db: AsyncSession,
    topic: str = "percentages",
    question_en: str = "Test problem?",
) -> Problem:
    """Create and flush a test problem."""
    problem = Problem(
        grade=7,
        topic=topic,
        difficulty=1,
        question_en=question_en,
        question_bn="পরীক্ষামূলক?",
        answer="20",
        hints=[
            {"hint_number": 1, "text_en": "Hint.", "text_bn": "ইঙ্গিত।", "is_ai_generated": False}
        ],
        answer_type="numeric",
    )
    db.add(problem)
    await db.flush()
    return problem


async def _make_session(
    db: AsyncSession,
    student_id: int,
    problem_ids: list[int] | None = None,
    created_at: datetime | None = None,
) -> Session:
    """Create and flush a test session."""
    now = created_at or datetime.now(UTC)
    session = Session(
        student_id=student_id,
        date=now,
        status=SessionStatus.IN_PROGRESS,
        problem_ids=problem_ids or [1],
        expires_at=now + timedelta(hours=1),
        total_time_seconds=0,
        problems_correct=0,
        created_at=now,
    )
    db.add(session)
    await db.flush()
    return session


# ---------------------------------------------------------------------------
# Tests: _confidence_from_hints (pure function)
# ---------------------------------------------------------------------------


class TestConfidenceFromHints:
    """Tests for the _confidence_from_hints helper."""

    def test_zero_hints_is_high(self) -> None:
        """0 hints used -> high confidence."""
        assert _confidence_from_hints(0) == ConfidenceLevel.HIGH

    def test_one_hint_is_medium(self) -> None:
        """1 hint used -> medium confidence."""
        assert _confidence_from_hints(1) == ConfidenceLevel.MEDIUM

    def test_two_hints_is_low(self) -> None:
        """2 hints used -> low confidence."""
        assert _confidence_from_hints(2) == ConfidenceLevel.LOW

    def test_three_hints_is_low(self) -> None:
        """3 hints used -> low confidence."""
        assert _confidence_from_hints(3) == ConfidenceLevel.LOW


# ---------------------------------------------------------------------------
# Tests: create_response
# ---------------------------------------------------------------------------


class TestCreateResponse:
    """Tests for ResponseRepository.create_response()."""

    @pytest.mark.asyncio
    async def test_creates_response_with_correct_fields(self, db: AsyncSession) -> None:
        """create_response should persist a response with all provided fields."""
        repo = ResponseRepository()
        student = await _make_student(db, telegram_id=2001)
        problem = await _make_problem(db, question_en="How much is 25% of 80?")
        session = await _make_session(db, student.student_id, [problem.problem_id])

        response = await repo.create_response(
            db,
            session_id=session.session_id,
            problem_id=problem.problem_id,
            student_answer="20",
            is_correct=True,
            hints_used=0,
            time_spent_seconds=45,
        )

        assert response.response_id is not None
        assert response.session_id == session.session_id
        assert response.problem_id == problem.problem_id
        assert response.student_answer == "20"
        assert response.is_correct is True
        assert response.hints_used == 0
        assert response.time_spent_seconds == 45

    @pytest.mark.asyncio
    async def test_confidence_derived_from_hints_when_not_provided(self, db: AsyncSession) -> None:
        """confidence_level should be auto-derived when not explicitly set."""
        repo = ResponseRepository()
        student = await _make_student(db, telegram_id=2002)
        problem = await _make_problem(db, question_en="Q for confidence test?")
        session = await _make_session(db, student.student_id, [problem.problem_id])

        response = await repo.create_response(
            db,
            session_id=session.session_id,
            problem_id=problem.problem_id,
            student_answer="20",
            is_correct=True,
            hints_used=2,
            time_spent_seconds=60,
        )
        assert response.confidence_level == ConfidenceLevel.LOW

    @pytest.mark.asyncio
    async def test_explicit_confidence_is_respected(self, db: AsyncSession) -> None:
        """Explicitly passed confidence_level should override derivation."""
        repo = ResponseRepository()
        student = await _make_student(db, telegram_id=2003)
        problem = await _make_problem(db, question_en="Q for explicit confidence?")
        session = await _make_session(db, student.student_id, [problem.problem_id])

        response = await repo.create_response(
            db,
            session_id=session.session_id,
            problem_id=problem.problem_id,
            student_answer="20",
            is_correct=False,
            hints_used=3,
            time_spent_seconds=90,
            confidence_level=ConfidenceLevel.HIGH,  # explicitly overridden
        )
        assert response.confidence_level == ConfidenceLevel.HIGH


# ---------------------------------------------------------------------------
# Tests: get_response_for_problem
# ---------------------------------------------------------------------------


class TestGetResponseForProblem:
    """Tests for ResponseRepository.get_response_for_problem()."""

    @pytest.mark.asyncio
    async def test_returns_response_when_found(self, db: AsyncSession) -> None:
        """Should return the response for a problem in the session."""
        repo = ResponseRepository()
        student = await _make_student(db, telegram_id=2004)
        problem = await _make_problem(db, question_en="Found response problem?")
        session = await _make_session(db, student.student_id, [problem.problem_id])

        created = await repo.create_response(
            db, session.session_id, problem.problem_id, "20", True, 0, 30
        )

        found = await repo.get_response_for_problem(db, session.session_id, problem.problem_id)
        assert found is not None
        assert found.response_id == created.response_id

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, db: AsyncSession) -> None:
        """Should return None if no response exists for the session+problem combo."""
        repo = ResponseRepository()
        result = await repo.get_response_for_problem(db, 99999, 99999)
        assert result is None


# ---------------------------------------------------------------------------
# Tests: get_topic_accuracy_for_student
# ---------------------------------------------------------------------------


class TestGetTopicAccuracyForStudent:
    """Tests for ResponseRepository.get_topic_accuracy_for_student()."""

    @pytest.mark.asyncio
    async def test_returns_neutral_baseline_for_no_history(self, db: AsyncSession) -> None:
        """Should return 0.5 baseline when student has no history for topic."""
        repo = ResponseRepository()
        result = await repo.get_topic_accuracy_for_student(db, student_id=9999, topic="algebra")
        assert result == 0.5

    @pytest.mark.asyncio
    async def test_correct_accuracy_calculation(self, db: AsyncSession) -> None:
        """Accuracy should equal correct_count / total_count."""
        repo = ResponseRepository()
        student = await _make_student(db, telegram_id=2005)
        p1 = await _make_problem(db, topic="algebra", question_en="Alg 1?")
        p2 = await _make_problem(db, topic="algebra", question_en="Alg 2?")
        session = await _make_session(db, student.student_id, [p1.problem_id, p2.problem_id])

        # 1 correct, 1 incorrect.
        await repo.create_response(db, session.session_id, p1.problem_id, "5", True, 0, 30)
        await repo.create_response(db, session.session_id, p2.problem_id, "wrong", False, 1, 60)

        accuracy = await repo.get_topic_accuracy_for_student(
            db, student_id=student.student_id, topic="algebra"
        )
        assert accuracy == pytest.approx(0.5)

    @pytest.mark.asyncio
    async def test_perfect_accuracy(self, db: AsyncSession) -> None:
        """All correct answers should give accuracy of 1.0."""
        repo = ResponseRepository()
        student = await _make_student(db, telegram_id=2006)
        problem = await _make_problem(db, topic="percentages", question_en="100% q?")
        session = await _make_session(db, student.student_id, [problem.problem_id])

        await repo.create_response(db, session.session_id, problem.problem_id, "20", True, 0, 30)

        accuracy = await repo.get_topic_accuracy_for_student(
            db, student_id=student.student_id, topic="percentages"
        )
        assert accuracy == pytest.approx(1.0)

    @pytest.mark.asyncio
    async def test_returns_neutral_for_unknown_topic(self, db: AsyncSession) -> None:
        """Topic that doesn't exist in DB should return 0.5."""
        repo = ResponseRepository()
        student = await _make_student(db, telegram_id=2007)
        result = await repo.get_topic_accuracy_for_student(
            db, student_id=student.student_id, topic="nonexistent_topic_xyz"
        )
        assert result == 0.5

    @pytest.mark.asyncio
    async def test_returns_neutral_when_topic_exists_but_no_responses(
        self, db: AsyncSession
    ) -> None:
        """Student has sessions but never answered this topic -> 0.5."""
        repo = ResponseRepository()
        student = await _make_student(db, telegram_id=2011)
        # Create a session (so student has history) but don't answer any algebra.
        await _make_session(db, student.student_id, [1])
        # Create the problem in the DB so the topic exists.
        await _make_problem(db, topic="algebra", question_en="Untried algebra?")
        # No responses recorded for this student + topic combo.

        result = await repo.get_topic_accuracy_for_student(
            db, student_id=student.student_id, topic="algebra"
        )
        # Should return neutral baseline since no responses exist.
        assert result == 0.5


# ---------------------------------------------------------------------------
# Tests: get_all_topic_accuracies
# ---------------------------------------------------------------------------


class TestGetAllTopicAccuracies:
    """Tests for ResponseRepository.get_all_topic_accuracies()."""

    @pytest.mark.asyncio
    async def test_returns_empty_for_no_history(self, db: AsyncSession) -> None:
        """Student with no responses should get empty dict."""
        repo = ResponseRepository()
        result = await repo.get_all_topic_accuracies(db, student_id=9998)
        assert result == {}

    @pytest.mark.asyncio
    async def test_returns_accuracies_for_all_attempted_topics(self, db: AsyncSession) -> None:
        """All attempted topics should appear in result dict."""
        repo = ResponseRepository()
        student = await _make_student(db, telegram_id=2008)
        p_alg = await _make_problem(db, topic="algebra", question_en="Alg?")
        p_pct = await _make_problem(db, topic="percentages", question_en="Pct?")
        session = await _make_session(db, student.student_id, [p_alg.problem_id, p_pct.problem_id])

        await repo.create_response(db, session.session_id, p_alg.problem_id, "5", True, 0, 30)
        await repo.create_response(db, session.session_id, p_pct.problem_id, "wrong", False, 1, 40)

        accuracies = await repo.get_all_topic_accuracies(db, student_id=student.student_id)
        assert "algebra" in accuracies
        assert "percentages" in accuracies
        assert accuracies["algebra"] == pytest.approx(1.0)
        assert accuracies["percentages"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Tests: update_hint_count
# ---------------------------------------------------------------------------


class TestUpdateHintCount:
    """Tests for ResponseRepository.update_hint_count()."""

    @pytest.mark.asyncio
    async def test_increments_hint_count_and_appends_hint(self, db: AsyncSession) -> None:
        """hints_used should increase and hint should appear in hints_viewed."""
        repo = ResponseRepository()
        student = await _make_student(db, telegram_id=2009)
        problem = await _make_problem(db, question_en="Hint update test?")
        session = await _make_session(db, student.student_id, [problem.problem_id])

        response = await repo.create_response(
            db, session.session_id, problem.problem_id, "", False, 0, 10
        )
        assert response.hints_used == 0
        assert response.hints_viewed == []

        hint_data: dict[str, Any] = {
            "hint_number": 1,
            "text_en": "Hint one.",
            "text_bn": "ইঙ্গিত এক।",
            "is_ai_generated": False,
        }
        updated = await repo.update_hint_count(
            db, response, new_hints_used=1, hint_viewed=hint_data
        )

        assert updated.hints_used == 1
        assert len(updated.hints_viewed) == 1
        assert updated.hints_viewed[0]["hint_number"] == 1

    @pytest.mark.asyncio
    async def test_appending_multiple_hints(self, db: AsyncSession) -> None:
        """Calling update_hint_count twice should accumulate hints_viewed."""
        repo = ResponseRepository()
        student = await _make_student(db, telegram_id=2010)
        problem = await _make_problem(db, question_en="Multi hint test?")
        session = await _make_session(db, student.student_id, [problem.problem_id])

        response = await repo.create_response(
            db, session.session_id, problem.problem_id, "", False, 0, 10
        )

        hint1: dict[str, Any] = {
            "hint_number": 1,
            "text_en": "H1.",
            "text_bn": "H1.",
            "is_ai_generated": False,
        }
        hint2: dict[str, Any] = {
            "hint_number": 2,
            "text_en": "H2.",
            "text_bn": "H2.",
            "is_ai_generated": False,
        }

        response = await repo.update_hint_count(db, response, new_hints_used=1, hint_viewed=hint1)
        response = await repo.update_hint_count(db, response, new_hints_used=2, hint_viewed=hint2)

        assert response.hints_used == 2
        assert len(response.hints_viewed) == 2
        assert response.hints_viewed[0]["hint_number"] == 1
        assert response.hints_viewed[1]["hint_number"] == 2
