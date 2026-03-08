"""Student profile endpoints."""

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.logging import get_logger
from src.models.response import Response
from src.models.session import Session
from src.models.student import Student
from src.repositories.streak_repository import StreakRepository
from src.schemas.student import ProfileUpdateRequest, StudentProfile

router = APIRouter()
logger = get_logger(__name__)


async def _build_profile(student: Student, db: AsyncSession) -> StudentProfile:
    """Build a StudentProfile from a Student ORM object.

    Queries avg_accuracy from Response rows and streak data from Streak.

    Args:
        student: Student ORM object (attributes must not be expired).
        db: Async database session.

    Returns:
        Populated StudentProfile schema.
    """
    session_subq = select(Session.session_id).where(Session.student_id == student.student_id)

    total = (
        await db.scalar(
            select(func.count(Response.response_id)).where(Response.session_id.in_(session_subq))
        )
        or 0
    )
    correct = (
        await db.scalar(
            select(func.count(Response.response_id)).where(
                Response.session_id.in_(session_subq),
                Response.is_correct == True,  # noqa: E712
            )
        )
        or 0
    )
    avg_accuracy = round(correct / total * 100, 1) if total > 0 else 0.0

    streak_repo = StreakRepository()
    streak = await streak_repo.get_for_student(db, student.student_id)

    return StudentProfile(
        student_id=student.student_id,
        telegram_id=student.telegram_id,
        name=student.name,
        grade=student.grade,
        language=student.language,
        current_streak=streak.current_streak if streak else 0,
        longest_streak=streak.longest_streak if streak else 0,
        avg_accuracy=avg_accuracy,
        last_practice=streak.last_practice_date if streak else None,
        created_at=student.created_at,
        updated_at=student.updated_at,
    )


@router.get("/student/profile", response_model=StudentProfile, tags=["Student"])
async def get_student_profile(
    x_student_id: str = Header(..., description="Student telegram ID"),
    db: AsyncSession = Depends(get_session),
) -> StudentProfile:
    """Get student's learning profile with real data from database.

    Args:
        x_student_id: Student telegram ID from header.
        db: Async database session.

    Returns:
        StudentProfile with accuracy and streak data.

    Raises:
        HTTPException: 400 if header is not numeric, 404 if not found.
    """
    if not x_student_id.isdigit():
        raise HTTPException(status_code=400, detail="X-Student-ID must be a numeric Telegram ID")

    telegram_id = int(x_student_id)
    result = await db.execute(select(Student).where(Student.telegram_id == telegram_id))
    student = result.scalar_one_or_none()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    logger.info("Profile fetched", student_id=student.student_id)
    return await _build_profile(student, db)


@router.patch("/student/profile", response_model=StudentProfile, tags=["Student"])
async def update_student_profile(
    request: ProfileUpdateRequest,
    x_student_id: str = Header(..., description="Student telegram ID"),
    db: AsyncSession = Depends(get_session),
) -> StudentProfile:
    """Update student language and/or grade preference.

    Args:
        request: Fields to update (language and/or grade).
        x_student_id: Student telegram ID from header.
        db: Async database session.

    Returns:
        Updated StudentProfile.

    Raises:
        HTTPException: 400 if header is invalid, 404 if not found.
    """
    if not x_student_id.isdigit():
        raise HTTPException(status_code=400, detail="X-Student-ID must be a numeric Telegram ID")

    telegram_id = int(x_student_id)
    result = await db.execute(select(Student).where(Student.telegram_id == telegram_id))
    student = result.scalar_one_or_none()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    if request.language is not None:
        student.language = request.language
    if request.grade is not None:
        student.grade = request.grade

    await db.flush()
    await db.commit()
    await db.refresh(student)

    logger.info(
        "Profile updated",
        student_id=student.student_id,
        language=student.language,
        grade=student.grade,
    )
    return await _build_profile(student, db)
