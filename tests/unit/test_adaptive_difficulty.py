"""Unit tests for AdaptiveDifficultyService.

Covers REQ-004: adaptive difficulty — upgrade/downgrade/clamp/no-change logic.
Uses AsyncMock for the database session and MagicMock for the Student model.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.adaptive_difficulty import AdaptiveDifficultyService


def _make_student(difficulty_level: int = 1) -> MagicMock:
    """Create a mock Student with a configurable difficulty_level.

    StudentRepository.set_difficulty() mutates student.difficulty_level in
    place, so we need an object with a writable attribute.
    """
    student = MagicMock()
    student.difficulty_level = difficulty_level
    return student


def _make_db() -> AsyncMock:
    """Create a minimal async database session mock."""
    db = AsyncMock()
    # add() and flush() are called by StudentRepository.set_difficulty
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


@pytest.mark.unit
class TestAdaptiveDifficultyUpgrade:
    """Tests for difficulty upgrade logic (2 consecutive strong sessions)."""

    @pytest.mark.asyncio
    async def test_upgrade_when_two_consecutive_strong_sessions(self) -> None:
        """Should upgrade from level 1 → 2 on two consecutive ≥4/5 sessions."""
        svc = AdaptiveDifficultyService()
        db = _make_db()
        student = _make_student(difficulty_level=1)

        with patch("src.services.adaptive_difficulty._student_repo") as mock_repo:
            mock_repo.set_difficulty = AsyncMock(
                side_effect=lambda _db, s, level: setattr(s, "difficulty_level", level)
            )
            _, new_level = await svc.update_difficulty(
                db,
                student,
                session_results=[True, True, True, True, False],  # 4/5
                prev_session_results=[True, True, True, True, True],  # 5/5
            )

        assert new_level == 2

    @pytest.mark.asyncio
    async def test_upgrade_from_level_2_to_3(self) -> None:
        """Should upgrade from level 2 → 3 on two consecutive ≥4/5 sessions."""
        svc = AdaptiveDifficultyService()
        db = _make_db()
        student = _make_student(difficulty_level=2)

        with patch("src.services.adaptive_difficulty._student_repo") as mock_repo:
            mock_repo.set_difficulty = AsyncMock(
                side_effect=lambda _db, s, level: setattr(s, "difficulty_level", level)
            )
            _, new_level = await svc.update_difficulty(
                db,
                student,
                session_results=[True, True, True, True, True],  # 5/5
                prev_session_results=[True, True, True, True, False],  # 4/5
            )

        assert new_level == 3

    @pytest.mark.asyncio
    async def test_no_upgrade_on_single_strong_session(self) -> None:
        """Should NOT upgrade on only one strong session (prev_session_results=None)."""
        svc = AdaptiveDifficultyService()
        db = _make_db()
        student = _make_student(difficulty_level=1)

        _, new_level = await svc.update_difficulty(
            db,
            student,
            session_results=[True, True, True, True, True],  # 5/5
            prev_session_results=None,
        )

        assert new_level == 1  # No change — prev session unknown

    @pytest.mark.asyncio
    async def test_no_upgrade_when_prev_session_was_weak(self) -> None:
        """Should NOT upgrade if previous session had <4 correct."""
        svc = AdaptiveDifficultyService()
        db = _make_db()
        student = _make_student(difficulty_level=2)

        _, new_level = await svc.update_difficulty(
            db,
            student,
            session_results=[True, True, True, True, True],  # 5/5
            prev_session_results=[True, True, False, False, False],  # 2/5 — weak
        )

        assert new_level == 2  # No change

    @pytest.mark.asyncio
    async def test_no_upgrade_above_max_level(self) -> None:
        """Should not upgrade above level 3 (clamping)."""
        svc = AdaptiveDifficultyService()
        db = _make_db()
        student = _make_student(difficulty_level=3)

        with patch("src.services.adaptive_difficulty._student_repo") as mock_repo:
            mock_repo.set_difficulty = AsyncMock(
                side_effect=lambda _db, s, level: setattr(s, "difficulty_level", level)
            )
            _, new_level = await svc.update_difficulty(
                db,
                student,
                session_results=[True, True, True, True, True],
                prev_session_results=[True, True, True, True, True],
            )

        # Already at max — no change, set_difficulty never called
        assert new_level == 3
        mock_repo.set_difficulty.assert_not_called()


@pytest.mark.unit
class TestAdaptiveDifficultyDowngrade:
    """Tests for difficulty downgrade logic (≤1/5 correct)."""

    @pytest.mark.asyncio
    async def test_downgrade_when_one_correct(self) -> None:
        """Should downgrade when student gets exactly 1/5 correct."""
        svc = AdaptiveDifficultyService()
        db = _make_db()
        student = _make_student(difficulty_level=2)

        with patch("src.services.adaptive_difficulty._student_repo") as mock_repo:
            mock_repo.set_difficulty = AsyncMock(
                side_effect=lambda _db, s, level: setattr(s, "difficulty_level", level)
            )
            _, new_level = await svc.update_difficulty(
                db,
                student,
                session_results=[True, False, False, False, False],  # 1/5
            )

        assert new_level == 1

    @pytest.mark.asyncio
    async def test_downgrade_when_zero_correct(self) -> None:
        """Should downgrade when student gets 0/5 correct."""
        svc = AdaptiveDifficultyService()
        db = _make_db()
        student = _make_student(difficulty_level=3)

        with patch("src.services.adaptive_difficulty._student_repo") as mock_repo:
            mock_repo.set_difficulty = AsyncMock(
                side_effect=lambda _db, s, level: setattr(s, "difficulty_level", level)
            )
            _, new_level = await svc.update_difficulty(
                db,
                student,
                session_results=[False, False, False, False, False],  # 0/5
            )

        assert new_level == 2

    @pytest.mark.asyncio
    async def test_no_downgrade_below_min_level(self) -> None:
        """Should not downgrade below level 1 (clamping)."""
        svc = AdaptiveDifficultyService()
        db = _make_db()
        student = _make_student(difficulty_level=1)

        with patch("src.services.adaptive_difficulty._student_repo") as mock_repo:
            mock_repo.set_difficulty = AsyncMock(
                side_effect=lambda _db, s, level: setattr(s, "difficulty_level", level)
            )
            _, new_level = await svc.update_difficulty(
                db,
                student,
                session_results=[False, False, False, False, False],  # 0/5
            )

        assert new_level == 1
        mock_repo.set_difficulty.assert_not_called()


@pytest.mark.unit
class TestAdaptiveDifficultyNoChange:
    """Tests for the no-change case (2-3 correct out of 5)."""

    @pytest.mark.asyncio
    async def test_no_change_on_average_performance(self) -> None:
        """Should not change level for 2-3 correct answers."""
        svc = AdaptiveDifficultyService()
        db = _make_db()
        student = _make_student(difficulty_level=2)

        with patch("src.services.adaptive_difficulty._student_repo") as mock_repo:
            mock_repo.set_difficulty = AsyncMock()
            _, new_level = await svc.update_difficulty(
                db,
                student,
                session_results=[True, True, True, False, False],  # 3/5
            )

        assert new_level == 2
        mock_repo.set_difficulty.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_change_on_exactly_two_correct(self) -> None:
        """2/5 correct is above downgrade threshold (≤1) — no change."""
        svc = AdaptiveDifficultyService()
        db = _make_db()
        student = _make_student(difficulty_level=2)

        with patch("src.services.adaptive_difficulty._student_repo") as mock_repo:
            mock_repo.set_difficulty = AsyncMock()
            _, new_level = await svc.update_difficulty(
                db,
                student,
                session_results=[True, True, False, False, False],  # 2/5
            )

        assert new_level == 2
        mock_repo.set_difficulty.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_student_and_level(self) -> None:
        """update_difficulty must return (Student, int) tuple."""
        svc = AdaptiveDifficultyService()
        db = _make_db()
        student = _make_student(difficulty_level=1)

        result = await svc.update_difficulty(
            db,
            student,
            session_results=[True, True, True, False, False],
        )

        assert isinstance(result, tuple)
        assert len(result) == 2
        returned_student, level = result
        assert returned_student is student
        assert isinstance(level, int)
