"""
ResponseRepository — data access layer for the responses table.

Provides CRUD operations and aggregation queries for student answer
submissions. All methods accept an AsyncSession from the caller; transaction
management (commit/rollback) is the caller's responsibility.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.problem import Problem
from src.models.response import ConfidenceLevel, Response
from src.models.session import Session


def _confidence_from_hints(hints_used: int) -> str:
    """Derive a confidence level string based on how many hints were used.

    Args:
        hints_used: Number of hints requested during problem solving (0-3).

    Returns:
        One of 'high', 'medium', 'low' as a string constant.
    """
    if hints_used == 0:
        return ConfidenceLevel.HIGH
    if hints_used == 1:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


class ResponseRepository:
    """Data access methods for the responses table.

    Example:
        repo = ResponseRepository()
        response = await repo.create_response(
            db, session_id=1, problem_id=5, student_answer="20",
            is_correct=True, hints_used=0, time_spent_seconds=45,
            confidence_level="high",
        )
    """

    async def create_response(
        self,
        db: AsyncSession,
        session_id: int,
        problem_id: int,
        student_answer: str,
        is_correct: bool,
        hints_used: int,
        time_spent_seconds: int,
        confidence_level: str | None = None,
    ) -> Response:
        """Record a student's answer submission.

        If confidence_level is not provided it is derived automatically from
        hints_used (0 hints -> high, 1 hint -> medium, 2+ hints -> low).

        Flushes the new row so the caller can read the generated response_id
        before the transaction is committed.

        Args:
            db: Active async database session.
            session_id: Session this response belongs to.
            problem_id: Problem being answered.
            student_answer: Student's submitted answer string.
            is_correct: Whether the answer was evaluated as correct.
            hints_used: Number of hints the student requested (0-3).
            time_spent_seconds: Time spent on this problem in seconds.
            confidence_level: Optional override; derived from hints_used if None.

        Returns:
            Newly created and flushed Response object.
        """
        if confidence_level is None:
            confidence_level = _confidence_from_hints(hints_used)

        response = Response(
            session_id=session_id,
            problem_id=problem_id,
            student_answer=student_answer,
            is_correct=is_correct,
            hints_used=hints_used,
            time_spent_seconds=time_spent_seconds,
            evaluated_at=datetime.now(UTC),
            confidence_level=confidence_level,
            hints_viewed=[],
        )
        db.add(response)
        await db.flush()
        return response

    async def get_response_for_problem(
        self,
        db: AsyncSession,
        session_id: int,
        problem_id: int,
    ) -> Response | None:
        """Get the response for a specific problem within a session.

        Args:
            db: Active async database session.
            session_id: Session to look in.
            problem_id: Problem to look for.

        Returns:
            Response object if found, None otherwise.
        """
        stmt = select(Response).where(
            Response.session_id == session_id,
            Response.problem_id == problem_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_topic_accuracy_for_student(
        self,
        db: AsyncSession,
        student_id: int,
        topic: str,
        days: int = 30,
    ) -> float:
        """Calculate a student's accuracy for a specific topic over the last N days.

        Accuracy = correct_responses / total_responses for the topic.
        Returns 0.5 (neutral baseline) if the student has no data for the topic.

        Args:
            db: Active async database session.
            student_id: Student to compute accuracy for.
            topic: Topic string (must match Problem.topic exactly).
            days: Look-back window in days (default 30).

        Returns:
            Accuracy as a float in [0.0, 1.0].
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)

        # Get sessions for this student within the window.
        session_stmt = select(Session.session_id).where(
            Session.student_id == student_id,
            Session.created_at >= cutoff,
        )
        session_result = await db.execute(session_stmt)
        session_ids = [row[0] for row in session_result.fetchall()]

        if not session_ids:
            return 0.5  # Neutral baseline — no history.

        # Get problem IDs for the topic.
        problem_stmt = select(Problem.problem_id).where(Problem.topic == topic)
        problem_result = await db.execute(problem_stmt)
        topic_problem_ids = [row[0] for row in problem_result.fetchall()]

        if not topic_problem_ids:
            return 0.5  # Topic not in DB — neutral.

        # Count total and correct responses for this student on the topic.
        total_stmt = (
            select(func.count())
            .select_from(Response)
            .where(
                Response.session_id.in_(session_ids),
                Response.problem_id.in_(topic_problem_ids),
            )
        )
        total_result = await db.execute(total_stmt)
        total = total_result.scalar_one()

        if total == 0:
            return 0.5

        correct_stmt = (
            select(func.count())
            .select_from(Response)
            .where(
                Response.session_id.in_(session_ids),
                Response.problem_id.in_(topic_problem_ids),
                Response.is_correct.is_(True),
            )
        )
        correct_result = await db.execute(correct_stmt)
        correct = correct_result.scalar_one()

        return correct / total

    async def get_all_topic_accuracies(
        self,
        db: AsyncSession,
        student_id: int,
        days: int = 30,
    ) -> dict[str, float]:
        """Compute accuracy for every topic a student has attempted.

        Returns a dict mapping topic -> accuracy (float in [0.0, 1.0]).
        Topics the student has never attempted are not included.

        Args:
            db: Active async database session.
            student_id: Student to compute accuracies for.
            days: Look-back window in days (default 30).

        Returns:
            Dict of topic -> accuracy floats.
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)

        # Get recent sessions for this student.
        session_stmt = select(Session.session_id).where(
            Session.student_id == student_id,
            Session.created_at >= cutoff,
        )
        session_result = await db.execute(session_stmt)
        session_ids = [row[0] for row in session_result.fetchall()]

        if not session_ids:
            return {}

        # Join responses -> problems to group by topic.
        stmt = (
            select(
                Problem.topic,
                func.count(Response.response_id).label("total"),
                func.sum(func.cast(Response.is_correct, type_=func.count().type)).label("correct"),
            )
            .join(Problem, Response.problem_id == Problem.problem_id)
            .where(Response.session_id.in_(session_ids))
            .group_by(Problem.topic)
        )
        result = await db.execute(stmt)
        rows = result.fetchall()

        accuracies: dict[str, float] = {}
        for row in rows:
            topic, total, correct = row
            if total and total > 0:
                accuracies[topic] = (correct or 0) / total
        return accuracies

    async def update_hint_count(
        self,
        db: AsyncSession,
        response: Response,
        new_hints_used: int,
        hint_viewed: dict[str, Any],
    ) -> Response:
        """Update the hint usage count and append a viewed hint to the response.

        Flushes but does not commit.

        Args:
            db: Active async database session.
            response: Response object to update.
            new_hints_used: Updated count of hints used (must be > current count).
            hint_viewed: Hint dict (with hint_number, text_en, text_bn keys) to append.

        Returns:
            Updated Response object.
        """
        response.hints_used = new_hints_used
        # Append to the existing hints_viewed JSON array.
        current_viewed: list[dict[str, Any]] = list(response.hints_viewed or [])
        current_viewed.append(hint_viewed)
        response.hints_viewed = current_viewed
        db.add(response)
        await db.flush()
        return response
