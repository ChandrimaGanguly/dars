"""
StudentRepository — data access layer for the students table.

Provides lookup and update operations for student profiles.
All methods accept an AsyncSession provided by the caller; transaction
management (commit/rollback) is the caller's responsibility.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.student import Student

# Valid difficulty levels (REQ-004)
_MIN_DIFFICULTY: int = 1
_MAX_DIFFICULTY: int = 3


class StudentRepository:
    """Data access methods for the students table.

    Example::

        repo = StudentRepository()
        student = await repo.get_by_telegram_id(db, telegram_id=123456)
    """

    async def get_by_telegram_id(
        self,
        db: AsyncSession,
        telegram_id: int,
    ) -> Student | None:
        """Retrieve a student by Telegram user ID.

        Args:
            db: Active async database session.
            telegram_id: Telegram user ID.

        Returns:
            Student object if found, None otherwise.
        """
        stmt = select(Student).where(Student.telegram_id == telegram_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(
        self,
        db: AsyncSession,
        student_id: int,
    ) -> Student | None:
        """Retrieve a student by primary key.

        Args:
            db: Active async database session.
            student_id: Student primary key.

        Returns:
            Student object if found, None otherwise.
        """
        stmt = select(Student).where(Student.student_id == student_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_difficulty(
        self,
        db: AsyncSession,
        student_id: int,
    ) -> int:
        """Return the student's current adaptive difficulty level (REQ-004).

        Args:
            db: Active async database session.
            student_id: Student primary key.

        Returns:
            Difficulty level in [1, 2, 3]. Returns 1 (easy) if student not found.
        """
        student = await self.get_by_id(db, student_id)
        if student is None:
            return _MIN_DIFFICULTY
        return student.difficulty_level

    async def set_difficulty(
        self,
        db: AsyncSession,
        student: Student,
        new_level: int,
    ) -> None:
        """Update the student's adaptive difficulty level and flush.

        Clamps new_level to [1, 3] so callers never need to guard against
        out-of-range values.  Uses flush() not commit() — the caller owns
        the transaction boundary.

        Args:
            db: Active async database session.
            student: Student ORM object to update.
            new_level: New difficulty level (clamped to [1, 3]).
        """
        clamped = max(_MIN_DIFFICULTY, min(_MAX_DIFFICULTY, new_level))
        student.difficulty_level = clamped
        db.add(student)
        await db.flush()
