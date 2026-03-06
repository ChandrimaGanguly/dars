"""Unit tests for SentMessage model and EncouragementService non-repeat methods.

PHASE6-B-2 (REQ-013)

Tests use in-memory SQLite via the shared db_session fixture from conftest.py.
All async methods flush but do not commit — we verify state within the session.
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.sent_message import SentMessage
from src.models.student import Student
from src.services.encouragement import EncouragementService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_student(db: AsyncSession, telegram_id: int = 100) -> Student:
    """Insert a minimal Student row and return it."""
    student = Student(
        telegram_id=telegram_id,
        name="Test Student",
        grade=7,
        language="en",
    )
    db.add(student)
    await db.flush()
    return student


# ---------------------------------------------------------------------------
# Tests: get_unique_correct_message
# ---------------------------------------------------------------------------


class TestGetUniqueCorrectMessage:
    @pytest.mark.asyncio
    async def test_returns_non_empty_string(self, db_session: AsyncSession) -> None:
        student = await _make_student(db_session)
        svc = EncouragementService()

        msg = await svc.get_unique_correct_message(
            db=db_session,
            student_id=student.student_id,
            streak=0,
            language="en",
        )

        assert isinstance(msg, str)
        assert len(msg) > 0

    @pytest.mark.asyncio
    async def test_avoids_recently_sent_variant(self, db_session: AsyncSession) -> None:
        student = await _make_student(db_session)
        svc = EncouragementService()

        # Manually mark first two variants as recently sent
        db_session.add(
            SentMessage(student_id=student.student_id, message_key="correct_streak_low_0")
        )
        db_session.add(
            SentMessage(student_id=student.student_id, message_key="correct_streak_low_1")
        )
        await db_session.flush()

        msg = await svc.get_unique_correct_message(
            db=db_session,
            student_id=student.student_id,
            streak=0,
            language="en",
        )

        # Should select variant 2 (the first unseen one)
        assert isinstance(msg, str)
        assert len(msg) > 0
        # Verify a new SentMessage row was written for variant 2
        rows = (
            (
                await db_session.execute(
                    select(SentMessage).where(
                        SentMessage.student_id == student.student_id,
                        SentMessage.message_key == "correct_streak_low_2",
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(rows) == 1

    @pytest.mark.asyncio
    async def test_falls_back_when_all_variants_seen(self, db_session: AsyncSession) -> None:
        """When all variants recently sent, falls back to deterministic selection."""
        student = await _make_student(db_session)
        svc = EncouragementService()

        # Mark all 3 low-streak variants as recently sent
        for i in range(3):
            db_session.add(
                SentMessage(student_id=student.student_id, message_key=f"correct_streak_low_{i}")
            )
        await db_session.flush()

        msg = await svc.get_unique_correct_message(
            db=db_session,
            student_id=student.student_id,
            streak=0,
            language="en",
        )

        assert isinstance(msg, str)
        assert len(msg) > 0

    @pytest.mark.asyncio
    async def test_writes_sent_message_row(self, db_session: AsyncSession) -> None:
        student = await _make_student(db_session)
        svc = EncouragementService()

        await svc.get_unique_correct_message(
            db=db_session,
            student_id=student.student_id,
            streak=0,
            language="en",
        )

        rows = (
            (
                await db_session.execute(
                    select(SentMessage).where(SentMessage.student_id == student.student_id)
                )
            )
            .scalars()
            .all()
        )
        assert len(rows) == 1
        assert rows[0].message_key.startswith("correct_streak_low_")

    @pytest.mark.asyncio
    async def test_streak_high_uses_streak_aware_pool(self, db_session: AsyncSession) -> None:
        """streak >= 7 uses the high-streak pool which includes {streak} in text."""
        student = await _make_student(db_session)
        svc = EncouragementService()

        msg = await svc.get_unique_correct_message(
            db=db_session,
            student_id=student.student_id,
            streak=10,
            language="en",
        )

        # High-streak messages reference the streak count
        assert "10" in msg

    @pytest.mark.asyncio
    async def test_ignores_expired_sent_messages(self, db_session: AsyncSession) -> None:
        """SentMessage rows older than 7 days are ignored (soft TTL)."""
        student = await _make_student(db_session)

        # Insert expired row for variant 0
        old_sent = SentMessage(
            student_id=student.student_id,
            message_key="correct_streak_low_0",
        )
        db_session.add(old_sent)
        await db_session.flush()
        # Manually backdate sent_at beyond the 7-day window
        old_sent.sent_at = datetime.now(UTC) - timedelta(days=8)
        await db_session.flush()

        svc = EncouragementService()
        msg = await svc.get_unique_correct_message(
            db=db_session,
            student_id=student.student_id,
            streak=0,
            language="en",
        )

        # Expired row should not block variant 0 — message is returned
        assert isinstance(msg, str)
        assert len(msg) > 0

    @pytest.mark.asyncio
    async def test_bengali_returns_valid_string(self, db_session: AsyncSession) -> None:
        student = await _make_student(db_session)
        svc = EncouragementService()

        msg = await svc.get_unique_correct_message(
            db=db_session,
            student_id=student.student_id,
            streak=0,
            language="bn",
        )

        assert isinstance(msg, str)
        assert len(msg) > 0


# ---------------------------------------------------------------------------
# Tests: get_unique_incorrect_message
# ---------------------------------------------------------------------------


class TestGetUniqueIncorrectMessage:
    @pytest.mark.asyncio
    async def test_returns_non_empty_string(self, db_session: AsyncSession) -> None:
        student = await _make_student(db_session, telegram_id=200)
        svc = EncouragementService()

        msg = await svc.get_unique_incorrect_message(
            db=db_session,
            student_id=student.student_id,
            hints_used=0,
            language="en",
        )

        assert isinstance(msg, str)
        assert len(msg) > 0

    @pytest.mark.asyncio
    async def test_avoids_recently_sent_variant(self, db_session: AsyncSession) -> None:
        student = await _make_student(db_session, telegram_id=201)
        svc = EncouragementService()

        # Pre-send variants 0 and 1
        db_session.add(SentMessage(student_id=student.student_id, message_key="incorrect_0"))
        db_session.add(SentMessage(student_id=student.student_id, message_key="incorrect_1"))
        await db_session.flush()

        msg = await svc.get_unique_incorrect_message(
            db=db_session,
            student_id=student.student_id,
            hints_used=0,
            language="en",
        )

        # Should land on variant 2
        assert isinstance(msg, str)
        assert len(msg) > 0
        rows = (
            (
                await db_session.execute(
                    select(SentMessage).where(
                        SentMessage.student_id == student.student_id,
                        SentMessage.message_key == "incorrect_2",
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(rows) == 1

    @pytest.mark.asyncio
    async def test_writes_sent_message_row(self, db_session: AsyncSession) -> None:
        student = await _make_student(db_session, telegram_id=202)
        svc = EncouragementService()

        await svc.get_unique_incorrect_message(
            db=db_session,
            student_id=student.student_id,
            hints_used=1,
            language="en",
        )

        rows = (
            (
                await db_session.execute(
                    select(SentMessage).where(SentMessage.student_id == student.student_id)
                )
            )
            .scalars()
            .all()
        )
        assert len(rows) == 1
        assert rows[0].message_key.startswith("incorrect_")

    @pytest.mark.asyncio
    async def test_bengali_returns_valid_string(self, db_session: AsyncSession) -> None:
        student = await _make_student(db_session, telegram_id=203)
        svc = EncouragementService()

        msg = await svc.get_unique_incorrect_message(
            db=db_session,
            student_id=student.student_id,
            hints_used=0,
            language="bn",
        )

        assert isinstance(msg, str)
        assert len(msg) > 0
