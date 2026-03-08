"""Add sent_messages table for non-repeat tracking

Tracks which encouragement message keys were sent to each student to prevent
the same message being repeated within a 7-day window (REQ-013).

Revision ID: c1d2e3f4a5b6
Revises: b1c2d3e4f5a6
Create Date: 2026-03-06 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create sent_messages table.

    Columns:
    - id: INTEGER primary key (autoincrement)
    - student_id: INTEGER NOT NULL, FK → students.student_id, indexed
    - message_key: VARCHAR(100) NOT NULL — stable variant identifier
    - sent_at: TIMESTAMP NOT NULL, server_default=now()
    """
    op.create_table(
        "sent_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("message_key", sa.String(length=100), nullable=False),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),  # Fix 7: TIMESTAMPTZ for consistent UTC comparisons
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["students.student_id"],
            ondelete="CASCADE",  # Fix 5: cascade deletes to avoid orphaned rows
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sent_messages_student_id", "sent_messages", ["student_id"])


def downgrade() -> None:
    """Drop sent_messages table."""
    op.drop_index("ix_sent_messages_student_id", table_name="sent_messages")
    op.drop_table("sent_messages")
