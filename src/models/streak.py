"""
Streak model for tracking daily practice habits.

Tracks current streak, longest streak, and milestone achievements.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, CheckConstraint, Date, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.student import Student


class Streak(Base, TimestampMixin):
    """Streak tracking for daily practice habits.

    Tracks how many consecutive days a student has practiced, their longest
    streak, and milestone achievements (7, 14, 30 days).

    Attributes:
        student_id: Primary key and foreign key to students table.
        current_streak: Current consecutive days of practice.
        longest_streak: Longest streak ever achieved.
        last_practice_date: Date of last practice session.
        milestones_achieved: Array of milestone days reached (e.g., [7, 14, 30]).
        updated_at: Timestamp when streak last updated.
    """

    __tablename__ = "streaks"

    # Primary key (also foreign key)
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.student_id", ondelete="CASCADE"),
        primary_key=True,
        comment="Student this streak belongs to",
    )

    # Streak data
    current_streak: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        default=0,
        comment="Current consecutive days of practice",
    )

    longest_streak: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        default=0,
        comment="Longest streak ever achieved",
    )

    last_practice_date: Mapped[datetime | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date of last practice session",
    )

    milestones_achieved: Mapped[list[int]] = mapped_column(
        JSON,
        nullable=False,
        server_default="[]",
        default=list,
        comment="Array of milestone days reached (e.g., [7, 14, 30])",
    )

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="streak",
        lazy="selectin",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "current_streak >= 0",
            name="ck_streaks_current_nonnegative",
        ),
        CheckConstraint(
            "longest_streak >= 0",
            name="ck_streaks_longest_nonnegative",
        ),
        CheckConstraint(
            "longest_streak >= current_streak",
            name="ck_streaks_longest_ge_current",
        ),
        Index("idx_streaks_current", "current_streak"),
    )

    def add_milestone(self, milestone_days: int) -> None:
        """Add a milestone achievement if not already achieved.

        Args:
            milestone_days: Milestone day count (e.g., 7, 14, 30).
        """
        if milestone_days not in self.milestones_achieved:
            self.milestones_achieved.append(milestone_days)
            # Sort milestones in ascending order
            self.milestones_achieved.sort()

    def get_next_milestone(self) -> int | None:
        """Get next milestone to achieve.

        Returns:
            Next milestone day count, or None if no more milestones.
        """
        standard_milestones = [7, 14, 30, 60, 90, 180, 365]
        for milestone in standard_milestones:
            if milestone > self.current_streak:
                return milestone
        return None

    def __repr__(self) -> str:
        """String representation of Streak."""
        return (
            f"<Streak(student_id={self.student_id}, current={self.current_streak}, "
            f"longest={self.longest_streak}, milestones={self.milestones_achieved})>"
        )
