"""
Repository layer for Dars platform.

Provides data access objects (DAOs) for all database entities.
All repositories accept an AsyncSession and manage queries only;
transaction commit/rollback is the caller's responsibility.

Usage:
    from src.repositories import ProblemRepository, SessionRepository, ResponseRepository

    problem_repo = ProblemRepository()
    session_repo = SessionRepository()
    response_repo = ResponseRepository()
"""

from src.repositories.problem_repository import ProblemRepository
from src.repositories.response_repository import ResponseRepository
from src.repositories.session_repository import SessionRepository

__all__ = [
    "ProblemRepository",
    "ResponseRepository",
    "SessionRepository",
]
