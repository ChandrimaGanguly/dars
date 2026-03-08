"""add_answer_type_columns_to_problems

Revision ID: a1b2c3d4e5f6
Revises: 4822235d35e4
Create Date: 2026-03-04 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "4822235d35e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add answer_type, acceptable_tolerance_percent, and multiple_choice_options to problems.

    - answer_type: VARCHAR(20), NOT NULL, server_default='numeric'
      Constrained to ('numeric', 'multiple_choice', 'text') via CHECK constraint.
    - acceptable_tolerance_percent: FLOAT, nullable.
      Tolerance for numeric answer evaluation (e.g., 5.0 means ±5%).
    - multiple_choice_options: JSON, nullable.
      Options for multiple-choice problems (list of strings).
    """
    op.add_column(
        "problems",
        sa.Column(
            "answer_type",
            sa.String(length=20),
            nullable=False,
            server_default="numeric",
            comment="Answer type: numeric, multiple_choice, or text",
        ),
    )
    op.add_column(
        "problems",
        sa.Column(
            "acceptable_tolerance_percent",
            sa.Float(),
            nullable=True,
            comment="Tolerance for numeric answers as percentage (e.g. 5.0 = ±5%)",
        ),
    )
    op.add_column(
        "problems",
        sa.Column(
            "multiple_choice_options",
            sa.JSON(),
            nullable=True,
            comment="List of answer options for multiple_choice problems",
        ),
    )

    # Add CHECK constraint for answer_type validity
    op.create_check_constraint(
        "ck_problems_answer_type_valid",
        "problems",
        "answer_type IN ('numeric', 'multiple_choice', 'text')",
    )


def downgrade() -> None:
    """Remove answer_type, acceptable_tolerance_percent, and multiple_choice_options from problems."""
    op.drop_constraint("ck_problems_answer_type_valid", "problems", type_="check")
    op.drop_column("problems", "multiple_choice_options")
    op.drop_column("problems", "acceptable_tolerance_percent")
    op.drop_column("problems", "answer_type")
