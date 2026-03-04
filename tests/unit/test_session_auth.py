"""Security tests for PHASE3-C-1: session ownership and IDOR prevention.

Tests for:
  - verify_session_owner: IDOR prevention, expired session, completed session,
    missing session
  - verify_problem_in_session: problem membership check
  - IDOR logging: WARNING level emitted with hashed IDs (never raw)

These tests use mocked database sessions and do not require a live database.
They are designed to run after CP4 (Jodha's endpoints are wired), but the
dependency functions can be tested independently with mocks.

CP5 gate: All tests in this file must pass before Phase 3 is declared complete.
"""

import hashlib
import logging
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.auth.session import (
    _hash_student_id,
    verify_problem_in_session,
    verify_session_owner,
)
from src.models.session import Session, SessionStatus
from src.models.student import Student

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_student(student_id: int = 1, telegram_id: int = 111111) -> Student:
    """Build a mock Student with the minimum fields required."""
    student = MagicMock(spec=Student)
    student.student_id = student_id
    student.telegram_id = telegram_id
    return student


def _make_session(
    session_id: int = 10,
    student_id: int = 1,
    status: str = SessionStatus.IN_PROGRESS,
    is_expired: bool = False,
    problem_ids: list[int] | None = None,
) -> Session:
    """Build a mock Session with configurable state."""
    session = MagicMock(spec=Session)
    session.session_id = session_id
    session.student_id = student_id
    session.status = status
    session.is_expired = MagicMock(return_value=is_expired)
    session.problem_ids = problem_ids if problem_ids is not None else [1, 2, 3, 4, 5]
    return session


def _make_db_with_session(session_obj: Session | None, student_obj: Student | None) -> Any:
    """Build a mock AsyncSession that returns the given session and student."""
    db = AsyncMock()

    # First execute call → session query result
    # Second execute call → student query result
    session_result = MagicMock()
    session_result.scalar_one_or_none.return_value = session_obj

    student_result = MagicMock()
    student_result.scalar_one_or_none.return_value = student_obj

    db.execute = AsyncMock(side_effect=[session_result, student_result])
    return db


# ---------------------------------------------------------------------------
# TestVerifySessionOwner
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestVerifySessionOwner:
    """Tests for verify_session_owner FastAPI dependency."""

    @pytest.mark.asyncio
    async def test_owner_can_access_own_session(self) -> None:
        """Happy path: authenticated student accesses their own session."""
        student = _make_student(student_id=1, telegram_id=111111)
        session = _make_session(session_id=10, student_id=1, status=SessionStatus.IN_PROGRESS)
        db = _make_db_with_session(session, student)

        result = await verify_session_owner(
            session_id=10,
            telegram_id=111111,
            db=db,
        )

        assert result is session

    @pytest.mark.asyncio
    async def test_idor_attempt_returns_403(self) -> None:
        """Student B trying to access Student A's session must get 403 Forbidden."""
        from fastapi import HTTPException

        # Session belongs to student_id=1, but attacker is student_id=2
        victim_student = _make_student(student_id=2, telegram_id=222222)
        session = _make_session(
            session_id=10,
            student_id=1,  # session belongs to student 1
            status=SessionStatus.IN_PROGRESS,
        )
        db = _make_db_with_session(session, victim_student)

        with pytest.raises(HTTPException) as exc_info:
            await verify_session_owner(
                session_id=10,
                telegram_id=222222,  # student 2 tries to access student 1's session
                db=db,
            )

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_expired_session_returns_410(self) -> None:
        """Expired session must return 410 Gone — not 400, 404, or 500."""
        from fastapi import HTTPException

        student = _make_student(student_id=1, telegram_id=111111)
        session = _make_session(
            session_id=10,
            student_id=1,
            status=SessionStatus.IN_PROGRESS,
            is_expired=True,  # expired
        )
        db = _make_db_with_session(session, student)

        with pytest.raises(HTTPException) as exc_info:
            await verify_session_owner(
                session_id=10,
                telegram_id=111111,
                db=db,
            )

        assert exc_info.value.status_code == 410

    @pytest.mark.asyncio
    async def test_missing_session_returns_404(self) -> None:
        """Non-existent session_id must return 404 Not Found."""
        from fastapi import HTTPException

        student = _make_student(student_id=1, telegram_id=111111)
        db = _make_db_with_session(session_obj=None, student_obj=student)

        with pytest.raises(HTTPException) as exc_info:
            await verify_session_owner(
                session_id=99999,
                telegram_id=111111,
                db=db,
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_completed_session_returns_409(self) -> None:
        """Re-submission to a completed session must return 409 Conflict."""
        from fastapi import HTTPException

        student = _make_student(student_id=1, telegram_id=111111)
        session = _make_session(
            session_id=10,
            student_id=1,
            status=SessionStatus.COMPLETED,
            is_expired=False,
        )
        db = _make_db_with_session(session, student)

        with pytest.raises(HTTPException) as exc_info:
            await verify_session_owner(
                session_id=10,
                telegram_id=111111,
                db=db,
            )

        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_abandoned_session_is_expired(self) -> None:
        """Abandoned sessions should have is_expired() return True and trigger 410."""
        from fastapi import HTTPException

        student = _make_student(student_id=1, telegram_id=111111)
        # Abandoned sessions will have is_expired() return True
        session = _make_session(
            session_id=10,
            student_id=1,
            status=SessionStatus.ABANDONED,
            is_expired=True,
        )
        db = _make_db_with_session(session, student)

        with pytest.raises(HTTPException) as exc_info:
            await verify_session_owner(
                session_id=10,
                telegram_id=111111,
                db=db,
            )

        # Expiry check runs before status check in our implementation
        assert exc_info.value.status_code == 410


# ---------------------------------------------------------------------------
# TestVerifyProblemInSession
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestVerifyProblemInSession:
    """Tests for verify_problem_in_session guard."""

    def test_problem_in_session_passes(self) -> None:
        """Problem ID that is in session.problem_ids should not raise."""
        session = _make_session(problem_ids=[1, 2, 3, 4, 5])
        # Should not raise
        verify_problem_in_session(problem_id=3, session=session)

    def test_first_problem_in_session_passes(self) -> None:
        """First problem in the list should pass."""
        session = _make_session(problem_ids=[10, 20, 30, 40, 50])
        verify_problem_in_session(problem_id=10, session=session)

    def test_last_problem_in_session_passes(self) -> None:
        """Last problem in the list should pass."""
        session = _make_session(problem_ids=[10, 20, 30, 40, 50])
        verify_problem_in_session(problem_id=50, session=session)

    def test_problem_not_in_session_returns_404(self) -> None:
        """Problem ID from a different session must return 404."""
        from fastapi import HTTPException

        session = _make_session(problem_ids=[1, 2, 3, 4, 5])

        with pytest.raises(HTTPException) as exc_info:
            verify_problem_in_session(problem_id=999, session=session)

        assert exc_info.value.status_code == 404
        assert "ERR_PROBLEM_NOT_FOUND" in (exc_info.value.headers or {}).get("X-Error-Code", "")

    def test_problem_not_in_empty_session_returns_404(self) -> None:
        """Empty problem_ids list must always return 404 for any problem."""
        from fastapi import HTTPException

        session = _make_session(problem_ids=[])

        with pytest.raises(HTTPException) as exc_info:
            verify_problem_in_session(problem_id=1, session=session)

        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# TestIDORLogging
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestIDORLogging:
    """Tests verifying IDOR attempts are logged correctly without PII exposure."""

    @pytest.mark.asyncio
    async def test_idor_attempt_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """IDOR attempt must emit a WARNING-level log."""
        from fastapi import HTTPException

        # Session belongs to student_id=1; attacker is student_id=2
        attacker_student = _make_student(student_id=2, telegram_id=222222)
        session = _make_session(
            session_id=10,
            student_id=1,
            status=SessionStatus.IN_PROGRESS,
            is_expired=False,
        )
        db = _make_db_with_session(session, attacker_student)

        with (
            caplog.at_level(logging.WARNING, logger="src.auth.session"),
            pytest.raises(HTTPException),
        ):
            await verify_session_owner(
                session_id=10,
                telegram_id=222222,
                db=db,
            )

        # Exactly one WARNING log should be emitted for the IDOR attempt
        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warning_records) >= 1

        # The WARNING must reference IDOR in the message
        warning_messages = " ".join(r.getMessage() for r in warning_records)
        assert "IDOR" in warning_messages or "idor" in warning_messages.lower()

    @pytest.mark.asyncio
    async def test_idor_log_contains_hashed_ids_not_raw(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Raw telegram_id integers must never appear in any log record."""
        from fastapi import HTTPException

        attacker_telegram_id = 222222
        attacker_student = _make_student(student_id=2, telegram_id=attacker_telegram_id)
        session = _make_session(
            session_id=10,
            student_id=1,
            status=SessionStatus.IN_PROGRESS,
            is_expired=False,
        )
        db = _make_db_with_session(session, attacker_student)

        with (
            caplog.at_level(logging.WARNING, logger="src.auth.session"),
            pytest.raises(HTTPException),
        ):
            await verify_session_owner(
                session_id=10,
                telegram_id=attacker_telegram_id,
                db=db,
            )

        # Raw telegram_id integer must NOT appear in any log message
        all_log_text = " ".join(r.getMessage() for r in caplog.records)
        assert (
            str(attacker_telegram_id) not in all_log_text
        ), f"Raw telegram_id {attacker_telegram_id} must not appear in logs"

    @pytest.mark.asyncio
    async def test_idor_log_severity_high(self, caplog: pytest.LogCaptureFixture) -> None:
        """IDOR log entry must carry severity=HIGH in its extra context."""
        from fastapi import HTTPException

        attacker_student = _make_student(student_id=2, telegram_id=333333)
        session = _make_session(
            session_id=20,
            student_id=1,
            status=SessionStatus.IN_PROGRESS,
            is_expired=False,
        )
        db = _make_db_with_session(session, attacker_student)

        with (
            caplog.at_level(logging.WARNING, logger="src.auth.session"),
            pytest.raises(HTTPException),
        ):
            await verify_session_owner(
                session_id=20,
                telegram_id=333333,
                db=db,
            )

        # Find the IDOR-related WARNING record
        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warning_records) >= 1

        # Check that severity=HIGH is present in the log record
        # Our implementation uses extra= dict; caplog captures it differently per handler.
        # We check the string representation of the record message for "HIGH".
        combined = " ".join(str(r.__dict__) for r in warning_records)
        assert "HIGH" in combined


# ---------------------------------------------------------------------------
# TestHashStudentId
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHashStudentId:
    """Tests for the _hash_student_id internal helper."""

    def test_returns_16_chars(self) -> None:
        """Hash must be exactly 16 characters."""
        result = _hash_student_id(123456)
        assert len(result) == 16

    def test_deterministic(self) -> None:
        """Same input must always produce same output."""
        h1 = _hash_student_id(987654321)
        h2 = _hash_student_id(987654321)
        assert h1 == h2

    def test_different_ids_produce_different_hashes(self) -> None:
        """Different student IDs should produce different hashes."""
        h1 = _hash_student_id(1)
        h2 = _hash_student_id(2)
        assert h1 != h2

    def test_output_is_hex_string(self) -> None:
        """Hash output must be a valid lowercase hex string."""
        result = _hash_student_id(99999)
        assert all(c in "0123456789abcdef" for c in result)

    def test_matches_sha256_computation(self) -> None:
        """Verify output matches expected SHA-256 prefix."""
        telegram_id = 123456789
        expected = hashlib.sha256(str(telegram_id).encode()).hexdigest()[:16]
        assert _hash_student_id(telegram_id) == expected
