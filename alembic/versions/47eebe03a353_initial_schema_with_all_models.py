"""Initial schema with all models

Revision ID: 47eebe03a353
Revises: 
Create Date: 2026-01-28 09:49:36.285544

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47eebe03a353'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables for Dars platform."""
    # Create students table
    op.create_table(
        'students',
        sa.Column('student_id', sa.Integer(), autoincrement=True, nullable=False, comment='Unique student identifier'),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False, comment='Telegram user ID (unique across platform)'),
        sa.Column('name', sa.String(length=100), nullable=False, comment="Student's display name"),
        sa.Column('grade', sa.Integer(), nullable=False, comment='Grade level (6, 7, or 8)'),
        sa.Column('language', sa.String(length=2), server_default='bn', nullable=False, comment='Preferred language (bn=Bengali, en=English)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False, comment='Timestamp when record was created (UTC)'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False, comment='Timestamp when record was last updated (UTC)'),
        sa.CheckConstraint('grade IN (6, 7, 8)', name='ck_students_grade_valid'),
        sa.CheckConstraint("language IN ('bn', 'en')", name='ck_students_language_valid'),
        sa.PrimaryKeyConstraint('student_id', name=op.f('pk_students')),
        sa.UniqueConstraint('telegram_id', name=op.f('uq_students_telegram_id'))
    )
    op.create_index('idx_students_telegram_id', 'students', ['telegram_id'])
    op.create_index('idx_students_grade', 'students', ['grade'])

    # Create problems table
    op.create_table(
        'problems',
        sa.Column('problem_id', sa.Integer(), autoincrement=True, nullable=False, comment='Unique problem identifier'),
        sa.Column('grade', sa.Integer(), nullable=False, comment='Grade level (6, 7, or 8)'),
        sa.Column('topic', sa.String(length=100), nullable=False, comment="Topic category (e.g., 'Profit & Loss')"),
        sa.Column('subtopic', sa.String(length=100), nullable=True, comment='Optional subtopic classification'),
        sa.Column('question_en', sa.Text(), nullable=False, comment='Problem statement in English'),
        sa.Column('question_bn', sa.Text(), nullable=False, comment='Problem statement in Bengali'),
        sa.Column('answer', sa.String(length=500), nullable=False, comment="Correct answer (accept format: '75 rupees' or '75')"),
        sa.Column('hints', sa.JSON(), nullable=False, comment='Array of 3 hints (JSON format)'),
        sa.Column('difficulty', sa.Integer(), nullable=False, comment='Difficulty level (1=easy, 2=medium, 3=hard)'),
        sa.Column('estimated_time_minutes', sa.Integer(), server_default='5', nullable=False, comment='Estimated time to solve in minutes'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False, comment='Timestamp when record was created (UTC)'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False, comment='Timestamp when record was last updated (UTC)'),
        sa.CheckConstraint('grade IN (6, 7, 8)', name='ck_problems_grade_valid'),
        sa.CheckConstraint('difficulty IN (1, 2, 3)', name='ck_problems_difficulty_valid'),
        sa.CheckConstraint('estimated_time_minutes > 0', name='ck_problems_time_positive'),
        sa.PrimaryKeyConstraint('problem_id', name=op.f('pk_problems'))
    )
    op.create_index('idx_problems_grade_topic', 'problems', ['grade', 'topic'])
    op.create_index('idx_problems_difficulty', 'problems', ['difficulty'])

    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('session_id', sa.Integer(), autoincrement=True, nullable=False, comment='Unique session identifier'),
        sa.Column('student_id', sa.Integer(), nullable=False, comment='Student who owns this session'),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False, comment='Date of practice session (UTC)'),
        sa.Column('status', sa.Enum('in_progress', 'completed', 'abandoned', name='session_status'), server_default='in_progress', nullable=False, comment='Session state'),
        sa.Column('problem_ids', sa.JSON(), nullable=False, comment='Array of 5 problem IDs selected for this session'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when session completed (UTC)'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, comment='Timestamp when session expires (30 min after start, UTC)'),
        sa.Column('total_time_seconds', sa.Integer(), server_default='0', nullable=False, comment='Total time spent on session in seconds'),
        sa.Column('problems_correct', sa.Integer(), server_default='0', nullable=False, comment='Count of correct answers (0-5)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False, comment='Timestamp when record was created (UTC)'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False, comment='Timestamp when record was last updated (UTC)'),
        sa.CheckConstraint('problems_correct >= 0 AND problems_correct <= 5', name='ck_sessions_problems_correct_range'),
        sa.CheckConstraint('total_time_seconds >= 0', name='ck_sessions_time_positive'),
        sa.ForeignKeyConstraint(['student_id'], ['students.student_id'], name=op.f('fk_sessions_student_id_students'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('session_id', name=op.f('pk_sessions'))
    )
    op.create_index('idx_sessions_student_created', 'sessions', ['student_id', 'created_at'])
    op.create_index('idx_sessions_status', 'sessions', ['status'])
    op.create_index('idx_sessions_date', 'sessions', ['date'])

    # Create responses table
    op.create_table(
        'responses',
        sa.Column('response_id', sa.Integer(), autoincrement=True, nullable=False, comment='Unique response identifier'),
        sa.Column('session_id', sa.Integer(), nullable=False, comment='Session this response belongs to'),
        sa.Column('problem_id', sa.Integer(), nullable=False, comment='Problem being answered'),
        sa.Column('student_answer', sa.String(length=500), nullable=False, comment="Student's submitted answer"),
        sa.Column('is_correct', sa.Boolean(), nullable=False, comment='Whether answer was correct'),
        sa.Column('time_spent_seconds', sa.Integer(), server_default='0', nullable=False, comment='Time spent on this problem in seconds'),
        sa.Column('hints_used', sa.Integer(), server_default='0', nullable=False, comment='Number of hints requested (0-3)'),
        sa.Column('hints_viewed', sa.JSON(), server_default='[]', nullable=False, comment='Array of Hint objects viewed (JSON)'),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False, comment='Timestamp when answer was evaluated (UTC)'),
        sa.Column('confidence_level', sa.Enum('low', 'medium', 'high', name='confidence_level'), server_default='medium', nullable=False, comment='Confidence based on hints needed'),
        sa.CheckConstraint('hints_used >= 0 AND hints_used <= 3', name='ck_responses_hints_range'),
        sa.CheckConstraint('time_spent_seconds >= 0', name='ck_responses_time_positive'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.session_id'], name=op.f('fk_responses_session_id_sessions'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.problem_id'], name=op.f('fk_responses_problem_id_problems'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('response_id', name=op.f('pk_responses'))
    )
    op.create_index('idx_responses_session', 'responses', ['session_id'])
    op.create_index('idx_responses_problem', 'responses', ['problem_id'])
    op.create_index('idx_responses_correctness', 'responses', ['is_correct'])

    # Create streaks table
    op.create_table(
        'streaks',
        sa.Column('student_id', sa.Integer(), nullable=False, comment='Student this streak belongs to'),
        sa.Column('current_streak', sa.Integer(), server_default='0', nullable=False, comment='Current consecutive days of practice'),
        sa.Column('longest_streak', sa.Integer(), server_default='0', nullable=False, comment='Longest streak ever achieved'),
        sa.Column('last_practice_date', sa.Date(), nullable=True, comment='Date of last practice session'),
        sa.Column('milestones_achieved', sa.JSON(), server_default='[]', nullable=False, comment='Array of milestone days reached (e.g., [7, 14, 30])'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False, comment='Timestamp when record was created (UTC)'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False, comment='Timestamp when record was last updated (UTC)'),
        sa.CheckConstraint('current_streak >= 0', name='ck_streaks_current_nonnegative'),
        sa.CheckConstraint('longest_streak >= 0', name='ck_streaks_longest_nonnegative'),
        sa.CheckConstraint('longest_streak >= current_streak', name='ck_streaks_longest_ge_current'),
        sa.ForeignKeyConstraint(['student_id'], ['students.student_id'], name=op.f('fk_streaks_student_id_students'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('student_id', name=op.f('pk_streaks'))
    )
    op.create_index('idx_streaks_current', 'streaks', ['current_streak'])

    # Create cost_records table
    op.create_table(
        'cost_records',
        sa.Column('cost_id', sa.Integer(), autoincrement=True, nullable=False, comment='Unique cost record identifier'),
        sa.Column('student_id', sa.Integer(), nullable=False, comment='Student who triggered this cost'),
        sa.Column('session_id', sa.Integer(), nullable=True, comment='Optional session this cost belongs to'),
        sa.Column('operation', sa.Enum('hint_generation', 'answer_evaluation', name='operation_type'), nullable=False, comment='Type of operation performed'),
        sa.Column('api_provider', sa.Enum('claude', 'twilio', name='api_provider'), nullable=False, comment='API provider used'),
        sa.Column('input_tokens', sa.Integer(), nullable=True, comment='Number of input tokens (Claude API)'),
        sa.Column('output_tokens', sa.Integer(), nullable=True, comment='Number of output tokens (Claude API)'),
        sa.Column('cost_usd', sa.Float(), nullable=False, comment='Cost in USD'),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False, comment='Timestamp when cost was recorded (UTC)'),
        sa.CheckConstraint('cost_usd >= 0', name='ck_cost_records_cost_nonnegative'),
        sa.CheckConstraint('input_tokens >= 0', name='ck_cost_records_input_nonnegative'),
        sa.CheckConstraint('output_tokens >= 0', name='ck_cost_records_output_nonnegative'),
        sa.ForeignKeyConstraint(['student_id'], ['students.student_id'], name=op.f('fk_cost_records_student_id_students'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.session_id'], name=op.f('fk_cost_records_session_id_sessions'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('cost_id', name=op.f('pk_cost_records'))
    )
    op.create_index('idx_cost_records_student', 'cost_records', ['student_id'])
    op.create_index('idx_cost_records_session', 'cost_records', ['session_id'])
    op.create_index('idx_cost_records_recorded', 'cost_records', ['recorded_at'])
    op.create_index('idx_cost_records_operation', 'cost_records', ['operation'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index('idx_cost_records_operation', table_name='cost_records')
    op.drop_index('idx_cost_records_recorded', table_name='cost_records')
    op.drop_index('idx_cost_records_session', table_name='cost_records')
    op.drop_index('idx_cost_records_student', table_name='cost_records')
    op.drop_table('cost_records')

    op.drop_index('idx_streaks_current', table_name='streaks')
    op.drop_table('streaks')

    op.drop_index('idx_responses_correctness', table_name='responses')
    op.drop_index('idx_responses_problem', table_name='responses')
    op.drop_index('idx_responses_session', table_name='responses')
    op.drop_table('responses')

    op.drop_index('idx_sessions_date', table_name='sessions')
    op.drop_index('idx_sessions_status', table_name='sessions')
    op.drop_index('idx_sessions_student_created', table_name='sessions')
    op.drop_table('sessions')

    op.drop_index('idx_problems_difficulty', table_name='problems')
    op.drop_index('idx_problems_grade_topic', table_name='problems')
    op.drop_table('problems')

    op.drop_index('idx_students_grade', table_name='students')
    op.drop_index('idx_students_telegram_id', table_name='students')
    op.drop_table('students')
