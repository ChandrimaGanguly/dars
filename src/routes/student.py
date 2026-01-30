"""Student profile endpoints."""

from datetime import datetime

from fastapi import APIRouter, Header

from src.schemas.student import ProfileUpdateRequest, StudentProfile

router = APIRouter()


@router.get("/student/profile", response_model=StudentProfile, tags=["Student"])
async def get_student_profile(
    x_student_id: str = Header(..., description="Student telegram ID")
) -> StudentProfile:
    """Get student's learning profile.

    Returns student's profile with learning progress and preferences.

    Args:
        x_student_id: Student telegram ID from header.

    Returns:
        StudentProfile with complete profile data.

    Raises:
        HTTPException: If student not found.
    """
    # TODO: Implement profile retrieval
    # - Validate student exists
    # - Fetch profile from database
    # - Include calculated fields (avg_accuracy, current_streak)

    # Mock data
    return StudentProfile(
        student_id=1,
        telegram_id=int(x_student_id) if x_student_id.isdigit() else 987654321,
        name="Rajesh",
        grade=7,
        language="bn",
        current_streak=12,
        longest_streak=28,
        avg_accuracy=72.5,
        last_practice=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@router.patch("/student/profile", response_model=StudentProfile, tags=["Student"])
async def update_student_profile(
    request: ProfileUpdateRequest,
    x_student_id: str = Header(..., description="Student telegram ID"),
) -> StudentProfile:
    """Update student preferences.

    Updates language preference, grade level, or other settings.

    Args:
        request: Profile update request with fields to update.
        x_student_id: Student telegram ID from header.

    Returns:
        StudentProfile with updated data.

    Raises:
        HTTPException: If student not found or validation fails.
    """
    # TODO: Implement profile update
    # - Validate student exists
    # - Validate update data
    # - Update database
    # - Return updated profile

    # Mock response - return current profile
    return StudentProfile(
        student_id=1,
        telegram_id=int(x_student_id) if x_student_id.isdigit() else 987654321,
        name="Rajesh",
        grade=request.grade if request.grade else 7,
        language=request.language if request.language else "bn",
        current_streak=12,
        longest_streak=28,
        avg_accuracy=72.5,
        last_practice=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
