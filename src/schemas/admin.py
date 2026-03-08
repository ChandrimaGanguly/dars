"""Admin dashboard schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class AdminStats(BaseModel):
    """System statistics for admin dashboard."""

    total_students: int = Field(..., description="Total number of students", examples=[50])
    active_this_week: int = Field(..., description="Students active this week", examples=[42])
    active_this_week_percent: float | None = Field(
        None, description="Percentage of students active this week", examples=[84.0]
    )
    avg_streak: float = Field(..., description="Average current streak length", examples=[7.2])
    sessions_this_week: int = Field(..., description="Sessions completed this week", examples=[42])
    week_cost_usd: float = Field(..., description="Week-to-date AI cost in USD", examples=[0.08])
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Report timestamp")


class StudentSummary(BaseModel):
    """Summary of a single student for admin list view."""

    student_id: int = Field(..., description="Student primary key")
    name: str = Field(..., description="Student display name")
    grade: int = Field(..., description="Grade level (6, 7, or 8)")
    language: str = Field(..., description="Language preference ('en' or 'bn')")
    current_streak: int = Field(..., description="Current consecutive practice days")
    longest_streak: int = Field(..., description="Longest streak ever achieved")
    last_practice_date: date | None = Field(None, description="Date of last practice session")
    total_sessions: int = Field(..., description="Total practice sessions completed")


class StudentListResponse(BaseModel):
    """Paginated list of students."""

    students: list[StudentSummary] = Field(..., description="List of student summaries")
    total: int = Field(..., description="Total number of students matching filter")
    page: int = Field(..., description="Current page number", ge=1)
    limit: int = Field(..., description="Items per page", ge=1, le=100)


class CostSummary(BaseModel):
    """Cost tracking summary for a given period."""

    period: str = Field(..., description="Time period", examples=["day", "week", "month"])
    total_cost_usd: float = Field(..., description="Total AI cost in USD", examples=[0.08])
    ai_hint_count: int = Field(
        ..., description="Hints served by Claude API (cost > $0)", examples=[42]
    )
    cache_hit_count: int = Field(
        ..., description="Hints served from pre-written cache (cost = $0)", examples=[120]
    )
    per_student_avg_usd: float = Field(
        ..., description="Avg cost per active student in period", examples=[0.002]
    )
    daily_avg_usd: float = Field(..., description="Daily average cost in USD", examples=[0.011])
    projected_monthly_usd: float = Field(
        ..., description="Projected monthly cost at current rate", examples=[0.34]
    )
    budget_alert: bool = Field(..., description="True if any student is projected > $0.10/month")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Report timestamp")
