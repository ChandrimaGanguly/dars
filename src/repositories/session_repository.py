"""
SessionRepository — data access layer for the sessions table.

Provides CRUD operations and business-logic queries for practice sessions.
All methods accept an AsyncSession provided by the caller; transaction
management (commit/rollback) is the caller's responsibility.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.engine.cursor import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.session import Session, SessionStatus

# Default session expiry window.
_SESSION_EXPIRY_MINUTES = 30


class SessionRepository:
    """Data access methods for the sessions table.

    Example:
        repo = SessionRepository()
        session = await repo.create_session(db, student_id=1, problem_ids=[1, 2, 3, 4, 5])
    """

    async def create_session(
        self,
        db: AsyncSession,
        student_id: int,
        problem_ids: list[int],
    ) -> Session:
        """Create a new practice session and flush it (without commit).

        The session expires 30 minutes from creation. Uses flush() so the
        caller can inspect the generated session_id before committing.

        Args:
            db: Active async database session.
            student_id: Student who owns this session.
            problem_ids: Ordered list of problem IDs for the session (usually 5).

        Returns:
            Newly created Session object with session_id populated after flush.
        """
        now = datetime.now(UTC)
        session = Session(
            student_id=student_id,
            date=now,
            status=SessionStatus.IN_PROGRESS,
            problem_ids=problem_ids,
            expires_at=now + timedelta(minutes=_SESSION_EXPIRY_MINUTES),
            total_time_seconds=0,
            problems_correct=0,
        )
        db.add(session)
        await db.flush()
        return session

    async def get_active_session_for_today(
        self,
        db: AsyncSession,
        student_id: int,
    ) -> Session | None:
        """Return the student's session for today (IN_PROGRESS or COMPLETED).

        Returns the most recent session created today (UTC) in either
        IN_PROGRESS or COMPLETED status. Callers check the status to decide
        how to proceed (e.g. resume an in-progress session, or short-circuit
        for a completed one).

        Args:
            db: Active async database session.
            student_id: Student to look up.

        Returns:
            Session object if one exists for today, None otherwise.
        """
        today_start = datetime.now(UTC).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        stmt = (
            select(Session)
            .where(
                Session.student_id == student_id,
                Session.status.in_([SessionStatus.IN_PROGRESS, SessionStatus.COMPLETED]),
                Session.created_at >= today_start,
            )
            .order_by(Session.created_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_session_by_id(
        self,
        db: AsyncSession,
        session_id: int,
    ) -> Session | None:
        """Retrieve a single session by primary key.

        Args:
            db: Active async database session.
            session_id: Primary key of the session.

        Returns:
            Session object if found, None otherwise.
        """
        stmt = select(Session).where(Session.session_id == session_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_session_complete(
        self,
        db: AsyncSession,
        session: Session,
    ) -> Session:
        """Mark a session as completed and record the completion timestamp.

        Flushes the change so the caller can see updated state before commit.

        Args:
            db: Active async database session.
            session: Session object to update.

        Returns:
            Updated Session object.
        """
        session.status = SessionStatus.COMPLETED
        session.completed_at = datetime.now(UTC)
        db.add(session)
        await db.flush()
        return session

    async def increment_correct_count(
        self,
        db: AsyncSession,
        session: Session,
    ) -> Session:
        """Increment problems_correct counter by 1.

        Flushes the change without committing.

        Args:
            db: Active async database session.
            session: Session object to update.

        Returns:
            Updated Session object.
        """
        session.problems_correct += 1
        db.add(session)
        await db.flush()
        return session

    async def expire_stale_sessions(
        self,
        db: AsyncSession,
    ) -> int:
        """Mark all in_progress sessions past their expiry as abandoned.

        Intended to be called at the start of each new /practice request so
        stale sessions from previous days/hours are cleaned up.

        Args:
            db: Active async database session.

        Returns:
            Number of sessions that were marked abandoned.
        """
        now = datetime.now(UTC)
        stmt = (
            update(Session)
            .where(
                Session.status == SessionStatus.IN_PROGRESS,
                Session.expires_at < now,
            )
            .values(status=SessionStatus.ABANDONED)
            .execution_options(synchronize_session="fetch")
        )
        cursor: CursorResult[tuple[int]] = await db.execute(stmt)  # type: ignore[assignment]
        await db.flush()
        return int(cursor.rowcount)

    async def get_completed_sessions_for_student(
        self,
        db: AsyncSession,
        student_id: int,
        limit: int = 10,
    ) -> list[Session]:
        """Retrieve the most recently completed sessions for a student.

        Args:
            db: Active async database session.
            student_id: Student to query.
            limit: Maximum number of sessions to return (default 10).

        Returns:
            List of completed Session objects ordered by completion time descending.
        """
        stmt = (
            select(Session)
            .where(
                Session.student_id == student_id,
                Session.status == SessionStatus.COMPLETED,
            )
            .order_by(Session.completed_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
