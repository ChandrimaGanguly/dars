"""Admin dashboard schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.schemas.student import StudentProfile


class AdminStats(BaseModel):
    """System statistics for admin dashboard."""

    total_students: int = Field(..., description="Total number of students", examples=[50])
    active_this_week: int = Field(..., description="Students active this week", examples=[42])
    active_this_week_percent: float | None = Field(
        None, description="Percentage of students active", examples=[84.0]
    )
    avg_streak: float = Field(..., description="Average streak length", examples=[7.2])
    avg_problems_per_session: float = Field(
        ..., description="Average problems per session", examples=[4.8]
    )
    total_sessions: int = Field(..., description="Total practice sessions", examples=[342])
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Report timestamp")


class StudentListResponse(BaseModel):
    """Paginated list of students."""

    students: list[StudentProfile] = Field(..., description="List of student profiles")
    total: int = Field(..., description="Total number of students")
    page: int = Field(..., description="Current page number", ge=1)
    limit: int = Field(..., description="Items per page", ge=1, le=100)


class CostSummary(BaseModel):
    """Cost tracking summary."""

    period: str = Field(..., description="Time period", examples=["day", "week", "month"])
    total_cost: float = Field(..., description="Total cost in USD", examples=[1.23])
    daily_average: float = Field(..., description="Daily average cost in USD", examples=[0.18])
    projected_monthly: float = Field(
        ..., description="Projected monthly cost in USD", examples=[7.80]
    )
    per_student_cost: float = Field(
        ..., description="Average cost per student in USD", examples=[0.16]
    )
    claude_cost: float | None = Field(None, description="AI API costs in USD", examples=[1.10])
    infrastructure_cost: float | None = Field(
        None, description="Server/DB costs in USD", examples=[0.13]
    )
    alert: bool = Field(..., description="True if over budget")
    alert_message: str | None = Field(None, description="Alert message if over budget")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Report timestamp")
