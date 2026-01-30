"""Admin dashboard endpoints."""

from datetime import datetime

from fastapi import APIRouter, Header, Query

from src.schemas.admin import AdminStats, CostSummary, StudentListResponse
from src.schemas.student import StudentProfile

router = APIRouter()


@router.get("/admin/stats", response_model=AdminStats, tags=["Admin"])
async def get_admin_stats(
    x_admin_id: str = Header(..., description="Admin telegram ID")
) -> AdminStats:
    """Get system statistics.

    Returns overall platform metrics including students, engagement, and usage.

    Args:
        x_admin_id: Admin telegram ID from header.

    Returns:
        AdminStats with system metrics.

    Raises:
        HTTPException: If not authorized or data unavailable.
    """
    # TODO: Implement admin authentication
    # - Validate admin ID (hardcoded list for Phase 0)
    # - Query database for statistics
    # - Calculate aggregations

    # Mock data
    return AdminStats(
        total_students=50,
        active_this_week=42,
        active_this_week_percent=84.0,
        avg_streak=7.2,
        avg_problems_per_session=4.8,
        total_sessions=342,
        timestamp=datetime.utcnow(),
    )


@router.get("/admin/students", response_model=StudentListResponse, tags=["Admin"])
async def get_admin_students(
    grade: int | None = Query(None, description="Filter by grade", ge=6, le=8),
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(20, description="Items per page", ge=1, le=100),
    x_admin_id: str = Header(..., description="Admin telegram ID"),
) -> StudentListResponse:
    """List all students with pagination.

    Returns paginated list of students with optional grade filtering.

    Args:
        grade: Optional grade filter (6, 7, or 8).
        page: Page number for pagination.
        limit: Number of items per page.
        x_admin_id: Admin telegram ID from header.

    Returns:
        StudentListResponse with paginated student list.

    Raises:
        HTTPException: If not authorized.
    """
    # TODO: Implement student list
    # - Validate admin authentication
    # - Apply grade filter if provided
    # - Paginate results
    # - Return student profiles

    # Mock data
    mock_student = StudentProfile(
        student_id=1,
        telegram_id=987654321,
        name="Rajesh",
        grade=grade if grade else 7,
        language="bn",
        current_streak=12,
        longest_streak=28,
        avg_accuracy=72.5,
        last_practice=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    return StudentListResponse(
        students=[mock_student],
        total=50,
        page=page,
        limit=limit,
    )


@router.get("/admin/cost", response_model=CostSummary, tags=["Admin"])
async def get_admin_cost(
    period: str = Query("week", description="Time period", regex="^(day|week|month)$"),
    x_admin_id: str = Header(..., description="Admin telegram ID"),
) -> CostSummary:
    """Get cost summary.

    Returns cost metrics for AI API usage and infrastructure.
    Includes budget alerts if projected costs exceed limits.

    Args:
        period: Time period for cost calculation (day, week, month).
        x_admin_id: Admin telegram ID from header.

    Returns:
        CostSummary with cost breakdown and alerts.

    Raises:
        HTTPException: If not authorized.
    """
    # TODO: Implement cost tracking
    # - Validate admin authentication
    # - Query cost records from database
    # - Calculate aggregations by period
    # - Check against budget thresholds
    # - Generate alerts if over budget

    # Mock data showing over-budget scenario
    per_student = 0.16
    alert = per_student > 0.15

    return CostSummary(
        period=period,
        total_cost=1.23,
        daily_average=0.18,
        projected_monthly=7.80,
        per_student_cost=per_student,
        claude_cost=1.10,
        infrastructure_cost=0.13,
        alert=alert,
        alert_message="Over budget - exceeds $0.15/student/month" if alert else None,
        timestamp=datetime.utcnow(),
    )
