"""Adaptive difficulty service for the Dars tutoring platform.

Implements REQ-004: adjusts a student's difficulty level based on session
performance across consecutive sessions.

Business rules:
    - Downgrade (-1 level) if student gets ≤1/5 correct in current session.
    - Upgrade   (+1 level) if student gets ≥4/5 correct in BOTH the current
      session AND the previous session (two consecutive strong sessions required
      to prevent premature promotion).
    - No change otherwise.
    - Difficulty is clamped to [1, 3] (1=easy, 2=medium, 3=hard).

All DB operations use flush() — the caller owns the transaction boundary.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from src.logging import get_logger
from src.models.student import Student
from src.repositories.student_repository import StudentRepository

logger = get_logger(__name__)

# Thresholds (out of 5 problems per session)
_DOWNGRADE_THRESHOLD: int = 1  # ≤1 correct → downgrade
_UPGRADE_THRESHOLD: int = 4  # ≥4 correct in BOTH sessions → upgrade

_student_repo = StudentRepository()


class AdaptiveDifficultyService:
    """Adjust student difficulty based on session performance (REQ-004).

    Example::

        svc = AdaptiveDifficultyService()
        student, new_level = await svc.update_difficulty(
            db, student,
            session_results=[True, True, True, True, False],
            prev_session_results=[True, True, True, True, True],
        )
        # new_level == 2 if student was at level 1
    """

    async def update_difficulty(
        self,
        db: AsyncSession,
        student: Student,
        session_results: list[bool],
        prev_session_results: list[bool] | None = None,
    ) -> tuple[Student, int]:
        """Evaluate session results and update the student's difficulty level.

        Args:
            db: Active async database session.
            student: Student ORM object to update.
            session_results: Ordered list of correct/incorrect booleans for the
                current session (True = correct).
            prev_session_results: Results from the immediately preceding session.
                Required for upgrade: without a previous session, upgrades are
                not applied (prevents promotion on first session alone).

        Returns:
            Tuple of (updated Student, new difficulty level as int).
            The Student's difficulty_level attribute is updated in-place.
        """
        current_level = student.difficulty_level
        correct_count = sum(1 for r in session_results if r)

        if correct_count <= _DOWNGRADE_THRESHOLD:
            new_level = max(1, current_level - 1)
        elif (
            correct_count >= _UPGRADE_THRESHOLD
            and prev_session_results is not None
            and sum(1 for r in prev_session_results if r) >= _UPGRADE_THRESHOLD
        ):
            new_level = min(3, current_level + 1)
        else:
            new_level = current_level

        if new_level > current_level:
            await _student_repo.set_difficulty(db, student, new_level)
            logger.info(
                "difficulty_upgraded",
                extra={
                    "student_id": student.student_id,
                    "from_level": current_level,
                    "to_level": student.difficulty_level,
                    "correct_count": correct_count,
                },
            )
        elif new_level < current_level:
            await _student_repo.set_difficulty(db, student, new_level)
            logger.info(
                "difficulty_downgraded",
                extra={
                    "student_id": student.student_id,
                    "from_level": current_level,
                    "to_level": student.difficulty_level,
                    "correct_count": correct_count,
                },
            )
        else:
            logger.debug(
                "difficulty_no_change",
                extra={
                    "student_id": student.student_id,
                    "level": current_level,
                    "correct_count": correct_count,
                },
            )

        return student, student.difficulty_level
