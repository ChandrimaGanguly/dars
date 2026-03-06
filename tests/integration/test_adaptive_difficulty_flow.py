"""Integration tests for the adaptive difficulty service layer.

Verifies end-to-end flows: difficulty stays the same on a single strong session,
upgrades after two consecutive strong sessions, and downgrades on a weak session.
Uses an in-memory SQLite database — no external services required.

These tests call the service/repository layer directly (not via HTTP) to avoid
event-loop isolation issues with Starlette TestClient + async SQLAlchemy.

PHASE4-C-1
"""

from typing import Any

import pytest

from src.models.student import Student
from src.services.adaptive_difficulty import AdaptiveDifficultyService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TELEGRAM_ID_BASE = 700_000_001  # distinct range from other integration test files


async def _create_student(db: Any, telegram_id: int, difficulty_level: int = 1) -> Student:
    """Create a Student row in the test database with given starting difficulty.

    Args:
        db: Async SQLAlchemy session.
        telegram_id: Unique Telegram ID for this student.
        difficulty_level: Starting difficulty level (1=easy, 2=medium, 3=hard).

    Returns:
        Committed and refreshed Student instance.
    """
    student = Student(
        telegram_id=telegram_id,
        name="DifficultyTestStudent",
        grade=7,
        language="en",
        difficulty_level=difficulty_level,
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestAdaptiveDifficultyNoUpgradeFirstSession:
    """Verify no upgrade happens on a single strong session without prior history."""

    async def test_first_strong_session_no_change(self, db_session: Any) -> None:
        """≥4/5 correct in first session should NOT upgrade (needs two consecutive)."""
        student = await _create_student(db_session, _TELEGRAM_ID_BASE, difficulty_level=1)
        student_id = student.student_id

        svc = AdaptiveDifficultyService()
        _, new_level = await svc.update_difficulty(
            db_session,
            student,
            session_results=[True, True, True, True, True],  # 5/5 — perfect
            prev_session_results=None,  # no previous session
        )
        await db_session.commit()

        # Reload from DB to confirm no change was written
        await db_session.refresh(student)
        assert new_level == 1
        assert student.difficulty_level == 1
        assert student.student_id == student_id

    async def test_average_session_no_change(self, db_session: Any) -> None:
        """3/5 correct should leave difficulty unchanged."""
        student = await _create_student(db_session, _TELEGRAM_ID_BASE + 1, difficulty_level=2)

        svc = AdaptiveDifficultyService()
        _, new_level = await svc.update_difficulty(
            db_session,
            student,
            session_results=[True, True, True, False, False],  # 3/5
        )
        await db_session.commit()
        await db_session.refresh(student)

        assert new_level == 2
        assert student.difficulty_level == 2


@pytest.mark.integration
class TestAdaptiveDifficultyUpgradeFlow:
    """Verify upgrade after two consecutive strong sessions."""

    async def test_two_strong_sessions_upgrade_level_1_to_2(self, db_session: Any) -> None:
        """≥4/5 in current AND previous session upgrades level 1 → 2."""
        student = await _create_student(db_session, _TELEGRAM_ID_BASE + 10, difficulty_level=1)

        svc = AdaptiveDifficultyService()
        _, new_level = await svc.update_difficulty(
            db_session,
            student,
            session_results=[True, True, True, True, False],  # 4/5 current
            prev_session_results=[True, True, True, True, True],  # 5/5 previous
        )
        await db_session.commit()
        await db_session.refresh(student)

        assert new_level == 2
        assert student.difficulty_level == 2

    async def test_two_strong_sessions_upgrade_level_2_to_3(self, db_session: Any) -> None:
        """≥4/5 in both sessions upgrades level 2 → 3."""
        student = await _create_student(db_session, _TELEGRAM_ID_BASE + 11, difficulty_level=2)

        svc = AdaptiveDifficultyService()
        _, new_level = await svc.update_difficulty(
            db_session,
            student,
            session_results=[True, True, True, True, True],  # 5/5
            prev_session_results=[True, True, True, True, False],  # 4/5
        )
        await db_session.commit()
        await db_session.refresh(student)

        assert new_level == 3
        assert student.difficulty_level == 3

    async def test_capped_at_max_level_3(self, db_session: Any) -> None:
        """Student already at level 3 cannot upgrade further."""
        student = await _create_student(db_session, _TELEGRAM_ID_BASE + 12, difficulty_level=3)

        svc = AdaptiveDifficultyService()
        _, new_level = await svc.update_difficulty(
            db_session,
            student,
            session_results=[True, True, True, True, True],
            prev_session_results=[True, True, True, True, True],
        )
        await db_session.commit()
        await db_session.refresh(student)

        assert new_level == 3
        assert student.difficulty_level == 3


@pytest.mark.integration
class TestAdaptiveDifficultyDowngradeFlow:
    """Verify downgrade on weak session performance (≤1/5 correct)."""

    async def test_one_correct_downgrades_level_2_to_1(self, db_session: Any) -> None:
        """1/5 correct downgrades level 2 → 1."""
        student = await _create_student(db_session, _TELEGRAM_ID_BASE + 20, difficulty_level=2)

        svc = AdaptiveDifficultyService()
        _, new_level = await svc.update_difficulty(
            db_session,
            student,
            session_results=[True, False, False, False, False],  # 1/5
        )
        await db_session.commit()
        await db_session.refresh(student)

        assert new_level == 1
        assert student.difficulty_level == 1

    async def test_zero_correct_downgrades_level_3_to_2(self, db_session: Any) -> None:
        """0/5 correct downgrades level 3 → 2."""
        student = await _create_student(db_session, _TELEGRAM_ID_BASE + 21, difficulty_level=3)

        svc = AdaptiveDifficultyService()
        _, new_level = await svc.update_difficulty(
            db_session,
            student,
            session_results=[False, False, False, False, False],  # 0/5
        )
        await db_session.commit()
        await db_session.refresh(student)

        assert new_level == 2
        assert student.difficulty_level == 2

    async def test_clamped_at_min_level_1(self, db_session: Any) -> None:
        """Student at level 1 cannot downgrade below 1."""
        student = await _create_student(db_session, _TELEGRAM_ID_BASE + 22, difficulty_level=1)

        svc = AdaptiveDifficultyService()
        _, new_level = await svc.update_difficulty(
            db_session,
            student,
            session_results=[False, False, False, False, False],  # 0/5
        )
        await db_session.commit()
        await db_session.refresh(student)

        assert new_level == 1
        assert student.difficulty_level == 1

    async def test_two_correct_is_not_downgrade(self, db_session: Any) -> None:
        """2/5 correct is above the ≤1 downgrade threshold — no change."""
        student = await _create_student(db_session, _TELEGRAM_ID_BASE + 23, difficulty_level=2)

        svc = AdaptiveDifficultyService()
        _, new_level = await svc.update_difficulty(
            db_session,
            student,
            session_results=[True, True, False, False, False],  # 2/5
        )
        await db_session.commit()
        await db_session.refresh(student)

        assert new_level == 2
        assert student.difficulty_level == 2
