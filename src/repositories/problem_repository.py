"""
ProblemRepository — data access layer for the problems table.

Provides all queries needed by the ProblemSelector service and other
downstream consumers. All methods accept an AsyncSession provided by the
caller so that transaction management stays at the service/route layer.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.problem import Problem
from src.models.response import Response
from src.models.session import Session


class ProblemRepository:
    """Data access methods for the problems table.

    All methods are async and require an active SQLAlchemy AsyncSession.
    Transaction commit/rollback is the caller's responsibility.

    Example:
        repo = ProblemRepository()
        problems = await repo.get_problems_by_grade(db, grade=7)
    """

    async def get_problems_by_grade(
        self,
        db: AsyncSession,
        grade: int,
        difficulty: int | None = None,
        topic: str | None = None,
        exclude_ids: list[int] | None = None,
    ) -> list[Problem]:
        """Retrieve problems for a given grade, with optional filters.

        Args:
            db: Active async database session.
            grade: Grade level to filter on (6, 7, or 8).
            difficulty: If provided, only return problems at this difficulty (1-3).
            topic: If provided, only return problems for this topic.
            exclude_ids: Problem IDs to exclude from results.

        Returns:
            List of matching Problem objects, ordered by problem_id.
        """
        stmt = select(Problem).where(Problem.grade == grade)

        if difficulty is not None:
            stmt = stmt.where(Problem.difficulty == difficulty)
        if topic is not None:
            stmt = stmt.where(Problem.topic == topic)
        if exclude_ids:
            stmt = stmt.where(Problem.problem_id.notin_(exclude_ids))

        stmt = stmt.order_by(Problem.problem_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_recently_seen_problem_ids(
        self,
        db: AsyncSession,
        student_id: int,
        days: int = 7,
    ) -> list[int]:
        """Get IDs of problems this student has seen in the last N days.

        Looks at all sessions belonging to the student within the window
        and returns the union of problem_ids from those sessions.

        Args:
            db: Active async database session.
            student_id: Student to query for.
            days: Look-back window in days (default 7).

        Returns:
            List of problem IDs seen by the student recently.
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)

        # Sub-query: get all sessions for this student in the window.
        session_stmt = select(Session.session_id).where(
            Session.student_id == student_id,
            Session.created_at >= cutoff,
        )
        session_result = await db.execute(session_stmt)
        session_ids = [row[0] for row in session_result.fetchall()]

        if not session_ids:
            return []

        # Get distinct problem_ids answered in those sessions via responses.
        resp_stmt = select(distinct(Response.problem_id)).where(
            Response.session_id.in_(session_ids)
        )
        resp_result = await db.execute(resp_stmt)
        return [row[0] for row in resp_result.fetchall()]

    async def get_problem_by_id(
        self,
        db: AsyncSession,
        problem_id: int,
    ) -> Problem | None:
        """Retrieve a single problem by primary key.

        Args:
            db: Active async database session.
            problem_id: Primary key of the problem.

        Returns:
            Problem object if found, None otherwise.
        """
        stmt = select(Problem).where(Problem.problem_id == problem_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_topics_for_grade(
        self,
        db: AsyncSession,
        grade: int,
    ) -> list[str]:
        """Get all distinct topics available for a given grade.

        Args:
            db: Active async database session.
            grade: Grade level to query topics for.

        Returns:
            Sorted list of distinct topic strings.
        """
        stmt = select(distinct(Problem.topic)).where(Problem.grade == grade).order_by(Problem.topic)
        result = await db.execute(stmt)
        return [row[0] for row in result.fetchall()]

    async def get_by_grade(
        self,
        db: AsyncSession,
        grade: int,
    ) -> list[Problem]:
        """Alias for get_problems_by_grade with no optional filters.

        Satisfies the ProblemRepository Protocol expected by ProblemSelector.

        Args:
            db: Active async database session.
            grade: Grade level (6, 7, or 8).

        Returns:
            List of all Problem objects for that grade, ordered by problem_id.
        """
        return await self.get_problems_by_grade(db, grade)

    async def get_problems_by_ids(
        self,
        db: AsyncSession,
        problem_ids: list[int],
    ) -> list[Problem]:
        """Retrieve multiple problems by their primary keys.

        Returns problems in the same order as problem_ids. Problems not found
        are silently omitted.

        Args:
            db: Active async database session.
            problem_ids: List of problem primary keys to fetch.

        Returns:
            List of Problem objects (may be shorter than problem_ids if some not found).
        """
        if not problem_ids:
            return []
        stmt = select(Problem).where(Problem.problem_id.in_(problem_ids))
        result = await db.execute(stmt)
        problems_by_id = {p.problem_id: p for p in result.scalars().all()}
        return [problems_by_id[pid] for pid in problem_ids if pid in problems_by_id]

    async def get_problem_count_by_grade(
        self,
        db: AsyncSession,
        grade: int,
    ) -> int:
        """Count total problems available for a grade.

        Args:
            db: Active async database session.
            grade: Grade level to count for.

        Returns:
            Integer count of problems for the grade.
        """
        stmt = select(func.count()).select_from(Problem).where(Problem.grade == grade)
        result = await db.execute(stmt)
        return result.scalar_one()
