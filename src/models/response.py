"""
Response model representing student answers to problems.

Each response tracks the student's answer, correctness, time spent, and hints used.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.problem import Hint
    from src.models.session import Session


class ConfidenceLevel:
    """Confidence level enum values."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Response(Base):
    """Student's answer to a problem.

    Tracks answer correctness, time spent, hints used, and confidence level.

    Attributes:
        response_id: Primary key.
        session_id: Foreign key to sessions table.
        problem_id: Foreign key to problems table.
        student_answer: Student's submitted answer (string).
        is_correct: Whether answer was correct.
        time_spent_seconds: Time spent on this problem.
        hints_used: Number of hints requested (0-3).
        hints_viewed: Array of Hint objects viewed (JSON).
        evaluated_at: Timestamp when answer was evaluated.
        confidence_level: Confidence based on hints needed (low/medium/high).
    """

    __tablename__ = "responses"

    # Primary key
    response_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique response identifier",
    )

    # Foreign keys
    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        comment="Session this response belongs to",
    )

    problem_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("problems.problem_id", ondelete="CASCADE"),
        nullable=False,
        comment="Problem being answered",
    )

    # Answer data
    student_answer: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Student's submitted answer",
    )

    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="Whether answer was correct",
    )

    time_spent_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        default=0,
        comment="Time spent on this problem in seconds",
    )

    # Hint usage
    hints_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        default=0,
        comment="Number of hints requested (0-3)",
    )

    hints_viewed: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        server_default="[]",
        default=list,
        comment="Array of Hint objects viewed (JSON)",
    )

    # Evaluation
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
        comment="Timestamp when answer was evaluated (UTC)",
    )

    confidence_level: Mapped[str] = mapped_column(
        Enum(
            ConfidenceLevel.LOW,
            ConfidenceLevel.MEDIUM,
            ConfidenceLevel.HIGH,
            name="confidence_level",
        ),
        nullable=False,
        server_default=ConfidenceLevel.MEDIUM,
        comment="Confidence based on hints needed",
    )

    # Relationships
    session: Mapped["Session"] = relationship(
        "Session",
        back_populates="responses",
        lazy="selectin",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "hints_used >= 0 AND hints_used <= 3",
            name="ck_responses_hints_range",
        ),
        CheckConstraint(
            "time_spent_seconds >= 0",
            name="ck_responses_time_positive",
        ),
        Index("idx_responses_session", "session_id"),
        Index("idx_responses_problem", "problem_id"),
        Index("idx_responses_correctness", "is_correct"),
    )

    def get_hints_viewed(self) -> list["Hint"]:
        """Get hints viewed as Hint objects.

        Returns:
            List of Hint objects.
        """
        from src.models.problem import Hint

        return [Hint.from_dict(hint_dict) for hint_dict in self.hints_viewed]

    def __repr__(self) -> str:
        """String representation of Response."""
        return (
            f"<Response(id={self.response_id}, session_id={self.session_id}, "
            f"problem_id={self.problem_id}, correct={self.is_correct}, "
            f"hints_used={self.hints_used})>"
        )
