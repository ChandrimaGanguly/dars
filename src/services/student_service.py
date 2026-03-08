"""Student database operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.logging import get_logger
from src.models.student import Student
from src.utils.pii import hash_telegram_id

logger = get_logger(__name__)


class StudentService:
    """Handle student database operations."""

    async def get_or_create(
        self,
        db: AsyncSession,
        telegram_id: int,
        name: str,
        grade: int = 7,
        language: str = "en",
    ) -> Student:
        """Get existing student or create new one (idempotent).

        For new students, grade and language should be provided after the
        onboarding flow collects them. Defaults are used only as fallback.

        Args:
            db: Database session
            telegram_id: Telegram user ID
            name: Student's first name
            grade: Grade level (6, 7, or 8); default 7
            language: Language preference ('en' or 'bn'); default 'en'

        Returns:
            Student record (existing or newly created)
        """
        result = await db.execute(select(Student).where(Student.telegram_id == telegram_id))
        student = result.scalar_one_or_none()

        if student:
            logger.info("Found existing student", hashed_id=hash_telegram_id(telegram_id))
            return student

        student = Student(
            telegram_id=telegram_id,
            name=name,
            grade=grade,
            language=language,
        )
        db.add(student)
        await db.commit()
        await db.refresh(student)

        logger.info(
            "Created new student",
            hashed_id=hash_telegram_id(telegram_id),
            grade=grade,
            language=language,
        )
        return student

    async def get_by_telegram_id(
        self,
        db: AsyncSession,
        telegram_id: int,
    ) -> Student | None:
        """Fetch a student by Telegram ID.

        Args:
            db: Database session
            telegram_id: Telegram user ID

        Returns:
            Student or None if not found
        """
        result = await db.execute(select(Student).where(Student.telegram_id == telegram_id))
        return result.scalar_one_or_none()
