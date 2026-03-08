"""add_difficulty_level_to_students

Adds adaptive difficulty level column to the students table (REQ-004).

Revision ID: b1c2d3e4f5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-03-05 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add difficulty_level column to students table.

    - difficulty_level: INTEGER, NOT NULL, server_default=1
      Constrained to (1, 2, 3) via CHECK constraint.
      1 = easy, 2 = medium, 3 = hard.
      Defaults to 1 (easy) for all existing and new students.
    """
    op.add_column(
        "students",
        sa.Column(
            "difficulty_level",
            sa.Integer(),
            nullable=False,
            server_default="1",
            comment="Current adaptive difficulty level (1=easy, 2=medium, 3=hard; REQ-004)",
        ),
    )
    op.create_check_constraint(
        "ck_students_difficulty_level_valid",
        "students",
        "difficulty_level IN (1, 2, 3)",
    )


def downgrade() -> None:
    """Remove difficulty_level column and its constraint from students table."""
    op.drop_constraint(
        "ck_students_difficulty_level_valid",
        "students",
        type_="check",
    )
    op.drop_column("students", "difficulty_level")
