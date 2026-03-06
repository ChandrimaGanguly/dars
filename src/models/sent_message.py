"""SentMessage model — tracks which message keys were sent to each student.

PHASE6-B-2 (REQ-013): Prevents the same encouragement message from being
sent twice to the same student within a 7-day window.

The 7-day TTL is enforced via a query filter (WHERE sent_at >= now() - 7 days),
NOT by deleting old rows. This keeps the audit trail intact.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.models.base import Base


class SentMessage(Base):
    """Track messages sent to students to prevent repetition within 7 days.

    Keyed on (student_id, message_key) where message_key is a stable
    identifier like "correct_streak_low_0" (type + variant index).

    Attributes:
        id: Primary key.
        student_id: Foreign key to students table.
        message_key: Stable string identifier for the message variant.
        sent_at: UTC timestamp when the message was sent.
    """

    __tablename__ = "sent_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.student_id", ondelete="CASCADE"),  # Fix 5: cascade deletes
        index=True,
        nullable=False,
    )
    message_key: Mapped[str] = mapped_column(String(100), nullable=False)
    # Fix 7: timezone=True ensures TIMESTAMPTZ in PostgreSQL — consistent UTC comparisons
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<SentMessage id={self.id} student_id={self.student_id} key={self.message_key!r}>"
