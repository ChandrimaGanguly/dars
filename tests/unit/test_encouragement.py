"""Unit tests for EncouragementService.

Covers REQ-009 (streak tracking display) and REQ-012 (milestone detection).
All tests are pure-Python — no database, no external services.
"""

import pytest

from src.services.encouragement import EncouragementService


@pytest.mark.unit
class TestGetCorrectMessage:
    """Tests for EncouragementService.get_correct_message."""

    def test_returns_non_empty_en(self) -> None:
        """English correct message must be a non-empty string."""
        svc = EncouragementService()
        result = svc.get_correct_message(streak=0, language="en")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_returns_non_empty_bn(self) -> None:
        """Bengali correct message must be a non-empty string."""
        svc = EncouragementService()
        result = svc.get_correct_message(streak=0, language="bn")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generic_message_when_streak_below_7(self) -> None:
        """Streaks below 7 should return a generic (no streak count) message."""
        svc = EncouragementService()
        result = svc.get_correct_message(streak=3, language="en")
        # Generic messages don't embed a streak number
        assert "3" not in result

    def test_streak_aware_message_at_exactly_7(self) -> None:
        """Streak of 7 should embed the streak count in the message."""
        svc = EncouragementService()
        result = svc.get_correct_message(streak=7, language="en")
        assert "7" in result

    def test_streak_aware_message_above_7_en(self) -> None:
        """Streak > 7 should embed the streak count in English."""
        svc = EncouragementService()
        result = svc.get_correct_message(streak=14, language="en")
        assert "14" in result

    def test_streak_aware_message_above_7_bn(self) -> None:
        """Streak > 7 should embed the streak count in Bengali."""
        svc = EncouragementService()
        result = svc.get_correct_message(streak=14, language="bn")
        assert "14" in result

    def test_unknown_language_falls_back_to_en(self) -> None:
        """Unknown language codes fall back to English."""
        svc = EncouragementService()
        result = svc.get_correct_message(streak=0, language="fr")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_deterministic_across_calls(self) -> None:
        """Same inputs always return the same message."""
        svc = EncouragementService()
        r1 = svc.get_correct_message(streak=5, language="en")
        r2 = svc.get_correct_message(streak=5, language="en")
        assert r1 == r2

    def test_different_streaks_cycle_through_variants(self) -> None:
        """Different streak values should produce at least 2 distinct messages."""
        svc = EncouragementService()
        messages = {svc.get_correct_message(streak=i, language="en") for i in range(6)}
        assert len(messages) > 1


@pytest.mark.unit
class TestGetIncorrectMessage:
    """Tests for EncouragementService.get_incorrect_message."""

    def test_returns_non_empty_en(self) -> None:
        """English incorrect message must be a non-empty string."""
        svc = EncouragementService()
        result = svc.get_incorrect_message(hints_used=0, language="en")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_returns_non_empty_bn(self) -> None:
        """Bengali incorrect message must be a non-empty string."""
        svc = EncouragementService()
        result = svc.get_incorrect_message(hints_used=0, language="bn")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_all_hint_counts_return_valid_messages(self) -> None:
        """All hints_used values 0-3 return non-empty strings."""
        svc = EncouragementService()
        for hints in range(4):
            result = svc.get_incorrect_message(hints_used=hints, language="en")
            assert isinstance(result, str)
            assert len(result) > 0, f"Empty message for hints_used={hints}"

    def test_unknown_language_falls_back_to_en(self) -> None:
        """Unknown language codes fall back to English."""
        svc = EncouragementService()
        result = svc.get_incorrect_message(hints_used=1, language="de")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_different_hint_counts_cycle_variants(self) -> None:
        """Different hints_used values produce at least 2 distinct messages."""
        svc = EncouragementService()
        messages = {svc.get_incorrect_message(hints_used=i, language="en") for i in range(3)}
        assert len(messages) > 1


@pytest.mark.unit
class TestGetSessionStartMessage:
    """Tests for EncouragementService.get_session_start_message."""

    def test_returns_non_empty_en(self) -> None:
        """English session-start message must be a non-empty string."""
        svc = EncouragementService()
        result = svc.get_session_start_message(grade=7, topics=["Fractions"], language="en")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_returns_non_empty_bn(self) -> None:
        """Bengali session-start message must be a non-empty string."""
        svc = EncouragementService()
        result = svc.get_session_start_message(grade=7, topics=["Fractions"], language="bn")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_grade_embedded_in_message(self) -> None:
        """Grade number should appear in the message."""
        svc = EncouragementService()
        result = svc.get_session_start_message(grade=8, topics=["Algebra"], language="en")
        assert "8" in result

    def test_topics_embedded_in_message(self) -> None:
        """Topic names should appear in the message."""
        svc = EncouragementService()
        result = svc.get_session_start_message(
            grade=7, topics=["Profit & Loss", "Fractions"], language="en"
        )
        assert "Profit & Loss" in result
        assert "Fractions" in result

    def test_empty_topics_uses_fallback(self) -> None:
        """Empty topic list should not crash and uses fallback text."""
        svc = EncouragementService()
        result = svc.get_session_start_message(grade=6, topics=[], language="en")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_unknown_language_falls_back_to_en(self) -> None:
        """Unknown language falls back to English."""
        svc = EncouragementService()
        result = svc.get_session_start_message(grade=7, topics=["Decimals"], language="hi")
        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.unit
class TestGetMilestoneMessage:
    """Tests for EncouragementService.get_milestone_message."""

    @pytest.mark.parametrize("days", [7, 14, 30])
    def test_known_milestone_returns_non_empty_en(self, days: int) -> None:
        """Known milestone should return non-empty English string."""
        svc = EncouragementService()
        result = svc.get_milestone_message(milestone_days=days, language="en")
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("days", [7, 14, 30])
    def test_known_milestone_returns_non_empty_bn(self, days: int) -> None:
        """Known milestone should return non-empty Bengali string."""
        svc = EncouragementService()
        result = svc.get_milestone_message(milestone_days=days, language="bn")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_milestone_7_en_content(self) -> None:
        """7-day milestone English message should reference 7."""
        svc = EncouragementService()
        result = svc.get_milestone_message(milestone_days=7, language="en")
        assert "7" in result

    def test_milestone_14_en_content(self) -> None:
        """14-day milestone English message should reference 14."""
        svc = EncouragementService()
        result = svc.get_milestone_message(milestone_days=14, language="en")
        assert "14" in result

    def test_milestone_30_en_content(self) -> None:
        """30-day milestone English message should reference 30."""
        svc = EncouragementService()
        result = svc.get_milestone_message(milestone_days=30, language="en")
        assert "30" in result

    def test_unknown_milestone_does_not_crash(self) -> None:
        """Unknown milestone value should return a non-empty fallback string."""
        svc = EncouragementService()
        result = svc.get_milestone_message(milestone_days=100, language="en")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_unknown_language_falls_back_to_en(self) -> None:
        """Unknown language for milestone falls back to English."""
        svc = EncouragementService()
        result = svc.get_milestone_message(milestone_days=7, language="zh")
        assert isinstance(result, str)
        assert len(result) > 0
