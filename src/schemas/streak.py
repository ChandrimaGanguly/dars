"""Streak tracking schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class StreakData(BaseModel):
    """Student's streak information."""

    student_id: int = Field(..., description="Student ID")
    current_streak: int = Field(..., description="Current streak in days", ge=0)
    longest_streak: int = Field(..., description="Longest streak achieved", ge=0)
    last_practice_date: datetime = Field(..., description="Last practice date")
    milestones_achieved: list[int] = Field(
        default_factory=list, description="Milestones achieved (e.g., [7, 14, 30])"
    )
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
