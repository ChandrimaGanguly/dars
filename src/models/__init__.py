"""
Database models for Dars AI Tutoring Platform.

This module contains all SQLAlchemy models representing the core entities:
- Student: User profiles with learning preferences
- Problem: Math problems from curated library
- Session: Daily practice sessions (5 problems)
- Response: Student answers to problems
- Streak: Daily habit tracking
- CostRecord: API cost tracking for business model validation
- MessageTemplate: Bilingual messages (Bengali + English) for all user-facing content
"""

from src.models.cost_record import CostRecord
from src.models.message_template import MessageCategory, MessageTemplate
from src.models.problem import Hint, Problem
from src.models.response import Response
from src.models.session import Session
from src.models.streak import Streak
from src.models.student import Student

__all__ = [
    "CostRecord",
    "Hint",
    "MessageCategory",
    "MessageTemplate",
    "Problem",
    "Response",
    "Session",
    "Streak",
    "Student",
]
