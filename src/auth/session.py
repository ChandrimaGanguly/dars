"""Session ownership verification FastAPI dependencies.

Prevents IDOR attacks on practice endpoints by verifying the authenticated
student is the owner of the session they are trying to access.

PHASE3-C-1: verify_session_owner, verify_problem_in_session

Security Model:
- verify_session_owner: chains off verify_student (already-verified telegram_id).
  Loads the Session from DB and compares session.student_id against the
  authenticated student's student_id. Mismatches are logged at WARNING with
  SHA-256 hashed IDs — raw telegram_ids are never logged.
- verify_problem_in_session: checks that the problem_id from the URL path is
  present in session.problem_ids (the JSON list of 5 problem IDs assigned to
  this session). Prevents accessing problems that belong to other sessions.

HTTP status codes returned:
  404 — Session not found in database
  410 — Session expired (is_expired() == True) — use 410 Gone per REQ-007
  409 — Session already completed (re-submission blocked)
  403 — IDOR attempt: session.student_id != authenticated student's student_id
"""

import hashlib
import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.student import verify_student
from src.database import get_session
from src.models.session import Session, SessionStatus
from src.models.student import Student

logger = logging.getLogger(__name__)


def _hash_student_id(student_id: int) -> str:
    """Return a 16-char SHA-256 prefix of student_id for safe logging.

    Ensures raw student IDs (telegram_ids or internal IDs) are never
    written to log output. Use this function everywhere an ID appears
    in a log message.

    Args:
        student_id: Integer student identifier (telegram_id or student_id).

    Returns:
        16-character hex prefix of SHA-256(str(student_id)).

    Example:
        >>> _hash_student_id(123456789)
        'ff6b3e9a0c4d1234'  # example output
    """
    return hashlib.sha256(str(student_id).encode()).hexdigest()[:16]


async def _get_student_by_telegram_id(
    db: AsyncSession,
    telegram_id: int,
) -> Student:
    """Load Student row by telegram_id from the database.

    Args:
        db: Async database session.
        telegram_id: Telegram user ID (from verify_student dependency).

    Returns:
        Student ORM object.

    Raises:
        HTTPException 404: If no student row exists for this telegram_id.
    """
    result = await db.execute(select(Student).where(Student.telegram_id == telegram_id))
    student = result.scalar_one_or_none()
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )
    return student


async def verify_session_owner(
    session_id: int,
    telegram_id: Annotated[int, Depends(verify_student)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> Session:
    """FastAPI dependency: verify the authenticated student owns this session.

    This dependency chains off verify_student to receive the already-verified
    telegram_id. It then:
      1. Loads the Session by session_id.
      2. Resolves the Student row to get the internal student_id (PK).
      3. Compares session.student_id against the authenticated student's
         student_id to detect IDOR attempts.
      4. Checks session expiry and completion status.

    Prevents CWE-639 (Insecure Direct Object Reference): a student cannot
    submit answers into another student's session by guessing a session_id.

    IDOR attempts are logged at WARNING level with hashed IDs (never raw).

    Args:
        session_id: Session ID from the request body (path param via Depends
                    caller; the endpoint extracts it before invoking this dep).
        telegram_id: Verified telegram_id from verify_student dependency.
        db: Async database session from get_session dependency.

    Returns:
        The Session ORM object if all checks pass.

    Raises:
        HTTPException 404: Session not found in database.
        HTTPException 403: IDOR attempt — session belongs to a different student.
        HTTPException 410: Session has expired (is_expired() returned True).
        HTTPException 409: Session already completed (re-submission blocked).
    """
    # Load session from database
    result = await db.execute(select(Session).where(Session.session_id == session_id))
    session = result.scalar_one_or_none()

    if session is None:
        logger.info(
            "Session not found",
            extra={
                "event": "practice.security.session_not_found",
                "session_id": session_id,
                "student_hash": _hash_student_id(telegram_id),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Resolve the authenticated student's internal student_id (PK)
    student = await _get_student_by_telegram_id(db, telegram_id)

    # IDOR check: compare internal student_id, not telegram_id
    if session.student_id != student.student_id:
        # Log IDOR attempt at WARNING with hashed IDs — never raw IDs
        logger.warning(
            "IDOR attempt: student tried to access another student's session",
            extra={
                "event": "practice.security.idor_attempt",
                "attacker_hash": _hash_student_id(telegram_id),
                "target_session_id": session_id,
                "target_owner_hash": _hash_student_id(session.student_id),
                "severity": "HIGH",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your session",
        )

    # Check session expiry — return 410 Gone, not 400 or 404
    if session.is_expired():
        logger.info(
            "Expired session access attempt",
            extra={
                "event": "practice.security.session_expired",
                "session_id": session_id,
                "student_hash": _hash_student_id(telegram_id),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Session has expired",
        )

    # Check session completion — block re-submission
    if session.status == SessionStatus.COMPLETED:
        logger.info(
            "Attempt to submit to already-completed session",
            extra={
                "event": "practice.security.session_already_completed",
                "session_id": session_id,
                "student_hash": _hash_student_id(telegram_id),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session already completed",
        )

    return session


def verify_problem_in_session(
    problem_id: int,
    session: Session,
) -> None:
    """Verify problem_id is part of this session's assigned problem set.

    Called after verify_session_owner to ensure the student is answering a
    problem that was actually assigned to their session. Prevents accessing
    arbitrary problems from other sessions by guessing problem IDs.

    Args:
        problem_id: Problem ID from the URL path.
        session: Verified Session object from verify_session_owner.

    Raises:
        HTTPException 404: problem_id is not in session.problem_ids.
    """
    if problem_id not in session.problem_ids:
        logger.warning(
            "Problem not in session — possible IDOR on problem resource",
            extra={
                "event": "practice.security.problem_not_in_session",
                "problem_id": problem_id,
                "session_id": session.session_id,
                "session_problem_ids": session.problem_ids,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(f"Problem {problem_id} is not part of session {session.session_id}"),
            headers={"X-Error-Code": "ERR_PROBLEM_NOT_FOUND"},
        )
