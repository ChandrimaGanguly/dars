"""Streak tracking endpoint."""

from datetime import UTC, datetime

from fastapi import APIRouter, Header

from src.schemas.streak import StreakData

router = APIRouter()


@router.get("/streak", response_model=StreakData, tags=["Student Engagement"])
async def get_streak(
    x_student_id: str = Header(..., description="Student telegram ID")
) -> StreakData:
    """Get student's streak information.

    Returns current streak, longest streak, and milestone achievements.

    Args:
        x_student_id: Student telegram ID from header.

    Returns:
        StreakData with streak information.

    Raises:
        HTTPException: If student not found.
    """
    # TODO: Implement streak retrieval
    # - Validate student exists
    # - Fetch streak data from database
    # - Calculate streak status (active/at-risk)
    # - Return formatted data

    # Mock data
    return StreakData(
        student_id=1,
        current_streak=12,
        longest_streak=28,
        last_practice_date=datetime.now(UTC),
        milestones_achieved=[7, 14],
        updated_at=datetime.now(UTC),
    )
