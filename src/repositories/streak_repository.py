"""
StreakRepository — data access layer for the streaks table.

Implements REQ-009 (Streak Tracking), REQ-010 (Streak Display),
and REQ-012 (Streak Milestones).

All methods accept an AsyncSession provided by the caller; transaction
management (commit/rollback) is the caller's responsibility. Methods
use flush() not commit() so callers control transaction boundaries.
"""

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.session import Session, SessionStatus
from src.models.streak import Streak

# Milestone thresholds (days).  REQ-012.
STREAK_MILESTONES: list[int] = [7, 14, 30]


def _to_date(value: date | datetime | None) -> date | None:
    """Normalise a value that may be a date or datetime into a plain date.

    SQLAlchemy's Date column returns datetime.date objects from PostgreSQL
    but the Streak model annotation is Mapped[datetime | None] for
    compatibility with legacy SQLite behaviour in tests.  This helper
    converts either type so streak arithmetic is always done on dates.

    Args:
        value: A date, datetime, or None.

    Returns:
        A datetime.date, or None.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    return value


class StreakRepository:
    """Data access methods for the streaks table.

    Example::

        repo = StreakRepository()
        streak, new_milestones = await repo.record_practice(db, student_id=1, practice_date=date.today())
    """

    async def get_for_student(
        self,
        db: AsyncSession,
        student_id: int,
    ) -> Streak | None:
        """Retrieve the streak row for a student.

        Args:
            db: Active async database session.
            student_id: Student primary key.

        Returns:
            Streak object if it exists, None otherwise.
        """
        stmt = select(Streak).where(Streak.student_id == student_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        db: AsyncSession,
        student_id: int,
    ) -> Streak:
        """Fetch the streak row for a student, creating it if it doesn't exist.

        New streaks start with current_streak=0, longest_streak=0 and
        last_practice_date=None. The new row is flushed (not committed)
        so the caller sees the generated primary key immediately.

        Args:
            db: Active async database session.
            student_id: Student primary key.

        Returns:
            Existing or newly created Streak object.
        """
        existing = await self.get_for_student(db, student_id)
        if existing is not None:
            return existing

        streak = Streak(
            student_id=student_id,
            current_streak=0,
            longest_streak=0,
            milestones_achieved=[],
        )
        db.add(streak)
        await db.flush()
        return streak

    async def record_practice(
        self,
        db: AsyncSession,
        student_id: int,
        practice_date: date,
    ) -> tuple[Streak, list[int]]:
        """Record a practice event and update streak counters.

        Business rules (REQ-009):
        - Same day as last_practice_date → no-op (idempotent).
        - Exactly 1 day after last_practice_date → consecutive; increment.
        - More than 1 day after last_practice_date → gap; reset to 1.
        - No previous practice → start streak at 1.

        Milestones (REQ-012): milestones [7, 14, 30] are detected and
        added to milestones_achieved only once (not re-fired on re-runs).

        Uses flush() so the caller decides when to commit.

        Args:
            db: Active async database session.
            student_id: Student primary key.
            practice_date: UTC calendar date of the practice session.

        Returns:
            Tuple of (updated Streak, list of newly achieved milestone ints).
            The milestone list is empty when no new milestones were hit.
        """
        streak = await self.get_or_create(db, student_id)
        last_date = _to_date(streak.last_practice_date)

        # --- Idempotency: same calendar day → no-op ---
        if last_date is not None and practice_date == last_date:
            return streak, []

        # --- Update current streak ---
        if last_date is None:
            # First practice ever
            streak.current_streak = 1
        elif practice_date == last_date + timedelta(days=1):
            # Consecutive day
            streak.current_streak += 1
        else:
            # Missed at least one day — reset
            streak.current_streak = 1

        # --- Update longest streak ---
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak

        # --- Update last practice date ---
        streak.last_practice_date = practice_date  # type: ignore[assignment]

        # --- Detect new milestones ---
        # Build a new list to replace the JSON column (in-place mutation is not
        # tracked by SQLAlchemy's change-detection for JSON columns).
        new_milestones: list[int] = []
        current_achieved: list[int] = list(streak.milestones_achieved or [])
        for milestone in STREAK_MILESTONES:
            if streak.current_streak >= milestone and milestone not in current_achieved:
                current_achieved.append(milestone)
                new_milestones.append(milestone)
        if new_milestones:
            streak.milestones_achieved = sorted(current_achieved)

        db.add(streak)
        await db.flush()
        return streak, new_milestones

    async def get_last_7_days(
        self,
        db: AsyncSession,
        student_id: int,
    ) -> list[date]:
        """Return the calendar dates (UTC) in the last 7 days when the student practiced.

        Queries completed sessions to determine practice days.  Used by the
        /streak endpoint to render a 7-day calendar view (REQ-010).

        Args:
            db: Active async database session.
            student_id: Student primary key.

        Returns:
            Sorted list of date objects (UTC) when student had a completed
            session in the last 7 calendar days (today inclusive).
            May be empty; at most 7 elements.
        """
        today_utc = datetime.now(UTC).date()
        seven_days_ago = today_utc - timedelta(days=6)  # 7-day window inclusive

        window_start = datetime(
            seven_days_ago.year,
            seven_days_ago.month,
            seven_days_ago.day,
            tzinfo=UTC,
        )

        stmt = (
            select(Session.completed_at)
            .where(
                Session.student_id == student_id,
                Session.status == SessionStatus.COMPLETED,
                Session.completed_at >= window_start,
            )
            .order_by(Session.completed_at)
        )
        result = await db.execute(stmt)
        rows = result.scalars().all()

        # Deduplicate by calendar date (UTC)
        seen: set[date] = set()
        practice_dates: list[date] = []
        for completed_at in rows:
            if completed_at is None:
                continue
            d = completed_at.date() if isinstance(completed_at, datetime) else completed_at
            if d not in seen:
                seen.add(d)
                practice_dates.append(d)

        return sorted(practice_dates)
