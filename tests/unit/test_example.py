"""Example unit tests for Dars project.

This file demonstrates the test structure. These tests should be replaced
with actual tests for the streak system, problem selector, etc.
"""

import pytest


class TestStreakCalculation:
    """Tests for streak calculation logic."""

    def test_streak_increments_on_consecutive_days(self) -> None:
        """Streak should increment when student practices on consecutive days."""
        # TODO: Implement when streak logic exists
        assert True

    def test_streak_resets_on_missed_day(self) -> None:
        """Streak should reset to 0 when student misses a day."""
        # TODO: Implement when streak logic exists
        assert True

    def test_longest_streak_updated(self) -> None:
        """Longest streak should update if current streak exceeds it."""
        # TODO: Implement when streak logic exists
        assert True


class TestProblemSelector:
    """Tests for problem selection logic."""

    def test_selects_five_problems_per_day(self) -> None:
        """Should return exactly 5 problems for daily practice."""
        # TODO: Implement when problem selector exists
        assert True

    def test_respects_grade_level(self) -> None:
        """Should only select problems for student's grade."""
        # TODO: Implement when problem selector exists
        assert True

    def test_adaptive_difficulty(self) -> None:
        """Should adjust difficulty based on student performance."""
        # TODO: Implement when problem selector exists
        assert True


class TestAnswerEvaluation:
    """Tests for answer evaluation logic."""

    def test_exact_match_for_numeric_answers(self) -> None:
        """Numeric answers should match exactly or within tolerance."""
        # TODO: Implement when evaluator exists
        assert True

    def test_tolerance_for_rounding(self) -> None:
        """Should allow for reasonable rounding differences."""
        # TODO: Implement when evaluator exists
        assert True


@pytest.mark.unit
class TestMathOperations:
    """Example unit tests showing pytest markers."""

    def test_addition(self) -> None:
        """Test that addition works correctly."""
        assert 2 + 2 == 4

    def test_division_by_zero(self) -> None:
        """Test that division by zero raises error."""
        with pytest.raises(ZeroDivisionError):
            _ = 1 / 0
