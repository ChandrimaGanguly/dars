"""Admin dashboard endpoints.

Security (SEC-004):
- All admin endpoints require authentication via verify_admin dependency
- Returns 401 if X-Admin-ID header missing
- Returns 403 if admin ID not in authorized list
- Prevents unauthorized access to sensitive data
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query

from src.auth.admin import verify_admin
from src.logging import get_logger
from src.schemas.admin import AdminStats, CostSummary, StudentListResponse
from src.schemas.student import StudentProfile

router = APIRouter()
logger = get_logger(__name__)


@router.get("/admin/stats", response_model=AdminStats, tags=["Admin"])
async def get_admin_stats(
    admin_id: int = Depends(verify_admin),
) -> AdminStats:
    """Get system statistics.

    Returns overall platform metrics including students, engagement, and usage.

    Security (SEC-004):
    - Requires authentication via verify_admin dependency
    - Only authorized admin IDs can access this endpoint
    - Returns 403 if admin ID not in authorized list

    Args:
        admin_id: Authenticated admin telegram ID (injected by verify_admin).

    Returns:
        AdminStats with system metrics.

    Raises:
        HTTPException: If not authorized (403) or data unavailable (500).
    """
    logger.info(f"Admin {admin_id} requested system stats")

    # TODO: Implement statistics calculation
    # - Query database for student counts
    # - Calculate engagement metrics
    # - Calculate averages

    # Mock data
    return AdminStats(
        total_students=50,
        active_this_week=42,
        active_this_week_percent=84.0,
        avg_streak=7.2,
        avg_problems_per_session=4.8,
        total_sessions=342,
        timestamp=datetime.now(UTC),
    )


@router.get("/admin/students", response_model=StudentListResponse, tags=["Admin"])
async def get_admin_students(
    grade: int | None = Query(None, description="Filter by grade", ge=6, le=8),
    page: int = Query(1, description="Page number", ge=1, le=1000),  # SEC-008: Upper bound
    limit: int = Query(20, description="Items per page", ge=1, le=100),
    admin_id: int = Depends(verify_admin),
) -> StudentListResponse:
    """List all students with pagination.

    Returns paginated list of students with optional grade filtering.

    Security (SEC-004):
    - Requires authentication via verify_admin dependency
    - Prevents unauthorized access to student data
    - Returns 403 if admin ID not authorized

    Args:
        grade: Optional grade filter (6, 7, or 8).
        page: Page number for pagination.
        limit: Number of items per page.
        admin_id: Authenticated admin telegram ID (injected by verify_admin).

    Returns:
        StudentListResponse with paginated student list.

    Raises:
        HTTPException: If not authorized (403).
    """
    logger.info(f"Admin {admin_id} requested student list (grade={grade}, page={page})")

    # TODO: Implement student list
    # - Query database for students
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
        last_practice=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    return StudentListResponse(
        students=[mock_student],
        total=50,
        page=page,
        limit=limit,
    )


@router.get("/admin/cost", response_model=CostSummary, tags=["Admin"])
async def get_admin_cost(
    period: str = Query("week", description="Time period", pattern="^(day|week|month)$"),
    admin_id: int = Depends(verify_admin),
) -> CostSummary:
    """Get cost summary.

    Returns cost metrics for AI API usage and infrastructure.
    Includes budget alerts if projected costs exceed limits.

    Security (SEC-004):
    - Requires authentication via verify_admin dependency
    - Prevents unauthorized access to cost data
    - Returns 403 if admin ID not authorized

    Args:
        period: Time period for cost calculation (day, week, month).
        admin_id: Authenticated admin telegram ID (injected by verify_admin).

    Returns:
        CostSummary with cost breakdown and alerts.

    Raises:
        HTTPException: If not authorized (403).
    """
    logger.info(f"Admin {admin_id} requested cost summary (period={period})")

    # TODO: Implement cost tracking
    # - Query cost records from database
    # - Calculate aggregations by period
    # - Check against budget thresholds ($0.10/student/month)
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
        timestamp=datetime.now(UTC),
    )
