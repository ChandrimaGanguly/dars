"""Student profile schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class StudentProfile(BaseModel):
    """Student profile with learning progress."""

    student_id: int = Field(..., description="Internal student ID")
    telegram_id: int = Field(..., description="Telegram user ID")
    name: str = Field(..., description="Student name", max_length=100)
    grade: int = Field(..., description="Grade level (6, 7, or 8)", ge=6, le=8)
    language: str = Field(..., description="Preferred language", examples=["bn", "en"])
    current_streak: int = Field(..., description="Current practice streak in days", ge=0)
    longest_streak: int = Field(..., description="Longest streak achieved", ge=0)
    avg_accuracy: float = Field(..., description="Average accuracy percentage", ge=0.0, le=100.0)
    last_practice: datetime | None = Field(None, description="Last practice session date")
    created_at: datetime = Field(..., description="Account creation date")
    updated_at: datetime | None = Field(None, description="Last profile update")


class ProfileUpdateRequest(BaseModel):
    """Request to update student preferences."""

    language: str | None = Field(None, description="Preferred language", examples=["bn", "en"])
    grade: int | None = Field(None, description="Grade level", ge=6, le=8)
