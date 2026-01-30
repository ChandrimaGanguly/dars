"""
Student model representing learners in the Dars platform.

Each student has a unique Telegram ID, grade level (6-8), and language preference.
"""

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.cost_record import CostRecord
    from src.models.session import Session
    from src.models.streak import Streak


class Student(Base, TimestampMixin):
    """Student profile representing a learner in the system.

    Attributes:
        student_id: Primary key, auto-incrementing.
        telegram_id: Unique Telegram user ID (used for authentication).
        name: Student's display name (max 100 chars).
        grade: Student's grade level (6, 7, or 8).
        language: Preferred language for content ('bn' for Bengali, 'en' for English).
        created_at: Timestamp when student registered.
        updated_at: Timestamp when profile last updated.
    """

    __tablename__ = "students"

    # Primary key
    student_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique student identifier",
    )

    # Authentication
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
        comment="Telegram user ID (unique across platform)",
    )

    # Profile information
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Student's display name",
    )

    grade: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Grade level (6, 7, or 8)",
    )

    language: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        server_default="bn",
        comment="Preferred language (bn=Bengali, en=English)",
    )

    # Relationships
    sessions: Mapped[list["Session"]] = relationship(
        "Session",
        back_populates="student",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    streak: Mapped["Streak"] = relationship(
        "Streak",
        back_populates="student",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )

    cost_records: Mapped[list["CostRecord"]] = relationship(
        "CostRecord",
        back_populates="student",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "grade IN (6, 7, 8)",
            name="ck_students_grade_valid",
        ),
        CheckConstraint(
            "language IN ('bn', 'en')",
            name="ck_students_language_valid",
        ),
        Index("idx_students_telegram_id", "telegram_id"),
        Index("idx_students_grade", "grade"),
    )

    def __repr__(self) -> str:
        """String representation of Student."""
        return (
            f"<Student(id={self.student_id}, telegram_id={self.telegram_id}, "
            f"name='{self.name}', grade={self.grade}, language='{self.language}')>"
        )
