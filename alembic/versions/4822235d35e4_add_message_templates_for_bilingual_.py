"""add_message_templates_for_bilingual_support

Revision ID: 4822235d35e4
Revises: 47eebe03a353
Create Date: 2026-02-24 13:16:31.928976

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4822235d35e4'
down_revision: Union[str, Sequence[str], None] = '47eebe03a353'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add message_templates table for bilingual content (REQ-021).

    This table stores all user-facing messages in Bengali and English:
    - Feedback messages (answer evaluation)
    - Milestone messages (streak achievements)
    - Notification messages (reminders, encouragement)
    - UI messages (buttons, labels)
    - Error messages (validation, system errors)
    """
    # Create message_templates table
    op.create_table(
        'message_templates',
        sa.Column('message_id', sa.Integer(), autoincrement=True, nullable=False, comment='Unique message template identifier'),
        sa.Column('message_key', sa.String(length=100), nullable=False, comment="Unique key for message lookup (e.g., 'feedback_correct')"),
        sa.Column('category', sa.String(length=50), nullable=False, comment='Message category (feedback, milestone, notification, ui, error)'),
        sa.Column('message_en', sa.Text(), nullable=False, comment='English message template with {variable} placeholders'),
        sa.Column('message_bn', sa.Text(), nullable=False, comment='Bengali message template with {variable} placeholders'),
        sa.Column('variables', sa.JSON(), server_default='[]', nullable=False, comment="Array of variable names used in template (e.g., ['student_name', 'days'])"),
        sa.Column('description', sa.Text(), nullable=True, comment='Human-readable description of message usage'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False, comment='Timestamp when template was created (UTC)'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False, comment='Timestamp when template was last modified (UTC)'),
        sa.CheckConstraint("category IN ('feedback', 'milestone', 'notification', 'ui', 'error')", name='ck_message_templates_category_valid'),
        sa.PrimaryKeyConstraint('message_id'),
        sa.UniqueConstraint('message_key', name='uq_message_templates_key')
    )

    # Create indexes for efficient lookups
    op.create_index('idx_message_templates_category', 'message_templates', ['category'], unique=False)
    op.create_index('idx_message_templates_key', 'message_templates', ['message_key'], unique=False)

    # Insert seed data for common messages
    op.execute("""
        INSERT INTO message_templates (message_key, category, message_en, message_bn, variables, description) VALUES
        -- Feedback messages
        ('feedback_correct', 'feedback', 'Correct! Well done! 🎉', 'সঠিক! সাবাশ! 🎉', '[]', 'Displayed when student answers correctly'),
        ('feedback_incorrect', 'feedback', 'Not quite right. Try again or ask for a hint!', 'ঠিক নয়। আবার চেষ্টা করুন অথবা একটি ইঙ্গিত চান!', '[]', 'Displayed when student answers incorrectly'),
        ('feedback_correct_with_hints', 'feedback', 'Correct! You used {hints_used} hint(s). Try to solve without hints next time! ✨', 'সঠিক! আপনি {hints_used}টি ইঙ্গিত ব্যবহার করেছেন। পরের বার ইঙ্গিত ছাড়াই সমাধান করার চেষ্টা করুন! ✨', '["hints_used"]', 'Displayed when student answers correctly after using hints'),

        -- Milestone messages
        ('milestone_7day', 'milestone', 'Amazing! You''ve reached a 7 day streak! 🔥', 'অসাধারণ! আপনি ৭ দিনের ধারাবাহিকতা অর্জন করেছেন! 🔥', '[]', '7 day streak achievement'),
        ('milestone_14day', 'milestone', 'Incredible! 14 days in a row! Keep it up! 💪', 'অবিশ্বাস্য! পরপর ১৪ দিন! এভাবেই চালিয়ে যান! 💪', '[]', '14 day streak achievement'),
        ('milestone_30day', 'milestone', 'Spectacular! 30 day streak! You''re unstoppable! 🌟', 'দুর্দান্ত! ৩০ দিনের ধারাবাহিকতা! আপনি অপ্রতিরোধ্য! 🌟', '[]', '30 day streak achievement'),

        -- Notification messages
        ('reminder_practice', 'notification', 'Don''t forget to practice today! Your {current_streak} day streak is waiting! 📚', 'আজ অনুশীলন করতে ভুলবেন না! আপনার {current_streak} দিনের ধারাবাহিকতা অপেক্ষা করছে! 📚', '["current_streak"]', 'Daily reminder to maintain streak'),
        ('encouragement_start', 'notification', 'Let''s start your practice session! 💫', 'চলুন আপনার অনুশীলন শুরু করি! 💫', '[]', 'Encouragement at session start'),

        -- UI messages
        ('ui_next_problem', 'ui', 'Next Problem', 'পরবর্তী সমস্যা', '[]', 'Button text for next problem'),
        ('ui_submit_answer', 'ui', 'Submit Answer', 'উত্তর জমা দিন', '[]', 'Button text for submitting answer'),
        ('ui_request_hint', 'ui', 'Request Hint', 'ইঙ্গিত চান', '[]', 'Button text for requesting hint')
    """)


def downgrade() -> None:
    """Remove message_templates table."""
    op.drop_index('idx_message_templates_key', table_name='message_templates')
    op.drop_index('idx_message_templates_category', table_name='message_templates')
    op.drop_table('message_templates')
