"""Admin dashboard endpoints.

Security (SEC-004):
- All admin endpoints require authentication via verify_admin dependency
- Returns 401 if X-Admin-ID header missing
- Returns 403 if admin ID not in authorized list
- Prevents unauthorized access to sensitive data
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.admin import verify_admin
from src.database import get_session
from src.logging import get_logger
from src.models.cost_record import CostRecord
from src.models.session import Session
from src.models.streak import Streak
from src.models.student import Student
from src.schemas.admin import AdminStats, CostSummary, StudentListResponse, StudentSummary
from src.services.cost_tracker import BUDGET_PER_STUDENT_USD

router = APIRouter()
logger = get_logger(__name__)


@router.get("/admin/stats", response_model=AdminStats, tags=["Admin"])
async def get_admin_stats(
    admin_id: int = Depends(verify_admin),
    db: AsyncSession = Depends(get_session),
) -> AdminStats:
    """Get system statistics.

    Returns real platform metrics: student count, weekly activity, average
    streak, session count, and week-to-date AI cost.

    Security (SEC-004):
    - Requires authentication via verify_admin dependency
    - Only authorized admin IDs can access this endpoint
    - Returns 403 if admin ID not in authorized list

    Args:
        admin_id: Authenticated admin telegram ID (injected by verify_admin).
        db: Async database session.

    Returns:
        AdminStats with real system metrics.
    """
    logger.info("Admin requested system stats", admin_id=admin_id)

    week_ago = datetime.now(UTC) - timedelta(days=7)

    total_students = await db.scalar(select(func.count(Student.student_id))) or 0

    active_week = (
        await db.scalar(
            select(func.count(func.distinct(Session.student_id))).where(
                Session.completed_at >= week_ago
            )
        )
        or 0
    )

    avg_streak_raw = await db.scalar(select(func.avg(Streak.current_streak)))
    avg_streak = round(float(avg_streak_raw), 1) if avg_streak_raw is not None else 0.0

    sessions_week = (
        await db.scalar(
            select(func.count(Session.session_id)).where(Session.completed_at >= week_ago)
        )
        or 0
    )

    week_cost_raw = await db.scalar(
        select(func.sum(CostRecord.cost_usd)).where(CostRecord.recorded_at >= week_ago)
    )
    week_cost = round(float(week_cost_raw), 4) if week_cost_raw is not None else 0.0

    active_this_week_percent = (
        round(active_week / total_students * 100, 1) if total_students > 0 else 0.0
    )

    return AdminStats(
        total_students=total_students,
        active_this_week=active_week,
        active_this_week_percent=active_this_week_percent,
        avg_streak=avg_streak,
        sessions_this_week=sessions_week,
        week_cost_usd=week_cost,
        timestamp=datetime.now(UTC),
    )


@router.get("/admin/students", response_model=StudentListResponse, tags=["Admin"])
async def get_admin_students(
    grade: int | None = Query(None, description="Filter by grade", ge=6, le=8),
    page: int = Query(1, description="Page number", ge=1, le=1000),
    limit: int = Query(20, description="Items per page", ge=1, le=100),
    admin_id: int = Depends(verify_admin),
    db: AsyncSession = Depends(get_session),
) -> StudentListResponse:
    """List all students with pagination and optional grade filter.

    Returns per-student: id, name, grade, language, current/longest streak,
    last practice date, and total session count.

    Security (SEC-004):
    - Requires authentication via verify_admin dependency
    - Prevents unauthorized access to student data
    - Returns 403 if admin ID not authorized

    Args:
        grade: Optional grade filter (6, 7, or 8).
        page: Page number for pagination.
        limit: Number of items per page.
        admin_id: Authenticated admin telegram ID (injected by verify_admin).
        db: Async database session.

    Returns:
        StudentListResponse with paginated student summaries.
    """
    logger.info(
        "Admin requested student list", admin_id=admin_id, grade=grade, page=page, limit=limit
    )

    # Count total matching students
    count_stmt = select(func.count(Student.student_id))
    if grade is not None:
        count_stmt = count_stmt.where(Student.grade == grade)
    total = await db.scalar(count_stmt) or 0

    # Left-join Student → Streak; paginate
    stmt = select(Student, Streak).outerjoin(Streak, Streak.student_id == Student.student_id)
    if grade is not None:
        stmt = stmt.where(Student.grade == grade)
    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit).order_by(Student.student_id)
    rows = (await db.execute(stmt)).all()

    summaries: list[StudentSummary] = []
    for student, streak in rows:
        session_count = (
            await db.scalar(
                select(func.count(Session.session_id)).where(
                    Session.student_id == student.student_id
                )
            )
            or 0
        )
        summaries.append(
            StudentSummary(
                student_id=student.student_id,
                name=student.name,
                grade=student.grade,
                language=student.language,
                current_streak=streak.current_streak if streak is not None else 0,
                longest_streak=streak.longest_streak if streak is not None else 0,
                last_practice_date=streak.last_practice_date if streak is not None else None,
                total_sessions=session_count,
            )
        )

    return StudentListResponse(
        students=summaries,
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/admin/cost", response_model=CostSummary, tags=["Admin"])
async def get_admin_cost(
    period: str = Query("week", description="Time period", pattern="^(day|week|month)$"),
    admin_id: int = Depends(verify_admin),
    db: AsyncSession = Depends(get_session),
) -> CostSummary:
    """Get cost summary.

    Returns aggregated AI cost metrics for the requested period with a budget
    alert flag if any student is projected to exceed $0.10/month.

    Security (SEC-004):
    - Requires authentication via verify_admin dependency
    - Prevents unauthorized access to cost data
    - Returns 403 if admin ID not authorized

    Args:
        period: Time period for cost calculation (day, week, month).
        admin_id: Authenticated admin telegram ID (injected by verify_admin).
        db: Async database session.

    Returns:
        CostSummary with real cost breakdown and budget alert flag.
    """
    logger.info("Admin requested cost summary", admin_id=admin_id, period=period)

    days = {"day": 1, "week": 7, "month": 30}[period]
    since = datetime.now(UTC) - timedelta(days=days)

    # Total cost in period
    total_cost_raw = await db.scalar(
        select(func.sum(CostRecord.cost_usd)).where(CostRecord.recorded_at >= since)
    )
    total_cost = round(float(total_cost_raw), 4) if total_cost_raw is not None else 0.0

    # AI hint count: cost_usd > 0 → real Claude call
    ai_hint_count = (
        await db.scalar(
            select(func.count(CostRecord.cost_id)).where(
                CostRecord.recorded_at >= since,
                CostRecord.cost_usd > 0,
            )
        )
        or 0
    )

    # Cache hit count: cost_usd = 0 → pre-written hint served for free
    cache_hit_count = (
        await db.scalar(
            select(func.count(CostRecord.cost_id)).where(
                CostRecord.recorded_at >= since,
                CostRecord.cost_usd == 0,
            )
        )
        or 0
    )

    # Active students in period (for per-student avg)
    active_students = (
        await db.scalar(
            select(func.count(func.distinct(CostRecord.student_id))).where(
                CostRecord.recorded_at >= since
            )
        )
        or 0
    )

    per_student_avg = round(total_cost / active_students, 4) if active_students > 0 else 0.0
    daily_avg = round(total_cost / days, 4)
    projected_monthly = round(daily_avg * 30, 4)
    # Project per-student cost to a full month and compare with budget ceiling
    budget_alert = (per_student_avg * (30 / days)) > BUDGET_PER_STUDENT_USD

    return CostSummary(
        period=period,
        total_cost_usd=total_cost,
        ai_hint_count=ai_hint_count,
        cache_hit_count=cache_hit_count,
        per_student_avg_usd=per_student_avg,
        daily_avg_usd=daily_avg,
        projected_monthly_usd=projected_monthly,
        budget_alert=budget_alert,
        timestamp=datetime.now(UTC),
    )
