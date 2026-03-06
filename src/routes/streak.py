"""Streak tracking endpoint.

Implements REQ-009 (streak tracking) and REQ-010 (streak display).
Returns real streak data from the database for the authenticated student.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.student import verify_student
from src.database import get_session
from src.models.student import Student
from src.repositories.streak_repository import StreakRepository
from src.schemas.streak import StreakData

router = APIRouter()


async def _get_student_by_telegram_id(db: AsyncSession, telegram_id: int) -> Student:
    """Fetch Student row by telegram_id.

    Args:
        db: Async database session.
        telegram_id: The telegram ID returned by verify_student.

    Returns:
        Student instance.

    Raises:
        HTTPException: 404 if not found.
    """
    result = await db.execute(select(Student).where(Student.telegram_id == telegram_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.get("/streak", response_model=StreakData, tags=["Student Engagement"])
async def get_streak(
    student_id: int = Depends(verify_student),
    db: AsyncSession = Depends(get_session),
) -> StreakData:
    """Get student's streak information.

    Returns current streak, longest streak, milestones achieved, and the
    dates of practice sessions in the last 7 calendar days.

    Args:
        student_id: Verified student telegram ID (from dependency).
        db: Database session (from dependency).

    Returns:
        StreakData with real streak information from the database.

    Raises:
        HTTPException: 404 if student not found.
    """
    student = await _get_student_by_telegram_id(db, student_id)

    streak_repo = StreakRepository()
    streak = await streak_repo.get_or_create(db, student.student_id)

    # Normalise last_practice_date: Streak stores date | datetime | None
    last_practice: datetime
    if streak.last_practice_date is None:
        last_practice = datetime.now(UTC)
    elif isinstance(streak.last_practice_date, datetime):
        last_practice = streak.last_practice_date
    else:
        # Plain date → make it midnight UTC datetime
        last_practice = datetime(
            streak.last_practice_date.year,
            streak.last_practice_date.month,
            streak.last_practice_date.day,
            tzinfo=UTC,
        )

    return StreakData(
        student_id=student.student_id,
        current_streak=streak.current_streak,
        longest_streak=streak.longest_streak,
        last_practice_date=last_practice,
        milestones_achieved=list(streak.milestones_achieved or []),
        updated_at=datetime.now(UTC),
    )
