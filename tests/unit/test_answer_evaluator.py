"""Unit tests for the AnswerEvaluator service.

Tests numeric tolerance, multiple-choice evaluation, input normalisation,
confidence levels, and bilingual feedback messages.

Coverage target: ≥80%

PHASE3-B-2.7
"""

from unittest.mock import MagicMock

import pytest

from src.services.answer_evaluator import AnswerEvaluator


def _make_problem(
    answer: str = "40",
    answer_type: str = "numeric",
    tolerance: float | None = None,
) -> MagicMock:
    """Create a mock Problem with configurable answer fields.

    Args:
        answer: The correct answer string.
        answer_type: "numeric" or "multiple_choice".
        tolerance: Optional custom tolerance percent (defaults to 5.0).

    Returns:
        MagicMock that mimics the Problem model interface.
    """
    problem = MagicMock()
    problem.answer = answer
    problem.answer_type = answer_type
    if tolerance is not None:
        problem.acceptable_tolerance_percent = tolerance
    else:
        # Simulate field not existing on older model without the column
        del problem.acceptable_tolerance_percent
    return problem


@pytest.mark.unit
class TestNumericEvaluation:
    """Tests for numeric answer evaluation."""

    def test_numeric_exact_match(self) -> None:
        """Exact numeric match should be correct."""
        evaluator = AnswerEvaluator()
        problem = _make_problem(answer="40", answer_type="numeric")
        result = evaluator.evaluate(problem, "40", hints_used=0)

        assert result.is_correct is True
        assert result.answer_format_valid is True

    def test_numeric_within_5_percent_tolerance(self) -> None:
        """Answer within 5% tolerance should be correct."""
        evaluator = AnswerEvaluator()
        # correct=100, 5% tolerance → range [95, 105]
        problem = _make_problem(answer="100", answer_type="numeric")

        # 97 is within 5% of 100
        result = evaluator.evaluate(problem, "97", hints_used=0)
        assert result.is_correct is True

        # 103 is within 5% of 100
        result2 = evaluator.evaluate(problem, "103", hints_used=0)
        assert result2.is_correct is True

    def test_numeric_outside_tolerance(self) -> None:
        """Answer outside 5% tolerance should be wrong."""
        evaluator = AnswerEvaluator()
        problem = _make_problem(answer="100", answer_type="numeric")
        # 90 is 10% off — outside tolerance
        result = evaluator.evaluate(problem, "90", hints_used=0)
        assert result.is_correct is False
        assert result.answer_format_valid is True

    def test_numeric_zero_correct_answer_exact_only(self) -> None:
        """When correct answer is 0, only exact 0 is accepted."""
        evaluator = AnswerEvaluator()
        problem = _make_problem(answer="0", answer_type="numeric")

        result_correct = evaluator.evaluate(problem, "0", hints_used=0)
        assert result_correct.is_correct is True

        result_wrong = evaluator.evaluate(problem, "1", hints_used=0)
        assert result_wrong.is_correct is False

    def test_custom_tolerance_percent(self) -> None:
        """Custom tolerance percent from problem field is respected."""
        evaluator = AnswerEvaluator()
        problem = _make_problem(answer="200", answer_type="numeric", tolerance=10.0)
        # 180 is 10% off, within 10% tolerance
        result = evaluator.evaluate(problem, "180", hints_used=0)
        assert result.is_correct is True

        # 170 is 15% off, outside 10% tolerance
        result2 = evaluator.evaluate(problem, "170", hints_used=0)
        assert result2.is_correct is False


@pytest.mark.unit
class TestMultipleChoiceEvaluation:
    """Tests for multiple-choice answer evaluation."""

    def test_mc_digit_input(self) -> None:
        """Digit input matching correct index should be correct."""
        evaluator = AnswerEvaluator()
        problem = _make_problem(answer="1", answer_type="multiple_choice")
        result = evaluator.evaluate(problem, "1", hints_used=0)
        assert result.is_correct is True

    def test_mc_letter_input_lowercase(self) -> None:
        """Lowercase letter 'b' maps to index 1."""
        evaluator = AnswerEvaluator()
        problem = _make_problem(answer="1", answer_type="multiple_choice")
        result = evaluator.evaluate(problem, "b", hints_used=0)
        assert result.is_correct is True

    def test_mc_letter_input_uppercase(self) -> None:
        """Uppercase letter 'B' maps to index 1."""
        evaluator = AnswerEvaluator()
        problem = _make_problem(answer="1", answer_type="multiple_choice")
        result = evaluator.evaluate(problem, "B", hints_used=0)
        assert result.is_correct is True

    def test_mc_wrong_answer(self) -> None:
        """Wrong MC index is incorrect."""
        evaluator = AnswerEvaluator()
        problem = _make_problem(answer="2", answer_type="multiple_choice")
        result = evaluator.evaluate(problem, "A", hints_used=0)
        assert result.is_correct is False
        assert result.answer_format_valid is True

    def test_mc_invalid_input(self) -> None:
        """Non-letter, non-digit MC input is format-invalid."""
        evaluator = AnswerEvaluator()
        problem = _make_problem(answer="0", answer_type="multiple_choice")
        result = evaluator.evaluate(problem, "xyz", hints_used=0)
        assert result.is_correct is False
        assert result.answer_format_valid is False

    def test_mc_all_letters_a_d(self) -> None:
        """All valid letters map correctly."""
        evaluator = AnswerEvaluator()
        expected_map = {"a": "0", "b": "1", "c": "2", "d": "3"}
        for letter, index_str in expected_map.items():
            problem = _make_problem(answer=index_str, answer_type="multiple_choice")
            result = evaluator.evaluate(problem, letter, hints_used=0)
            assert result.is_correct is True, f"Letter {letter!r} should map to index {index_str}"


@pytest.mark.unit
class TestNormalization:
    """Tests for answer normalisation."""

    def test_normalize_rupee_symbol(self) -> None:
        """₹ symbol should be stripped."""
        evaluator = AnswerEvaluator()
        assert evaluator._normalize_answer("₹300") == "300"

    def test_normalize_dollar_symbol(self) -> None:
        """$ symbol should be stripped."""
        evaluator = AnswerEvaluator()
        assert evaluator._normalize_answer("$50") == "50"

    def test_normalize_trailing_units(self) -> None:
        """Trailing unit words should be stripped."""
        evaluator = AnswerEvaluator()
        assert evaluator._normalize_answer("300 cm") == "300"
        assert evaluator._normalize_answer("25 kg") == "25"
        assert evaluator._normalize_answer("75 %") == "75"

    def test_normalize_commas_thousands_separator(self) -> None:
        """Thousands-separator commas should be stripped."""
        evaluator = AnswerEvaluator()
        assert evaluator._normalize_answer("3,500") == "3500"
        assert evaluator._normalize_answer("1,000,000") == "1000000"

    def test_normalize_currency_word_rupees(self) -> None:
        """The word 'rupees' should be stripped."""
        evaluator = AnswerEvaluator()
        result = evaluator._normalize_answer("300 rupees")
        assert result == "300"

    def test_normalize_empty_string(self) -> None:
        """Empty string normalises to empty string."""
        evaluator = AnswerEvaluator()
        assert evaluator._normalize_answer("") == ""

    def test_normalize_whitespace_only(self) -> None:
        """Whitespace-only string normalises to empty string."""
        evaluator = AnswerEvaluator()
        assert evaluator._normalize_answer("   ") == ""

    def test_normalize_preserves_decimal(self) -> None:
        """Decimal values should be preserved."""
        evaluator = AnswerEvaluator()
        assert evaluator._normalize_answer("3.14") == "3.14"

    def test_normalize_double_star_to_caret(self) -> None:
        """Python-style ** should be normalised to ^ so x**2 == x^2."""
        evaluator = AnswerEvaluator()
        assert evaluator._normalize_answer("x**2") == "x^2"
        assert evaluator._normalize_answer("2**3") == "2^3"


@pytest.mark.unit
class TestAlgebraicExpressions:
    """Tests for non-numeric (algebraic) expression answers."""

    def test_caret_notation_accepted(self) -> None:
        """Student answer x^2 should match DB answer x^2."""
        evaluator = AnswerEvaluator()
        problem = _make_problem(answer="x^2", answer_type="numeric")
        result = evaluator.evaluate(problem, "x^2", hints_used=0)
        assert result.is_correct is True
        assert result.answer_format_valid is True

    def test_double_star_notation_accepted(self) -> None:
        """Student answer x**2 should match DB answer x^2."""
        evaluator = AnswerEvaluator()
        problem = _make_problem(answer="x^2", answer_type="numeric")
        result = evaluator.evaluate(problem, "x**2", hints_used=0)
        assert result.is_correct is True
        assert result.answer_format_valid is True

    def test_double_star_in_db_matches_caret_input(self) -> None:
        """DB stores x**2 but student types x^2 — still correct."""
        evaluator = AnswerEvaluator()
        problem = _make_problem(answer="x**2", answer_type="numeric")
        result = evaluator.evaluate(problem, "x^2", hints_used=0)
        assert result.is_correct is True

    def test_wrong_algebraic_answer(self) -> None:
        """x^3 should not match x^2."""
        evaluator = AnswerEvaluator()
        problem = _make_problem(answer="x^2", answer_type="numeric")
        result = evaluator.evaluate(problem, "x^3", hints_used=0)
        assert result.is_correct is False
        assert result.answer_format_valid is True


@pytest.mark.unit
class TestBlankAndGibberish:
    """Tests for blank or unparseable answers."""

    def test_blank_answer_is_format_invalid(self) -> None:
        """Empty student answer is format-invalid."""
        evaluator = AnswerEvaluator()
        problem = _make_problem(answer="40", answer_type="numeric")
        result = evaluator.evaluate(problem, "", hints_used=0)

        assert result.is_correct is False
        assert result.answer_format_valid is False

    def test_whitespace_only_is_format_invalid(self) -> None:
        """Whitespace-only student answer is format-invalid."""
        evaluator = AnswerEvaluator()
        problem = _make_problem(answer="40", answer_type="numeric")
        result = evaluator.evaluate(problem, "   ", hints_used=0)

        assert result.is_correct is False
        assert result.answer_format_valid is False

    def test_gibberish_is_format_invalid(self) -> None:
        """Non-numeric gibberish for a numeric problem is format-invalid."""
        evaluator = AnswerEvaluator()
        problem = _make_problem(answer="40", answer_type="numeric")
        result = evaluator.evaluate(problem, "banana", hints_used=0)

        assert result.is_correct is False
        assert result.answer_format_valid is False


@pytest.mark.unit
class TestConfidenceLevels:
    """Tests for confidence level derivation from hints_used."""

    def test_confidence_no_hints(self) -> None:
        """0 hints → high confidence."""
        evaluator = AnswerEvaluator()
        assert evaluator._derive_confidence(0) == "high"

    def test_confidence_one_hint(self) -> None:
        """1 hint → medium confidence."""
        evaluator = AnswerEvaluator()
        assert evaluator._derive_confidence(1) == "medium"

    def test_confidence_two_hints(self) -> None:
        """2 hints → medium confidence."""
        evaluator = AnswerEvaluator()
        assert evaluator._derive_confidence(2) == "medium"

    def test_confidence_max_hints(self) -> None:
        """3 hints → low confidence."""
        evaluator = AnswerEvaluator()
        assert evaluator._derive_confidence(3) == "low"

    def test_confidence_reflected_in_result(self) -> None:
        """Confidence level is correctly reflected in EvaluationResult."""
        evaluator = AnswerEvaluator()
        problem = _make_problem(answer="40", answer_type="numeric")

        result_high = evaluator.evaluate(problem, "40", hints_used=0)
        assert result_high.confidence_level == "high"

        result_medium = evaluator.evaluate(problem, "40", hints_used=1)
        assert result_medium.confidence_level == "medium"

        result_low = evaluator.evaluate(problem, "40", hints_used=3)
        assert result_low.confidence_level == "low"


@pytest.mark.unit
class TestBilingualFeedback:
    """Tests for bilingual feedback messages."""

    def test_bilingual_feedback_correct(self) -> None:
        """Correct answer returns both EN and BN success messages."""
        evaluator = AnswerEvaluator()
        problem = _make_problem(answer="40", answer_type="numeric")
        result = evaluator.evaluate(problem, "40", hints_used=0)

        assert result.is_correct is True
        assert "Correct" in result.feedback_en
        assert "Well done" in result.feedback_en
        assert "সঠিক" in result.feedback_bn
        assert "শাবাশ" in result.feedback_bn

    def test_bilingual_feedback_wrong(self) -> None:
        """Wrong answer returns both EN and BN failure messages."""
        evaluator = AnswerEvaluator()
        problem = _make_problem(answer="40", answer_type="numeric")
        result = evaluator.evaluate(problem, "99", hints_used=0)

        assert result.is_correct is False
        assert "Not quite" in result.feedback_en
        assert "hint" in result.feedback_en
        assert "ঠিক হয়নি" in result.feedback_bn
        assert "hint" in result.feedback_bn

    def test_format_invalid_feedback(self) -> None:
        """Invalid format returns appropriate bilingual messages."""
        evaluator = AnswerEvaluator()
        problem = _make_problem(answer="40", answer_type="numeric")
        result = evaluator.evaluate(problem, "gibberish", hints_used=0)

        assert result.answer_format_valid is False
        assert "number" in result.feedback_en.lower()
        assert "সংখ্যা" in result.feedback_bn

    def test_normalized_answer_stored(self) -> None:
        """EvaluationResult stores the normalised version of the answer."""
        evaluator = AnswerEvaluator()
        problem = _make_problem(answer="300", answer_type="numeric")
        result = evaluator.evaluate(problem, "₹300", hints_used=0)

        assert result.normalized_answer == "300"
        assert result.is_correct is True
