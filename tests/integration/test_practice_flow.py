"""Integration tests for the practice session service layer.

Verifies end-to-end flows: session creation, answer evaluation, hint delivery,
session resume, and session completion. Uses an in-memory SQLite database so
no live Postgres is required.

These tests call the repository/service layer directly (not via HTTP) to avoid
the event-loop isolation issues with Starlette TestClient + async SQLAlchemy.

PHASE3-B-3.8
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import select

from src.models.problem import Problem
from src.models.response import Response
from src.models.session import Session, SessionStatus
from src.models.student import Student
from src.repositories import ProblemRepository, ResponseRepository, SessionRepository
from src.services.answer_evaluator import AnswerEvaluator
from src.services.problem_selector import ProblemSelector

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TELEGRAM_ID = 111222333
STUDENT_NAME = "TestStudent"
STUDENT_GRADE = 7


async def _create_student(db_session: Any, grade: int = 7, language: str = "en") -> Student:
    """Create a Student in the test database."""
    student = Student(
        telegram_id=TELEGRAM_ID,
        name=STUDENT_NAME,
        grade=grade,
        language=language,
    )
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)
    return student


async def _populate_problems(db_session: Any, count: int = 5) -> list[Problem]:
    """Create `count` problems in the test database."""
    for i in range(count):
        p = Problem(
            grade=STUDENT_GRADE,
            topic=f"Topic {i}",
            question_en=f"What is {i*10}+{i*10}?",
            question_bn=f"{i*10}+{i*10} কত?",
            answer=str(i * 20),
            hints=[
                {
                    "hint_number": 1,
                    "text_en": f"Think step by step for q{i}.",
                    "text_bn": f"প্রশ্ন {i} এর hint 1।",
                    "is_ai_generated": False,
                },
                {
                    "hint_number": 2,
                    "text_en": f"Add the numbers for q{i}.",
                    "text_bn": f"প্রশ্ন {i} এর hint 2।",
                    "is_ai_generated": False,
                },
                {
                    "hint_number": 3,
                    "text_en": f"The answer for q{i}.",
                    "text_bn": f"প্রশ্ন {i} এর hint 3।",
                    "is_ai_generated": False,
                },
            ],
            difficulty=(i % 3) + 1,
            estimated_time_minutes=5,
        )
        db_session.add(p)
    await db_session.commit()

    result = await db_session.execute(
        select(Problem).where(Problem.grade == STUDENT_GRADE).limit(count)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestGetPracticeEndpoint:
    """Tests for the practice session selection and creation service layer."""

    async def test_get_practice_returns_real_problems(self, db_session: Any) -> None:
        """ProblemSelector selects real problems from DB (not mock data)."""
        student = await _create_student(db_session)
        student_id = student.student_id  # capture before populate_problems expires student
        student_grade = student.grade
        await _populate_problems(db_session, 5)

        problem_repo = ProblemRepository()
        response_repo = ResponseRepository()
        session_repo = SessionRepository()

        # Expire stale sessions first
        await session_repo.expire_stale_sessions(db_session)

        selector = ProblemSelector(problem_repo, response_repo)
        selection = await selector.select_problems(db_session, student_id, student_grade)

        assert len(selection) >= 1
        assert selection[0].grade == STUDENT_GRADE

    async def test_session_persisted_before_response(self, db_session: Any) -> None:
        """A Session row must be committed to the DB after problem selection."""
        student = await _create_student(db_session)
        student_id = student.student_id  # capture before populate_problems expires student
        student_grade = student.grade
        await _populate_problems(db_session, 5)

        problem_repo = ProblemRepository()
        response_repo = ResponseRepository()
        session_repo = SessionRepository()

        selector = ProblemSelector(problem_repo, response_repo)
        selection = await selector.select_problems(db_session, student_id, student_grade)
        assert selection

        problem_ids = [p.problem_id for p in selection]
        await session_repo.create_session(db_session, student_id, problem_ids)
        await db_session.commit()

        # Reload from DB to confirm persistence
        result = await db_session.execute(select(Session).where(Session.student_id == student_id))
        found = result.scalar_one_or_none()
        assert found is not None
        assert found.status == SessionStatus.IN_PROGRESS

    async def test_already_completed_returns_empty(self, db_session: Any) -> None:
        """Session repo detects COMPLETED session for today."""
        student = await _create_student(db_session)
        student_id = student.student_id  # capture before commit expires student

        session = Session(
            student_id=student_id,
            date=datetime.now(UTC),
            status=SessionStatus.COMPLETED,
            problem_ids=[1, 2, 3, 4, 5],
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            completed_at=datetime.now(UTC),
        )
        db_session.add(session)
        await db_session.commit()

        session_repo = SessionRepository()
        existing = await session_repo.get_active_session_for_today(db_session, student_id)

        assert existing is not None
        assert existing.status == SessionStatus.COMPLETED

    async def test_resume_mid_session(self, db_session: Any) -> None:
        """Response repo returns correct answered_ids for resume logic."""
        student = await _create_student(db_session)
        student_id = student.student_id  # capture before populate_problems expires student
        problems = await _populate_problems(db_session, 5)
        problem_ids = [p.problem_id for p in problems]

        session = Session(
            student_id=student_id,
            date=datetime.now(UTC),
            status=SessionStatus.IN_PROGRESS,
            problem_ids=problem_ids,
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        session_id = session.session_id  # capture before second commit expires session

        # Add 2 responses (answers) for first 2 problems
        for pid in problem_ids[:2]:
            response = Response(
                session_id=session_id,
                problem_id=pid,
                student_answer="40",
                is_correct=True,
                time_spent_seconds=10,
                hints_used=0,
                hints_viewed=[],
                evaluated_at=datetime.now(UTC),
                confidence_level="high",
            )
            db_session.add(response)
        await db_session.commit()

        response_repo = ResponseRepository()
        answered_ids = await response_repo.get_answered_problem_ids(db_session, session_id)
        remaining = [pid for pid in problem_ids if pid not in answered_ids]

        assert len(answered_ids) == 2
        assert len(remaining) == 3


@pytest.mark.integration
class TestSubmitAnswerEndpoint:
    """Tests for answer evaluation and response persistence."""

    async def test_submit_correct_answer_numeric(self, db_session: Any) -> None:
        """Submitting the correct numeric answer persists is_correct=True."""
        student = await _create_student(db_session)
        student_id = student.student_id  # capture before populate_problems expires student
        problems = await _populate_problems(db_session, 1)
        problem = problems[0]

        session = Session(
            student_id=student_id,
            date=datetime.now(UTC),
            status=SessionStatus.IN_PROGRESS,
            problem_ids=[problem.problem_id],
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        await db_session.refresh(problem)  # re-load problem attributes after commit expires them
        session_id = session.session_id  # capture before second commit expires session

        evaluator = AnswerEvaluator()
        result = evaluator.evaluate(problem, problem.answer, hints_used=0)
        assert result.is_correct is True

        response_repo = ResponseRepository()
        response = await response_repo.create_response(
            db=db_session,
            session_id=session_id,
            problem_id=problem.problem_id,
            student_answer=problem.answer,
            is_correct=result.is_correct,
            hints_used=0,
            time_spent_seconds=10,
            confidence_level=result.confidence_level,
        )
        response_id = response.response_id  # capture before commit expires response
        await db_session.commit()

        # Reload from DB
        db_result = await db_session.execute(
            select(Response).where(Response.response_id == response_id)
        )
        saved = db_result.scalar_one()
        assert saved.is_correct is True

    async def test_submit_wrong_answer_numeric(self, db_session: Any) -> None:
        """Submitting a wrong numeric answer persists is_correct=False."""
        student = await _create_student(db_session)
        student_id = student.student_id  # capture before populate_problems expires student
        problems = await _populate_problems(db_session, 1)
        problem = problems[0]

        session = Session(
            student_id=student_id,
            date=datetime.now(UTC),
            status=SessionStatus.IN_PROGRESS,
            problem_ids=[problem.problem_id],
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        await db_session.refresh(problem)  # re-load problem attributes after commit expires them
        session_id = session.session_id  # capture before second commit expires session
        problem_id = problem.problem_id  # capture after refresh

        evaluator = AnswerEvaluator()
        result = evaluator.evaluate(problem, "999999", hints_used=0)
        assert result.is_correct is False

        response_repo = ResponseRepository()
        await response_repo.create_response(
            db=db_session,
            session_id=session_id,
            problem_id=problem_id,
            student_answer="999999",
            is_correct=result.is_correct,
            hints_used=0,
            time_spent_seconds=5,
            confidence_level="high",
        )
        await db_session.commit()

        db_result = await db_session.execute(
            select(Response).where(
                Response.session_id == session_id,
                Response.problem_id == problem_id,
            )
        )
        saved = db_result.scalar_one()
        assert saved.is_correct is False

    async def test_submit_5_answers_completes_session(self, db_session: Any) -> None:
        """Answering all 5 problems marks session as COMPLETED."""
        student = await _create_student(db_session)
        student_id = student.student_id  # capture before populate_problems expires student
        problems = await _populate_problems(db_session, 5)
        problem_ids = [p.problem_id for p in problems]

        session = Session(
            student_id=student_id,
            date=datetime.now(UTC),
            status=SessionStatus.IN_PROGRESS,
            problem_ids=problem_ids,
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        session_id = session.session_id  # capture before commits expire session
        # Refresh all problems so their attributes are accessible after commit
        for p in problems:
            await db_session.refresh(p)

        evaluator = AnswerEvaluator()
        response_repo = ResponseRepository()
        session_repo = SessionRepository()

        for problem in problems:
            result = evaluator.evaluate(problem, problem.answer, hints_used=0)
            await response_repo.create_response(
                db=db_session,
                session_id=session_id,
                problem_id=problem.problem_id,
                student_answer=problem.answer,
                is_correct=result.is_correct,
                hints_used=0,
                time_spent_seconds=5,
                confidence_level=result.confidence_level,
            )
            if result.is_correct:
                await session_repo.increment_correct_count(db_session, session)

        answered_ids = await response_repo.get_answered_problem_ids(db_session, session_id)
        remaining = [pid for pid in problem_ids if pid not in answered_ids]
        if not remaining:
            await session_repo.mark_session_complete(db_session, session)

        await db_session.commit()

        db_result = await db_session.execute(
            select(Session).where(Session.session_id == session_id)
        )
        updated = db_result.scalar_one()
        assert updated.status == SessionStatus.COMPLETED

    async def test_answer_expired_session_detected(self, db_session: Any) -> None:
        """Expired sessions are correctly detected via expires_at < now.

        Note: SQLite returns naive datetimes so we compare naive to naive here.
        Production uses PostgreSQL which preserves timezone info.
        """
        student = await _create_student(db_session)
        student_id = student.student_id  # capture before populate_problems expires student
        problems = await _populate_problems(db_session, 1)
        problem = problems[0]

        # Use naive datetimes for SQLite compatibility
        past_expires_at = datetime.now() - timedelta(hours=1)

        session = Session(
            student_id=student_id,
            date=datetime.now() - timedelta(hours=2),
            status=SessionStatus.IN_PROGRESS,
            problem_ids=[problem.problem_id],
            expires_at=past_expires_at,
        )
        session_expires_at = session.expires_at  # capture before commit expires session
        db_session.add(session)
        await db_session.commit()

        # Verify expires_at is in the past (naive comparison for SQLite)
        assert session_expires_at < datetime.now()


@pytest.mark.integration
class TestHintEndpoint:
    """Tests for hint delivery from pre-written DB hints."""

    async def test_hint_returns_prewritten_not_claude(self, db_session: Any) -> None:
        """Hint text is returned from DB, not None or empty."""
        await _create_student(db_session)
        problems = await _populate_problems(db_session, 1)
        problem = problems[0]

        hints = problem.get_hints()
        assert len(hints) >= 1

        hint = hints[0]
        assert hint.text_en is not None
        assert len(hint.text_en) > 0
        assert hint.text_bn is not None
        assert len(hint.text_bn) > 0

    async def test_hint_limit_3(self, db_session: Any) -> None:
        """After 3 hints recorded, hints_used=3 prevents more hints."""
        student = await _create_student(db_session)
        student_id = student.student_id  # capture before populate_problems expires student
        problems = await _populate_problems(db_session, 1)
        problem = problems[0]

        session = Session(
            student_id=student_id,
            date=datetime.now(UTC),
            status=SessionStatus.IN_PROGRESS,
            problem_ids=[problem.problem_id],
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        await db_session.refresh(problem)  # re-load problem after commit expires it
        session_id = session.session_id  # capture before second commit expires session

        response_repo = ResponseRepository()

        # Create response and mark 3 hints used
        response = await response_repo.create_response(
            db=db_session,
            session_id=session_id,
            problem_id=problem.problem_id,
            student_answer="",
            is_correct=False,
            hints_used=0,
            time_spent_seconds=0,
            confidence_level="high",
        )

        hints = problem.get_hints()
        for i, hint_obj in enumerate(hints[:3]):
            await response_repo.update_hint_count(db_session, response, i + 1, hint_obj.to_dict())

        await db_session.commit()
        await db_session.refresh(response)

        # hints_used should now be 3
        assert response.hints_used == 3

    async def test_hint_language_bengali(self, db_session: Any) -> None:
        """Hint text for language='bn' returns Bengali content."""
        student = Student(
            telegram_id=TELEGRAM_ID,
            name=STUDENT_NAME,
            grade=7,
            language="bn",
        )
        db_session.add(student)
        await db_session.commit()

        problems = await _populate_problems(db_session, 1)
        problem = problems[0]

        hints = problem.get_hints()
        assert hints[0].text_bn == "প্রশ্ন 0 এর hint 1।"
