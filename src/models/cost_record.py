"""
CostRecord model for tracking API usage and costs.

Logs every Claude API call with token counts and cost calculations for business validation.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.student import Student


class OperationType:
    """API operation type enum values."""

    HINT_GENERATION = "hint_generation"
    ANSWER_EVALUATION = "answer_evaluation"


class ApiProvider:
    """API provider enum values."""

    CLAUDE = "claude"
    TWILIO = "twilio"


class CostRecord(Base):
    """Cost tracking for API calls.

    Logs every external API call with token usage and cost for business model validation.
    Critical for maintaining <$0.10/student/month budget.

    Attributes:
        cost_id: Primary key.
        student_id: Foreign key to students table.
        session_id: Optional foreign key to sessions table.
        operation: Type of operation (hint_generation, answer_evaluation).
        api_provider: Provider used (claude, twilio).
        input_tokens: Number of input tokens (Claude API).
        output_tokens: Number of output tokens (Claude API).
        cost_usd: Cost in USD.
        recorded_at: Timestamp when cost was recorded.
    """

    __tablename__ = "cost_records"

    # Primary key
    cost_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique cost record identifier",
    )

    # Foreign keys
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.student_id", ondelete="CASCADE"),
        nullable=False,
        comment="Student who triggered this cost",
    )

    session_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("sessions.session_id", ondelete="SET NULL"),
        nullable=True,
        comment="Optional session this cost belongs to",
    )

    # Operation details
    operation: Mapped[str] = mapped_column(
        Enum(
            OperationType.HINT_GENERATION,
            OperationType.ANSWER_EVALUATION,
            name="operation_type",
        ),
        nullable=False,
        comment="Type of operation performed",
    )

    api_provider: Mapped[str] = mapped_column(
        Enum(
            ApiProvider.CLAUDE,
            ApiProvider.TWILIO,
            name="api_provider",
        ),
        nullable=False,
        comment="API provider used",
    )

    # Cost metrics
    input_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of input tokens (Claude API)",
    )

    output_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of output tokens (Claude API)",
    )

    cost_usd: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Cost in USD",
    )

    # Timing
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
        comment="Timestamp when cost was recorded (UTC)",
    )

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="cost_records",
        lazy="selectin",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "cost_usd >= 0",
            name="ck_cost_records_cost_nonnegative",
        ),
        CheckConstraint(
            "input_tokens >= 0",
            name="ck_cost_records_input_nonnegative",
        ),
        CheckConstraint(
            "output_tokens >= 0",
            name="ck_cost_records_output_nonnegative",
        ),
        Index("idx_cost_records_student", "student_id"),
        Index("idx_cost_records_session", "session_id"),
        Index("idx_cost_records_recorded", "recorded_at"),
        Index("idx_cost_records_operation", "operation"),
    )

    def __repr__(self) -> str:
        """String representation of CostRecord."""
        return (
            f"<CostRecord(id={self.cost_id}, student_id={self.student_id}, "
            f"operation='{self.operation}', cost=${self.cost_usd:.4f})>"
        )
