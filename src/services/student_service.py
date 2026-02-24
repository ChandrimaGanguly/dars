"""Student database operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.logging import get_logger
from src.models.student import Student

logger = get_logger(__name__)


class StudentService:
    """Handle student database operations."""

    async def get_or_create(
        self,
        db: AsyncSession,
        telegram_id: int,
        name: str,
    ) -> Student:
        """Get existing student or create new one (idempotent).

        Args:
            db: Database session
            telegram_id: Telegram user ID
            name: Student's first name

        Returns:
            Student record (existing or newly created)
        """
        # Check if student exists
        result = await db.execute(select(Student).where(Student.telegram_id == telegram_id))
        student = result.scalar_one_or_none()

        if student:
            logger.info(f"Found existing student {telegram_id}")
            return student

        # Create new student
        student = Student(
            telegram_id=telegram_id,
            name=name,
            grade=7,  # Default grade
            language="en",  # English only for now
        )
        db.add(student)
        await db.commit()
        await db.refresh(student)

        logger.info(f"Created new student {telegram_id}")
        return student
