"""
Session model representing daily practice sessions.

Each session contains 5 problems with student responses, timing data, and completion status.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.response import Response
    from src.models.student import Student


class SessionStatus:
    """Session status enum values."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class Session(Base, TimestampMixin):
    """Practice session (one 5-problem session).

    Each student can have one active session per day. Sessions contain 5 problems
    selected by the algorithm and track student responses, timing, and completion.

    Attributes:
        session_id: Primary key.
        student_id: Foreign key to students table.
        date: Date of session (for daily tracking).
        status: Session state (in_progress, completed, abandoned).
        problem_ids: Array of 5 problem IDs selected for this session.
        completed_at: Timestamp when session completed (nullable).
        expires_at: Timestamp when session expires (30 min after start).
        total_time_seconds: Total time spent on session.
        problems_correct: Count of correct answers (0-5).
        created_at: Timestamp when session started.
        updated_at: Timestamp when session last updated.
    """

    __tablename__ = "sessions"

    # Primary key
    session_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique session identifier",
    )

    # Foreign keys
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.student_id", ondelete="CASCADE"),
        nullable=False,
        comment="Student who owns this session",
    )

    # Session metadata
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Date of practice session (UTC)",
    )

    status: Mapped[str] = mapped_column(
        Enum(
            SessionStatus.IN_PROGRESS,
            SessionStatus.COMPLETED,
            SessionStatus.ABANDONED,
            name="session_status",
        ),
        nullable=False,
        server_default=SessionStatus.IN_PROGRESS,
        comment="Session state",
    )

    # Problem selection
    problem_ids: Mapped[list[int]] = mapped_column(
        JSON,
        nullable=False,
        comment="Array of 5 problem IDs selected for this session",
    )

    # Timing
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when session completed (UTC)",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Timestamp when session expires (30 min after start, UTC)",
    )

    # Analytics
    total_time_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        default=0,
        comment="Total time spent on session in seconds",
    )

    problems_correct: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        default=0,
        comment="Count of correct answers (0-5)",
    )

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="sessions",
        lazy="selectin",
    )

    responses: Mapped[list["Response"]] = relationship(
        "Response",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "problems_correct >= 0 AND problems_correct <= 5",
            name="ck_sessions_problems_correct_range",
        ),
        CheckConstraint(
            "total_time_seconds >= 0",
            name="ck_sessions_time_positive",
        ),
        Index("idx_sessions_student_created", "student_id", "created_at"),
        Index("idx_sessions_status", "status"),
        Index("idx_sessions_date", "date"),
    )

    def is_expired(self) -> bool:
        """Check if session has expired.

        Returns:
            True if current time is past expires_at timestamp.
        """

        return datetime.now(UTC) > self.expires_at

    def get_accuracy(self) -> float:
        """Calculate accuracy percentage for session.

        Returns:
            Accuracy as percentage (0-100).
        """
        total_responses = len(self.responses)
        if total_responses == 0:
            return 0.0
        return (self.problems_correct / total_responses) * 100

    def __repr__(self) -> str:
        """String representation of Session."""
        return (
            f"<Session(id={self.session_id}, student_id={self.student_id}, "
            f"status='{self.status}', correct={self.problems_correct}/5)>"
        )
