"""Authentication middleware for the Dars API.

This module provides:
- Telegram webhook authentication (Bearer token)
- Admin authentication (X-Admin-ID header, Phase 0: hardcoded IDs)
- Student authentication (X-Student-ID header, Phase 0: simple validation)
- Session ownership verification (IDOR prevention, PHASE3-C-1)
"""

from src.auth.admin import verify_admin
from src.auth.session import verify_problem_in_session, verify_session_owner
from src.auth.student import verify_student
from src.auth.telegram import verify_telegram_webhook

__all__ = [
    "verify_admin",
    "verify_problem_in_session",
    "verify_session_owner",
    "verify_student",
    "verify_telegram_webhook",
]
