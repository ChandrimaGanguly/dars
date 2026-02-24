"""
Message template model for bilingual content (English + Bengali).

Stores all user-facing messages with support for variable interpolation.
Satisfies REQ-021: Bengali Language Support.
"""

from typing import Any

from sqlalchemy import JSON, CheckConstraint, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class MessageCategory:
    """Message category enum values."""

    FEEDBACK = "feedback"  # Answer evaluation feedback
    MILESTONE = "milestone"  # Streak achievement messages
    NOTIFICATION = "notification"  # Reminders, encouragement
    UI = "ui"  # Buttons, labels, common UI text
    ERROR = "error"  # Validation and system errors


class MessageTemplate(Base, TimestampMixin):
    """Bilingual message template for user-facing content.

    Stores all translatable strings with variable interpolation support.
    Messages are retrieved based on message_key and formatted with variables.

    Example:
        ```python
        # Database: message_key="streak_milestone_7"
        # message_en="Congratulations {student_name}! You've reached a {days} day streak! 🔥"
        # message_bn="{student_name}, অভিনন্দন! আপনি {days} দিনের ধারাবাহিকতা অর্জন করেছেন! 🔥"

        template = await db.get(MessageTemplate, "streak_milestone_7")
        message = template.get_message("bn", student_name="রহিম", days=7)
        # Returns: "রহিম, অভিনন্দন! আপনি 7 দিনের ধারাবাহিকতা অর্জন করেছেন! 🔥"
        ```

    Attributes:
        message_id: Primary key.
        message_key: Unique identifier (e.g., "feedback_correct", "milestone_7day").
        category: Message category (feedback, milestone, notification, ui, error).
        message_en: English message template with {variable} placeholders.
        message_bn: Bengali message template with {variable} placeholders.
        variables: JSON array of variable names used in template.
        description: Human-readable description of when this message is used.
        created_at: Timestamp when template was created.
        updated_at: Timestamp when template was last modified.
    """

    __tablename__ = "message_templates"

    # Primary key
    message_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique message template identifier",
    )

    # Message identification
    message_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="Unique key for message lookup (e.g., 'feedback_correct')",
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Message category (feedback, milestone, notification, ui, error)",
    )

    # Bilingual content (REQ-021)
    message_en: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="English message template with {variable} placeholders",
    )

    message_bn: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Bengali message template with {variable} placeholders",
    )

    # Metadata
    variables: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        server_default="[]",
        default=list,
        comment="Array of variable names used in template (e.g., ['student_name', 'days'])",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable description of message usage",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            f"category IN ('{MessageCategory.FEEDBACK}', '{MessageCategory.MILESTONE}', "
            f"'{MessageCategory.NOTIFICATION}', '{MessageCategory.UI}', '{MessageCategory.ERROR}')",
            name="ck_message_templates_category_valid",
        ),
        UniqueConstraint("message_key", name="uq_message_templates_key"),
        Index("idx_message_templates_category", "category"),
        Index("idx_message_templates_key", "message_key"),
    )

    def get_message(self, language: str, **kwargs: Any) -> str:
        """Get formatted message in specified language.

        Args:
            language: 'en' for English, 'bn' for Bengali.
            **kwargs: Variable values to interpolate into template.

        Returns:
            Formatted message with variables replaced.

        Example:
            >>> template.get_message("en", student_name="John", score=5)
            "Great job John! You scored 5/5!"
        """
        template = self.message_bn if language == "bn" else self.message_en

        # Format template with provided variables
        try:
            return template.format(**kwargs)
        except KeyError as e:
            # Missing variable - return template with error note
            return f"{template} [Missing variable: {e}]"

    def __repr__(self) -> str:
        """String representation of MessageTemplate."""
        return (
            f"<MessageTemplate(id={self.message_id}, key='{self.message_key}', "
            f"category='{self.category}')>"
        )
