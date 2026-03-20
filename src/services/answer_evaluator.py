"""Answer evaluator for student practice responses.

Evaluates student answers against correct answers with appropriate tolerance
rules for numeric, multiple-choice, and future text types. Purely computational
— no I/O, completes in <10ms.

PHASE3-B-2
"""

import re
from dataclasses import dataclass

from src.models.problem import Problem

# Default tolerance for numeric answers (±5%)
DEFAULT_NUMERIC_TOLERANCE_PERCENT = 5.0

# Maximum hints per problem
MAX_HINTS_PER_PROBLEM = 3

# Currency symbols and words to strip during normalisation
_CURRENCY_SYMBOLS = re.compile(r"[₹$€£¥]")
_CURRENCY_WORDS = re.compile(
    r"\b(rupees?|taka|paisa|পয়সা|টাকা|dollars?|euros?|pounds?)\b",
    re.IGNORECASE,
)

# Trailing unit patterns to strip (% handled separately as a non-word char)
_TRAILING_UNITS = re.compile(
    r"\b(cm|m|km|kg|g|mg|sq|cubic|litre?|liter?|ml|°c|celsius|°f|fahrenheit|percent|"
    r"unit|units|hrs?|hours?|min|mins|minutes?|sec|secs?|seconds?)\b",
    re.IGNORECASE,
)
# Standalone percent symbol (not a word char so \b doesn't work around it)
_PERCENT_SYMBOL = re.compile(r"\s*%\s*")

# Thousands-separator commas (e.g., "3,500" → "3500")
_THOUSANDS_COMMA = re.compile(r"(\d),(\d{3})\b")

# Arabic-script variants of comma/separator
_ARABIC_COMMA = re.compile(r"[،,٬]")

# Normalise Python-style power operator to caret (x**2 → x^2)
_DOUBLE_STAR = re.compile(r"\*\*")

# Letter-to-index mapping for multiple choice
_MC_LETTER_MAP: dict[str, int] = {"a": 0, "b": 1, "c": 2, "d": 3}

# Bengali (Bangla) digit to ASCII digit translation table (U+09E6..U+09EF)
_BENGALI_TO_ASCII = str.maketrans(
    "\u09e6\u09e7\u09e8\u09e9\u09ea\u09eb\u09ec\u09ed\u09ee\u09ef", "0123456789"
)


@dataclass
class EvaluationResult:
    """Result of evaluating a student's answer.

    Attributes:
        is_correct: Whether the answer is considered correct.
        feedback_en: English-language feedback message.
        feedback_bn: Bengali-language feedback message.
        normalized_answer: The answer after normalisation (for logging/display).
        confidence_level: "high", "medium", or "low" based on hints_used.
        answer_format_valid: Whether the answer could be parsed correctly.
    """

    is_correct: bool
    feedback_en: str
    feedback_bn: str
    normalized_answer: str
    confidence_level: str
    answer_format_valid: bool


class AnswerEvaluator:
    """Evaluate student answers for numeric and multiple-choice problems.

    Pure computation — no I/O. Must complete in <10ms.

    Usage:
        evaluator = AnswerEvaluator()
        result = evaluator.evaluate(problem, "42", hints_used=0)
    """

    def evaluate(
        self,
        problem: Problem,
        student_answer: str,
        hints_used: int,
    ) -> EvaluationResult:
        """Evaluate a student's answer against the correct answer.

        Dispatches to the appropriate evaluation strategy based on the
        problem's answer_type (numeric or multiple_choice). Falls back
        to numeric if answer_type is not available on the model.

        Args:
            problem: The Problem being answered.
            student_answer: The student's submitted answer string.
            hints_used: Number of hints already used (0-3), used for confidence.

        Returns:
            EvaluationResult with all evaluation details.
        """
        answer_type = getattr(problem, "answer_type", None) or "numeric"
        confidence = self._derive_confidence(hints_used)
        normalized = self._normalize_answer(student_answer)

        # Format hint messages are answer-type-aware
        if answer_type == "multiple_choice":
            format_hint_en = "Please enter A, B, C, or D."
            format_hint_bn = "অনুগ্রহ করে A, B, C বা D লেখো।"
        else:
            format_hint_en = "Please write just the number."
            format_hint_bn = "শুধু সংখ্যাটা লেখো।"

        if not normalized:
            return EvaluationResult(
                is_correct=False,
                feedback_en=format_hint_en,
                feedback_bn=format_hint_bn,
                normalized_answer="",
                confidence_level=confidence,
                answer_format_valid=False,
            )

        if answer_type == "multiple_choice":
            is_correct, format_valid = self._evaluate_multiple_choice(problem.answer, normalized)
        else:
            # Default: numeric
            tolerance = getattr(problem, "acceptable_tolerance_percent", None)
            if tolerance is None:
                tolerance = DEFAULT_NUMERIC_TOLERANCE_PERCENT
            is_correct, format_valid = self._evaluate_numeric(
                problem.answer, normalized, float(tolerance)
            )

        if not format_valid:
            return EvaluationResult(
                is_correct=False,
                feedback_en=format_hint_en,
                feedback_bn=format_hint_bn,
                normalized_answer=normalized,
                confidence_level=confidence,
                answer_format_valid=False,
            )

        if is_correct:
            return EvaluationResult(
                is_correct=True,
                feedback_en="Correct! \u2705 Well done!",
                feedback_bn="সঠিক! \u2705 শাবাশ!",
                normalized_answer=normalized,
                confidence_level=confidence,
                answer_format_valid=True,
            )

        return EvaluationResult(
            is_correct=False,
            feedback_en="Not quite. Try again or ask for a hint.",
            feedback_bn="ঠিক হয়নি। আবার চেষ্টা করো বা hint চাও।",
            normalized_answer=normalized,
            confidence_level=confidence,
            answer_format_valid=True,
        )

    def _evaluate_numeric(
        self,
        correct_raw: str,
        student_normalized: str,
        tolerance_percent: float,
    ) -> tuple[bool, bool]:
        """Evaluate a numeric answer with percentage tolerance.

        Args:
            correct_raw: The raw correct answer from the database.
            student_normalized: The student's answer after normalisation.
            tolerance_percent: Acceptable tolerance as a percentage (e.g., 5.0).

        Returns:
            Tuple (is_correct, format_valid). format_valid is False if
            the student's answer cannot be parsed as a float.
        """
        correct_normalized = self._normalize_answer(correct_raw)

        try:
            correct_value = float(correct_normalized)
        except (ValueError, TypeError):
            # Correct answer not numeric; fall back to exact string match
            return (student_normalized == correct_normalized, True)

        try:
            student_value = float(student_normalized)
        except (ValueError, TypeError):
            return (False, False)

        # Special case: correct answer is zero → exact match only
        if correct_value == 0.0:
            return (student_value == 0.0, True)

        tolerance = abs(correct_value * tolerance_percent / 100.0)
        return (abs(student_value - correct_value) <= tolerance, True)

    def _evaluate_multiple_choice(
        self,
        correct_raw: str,
        student_normalized: str,
    ) -> tuple[bool, bool]:
        """Evaluate a multiple-choice answer by index comparison.

        The correct answer in the database is a digit string: "0"=A, "1"=B,
        "2"=C, "3"=D. The student may input a digit or a letter (a/b/c/d or
        A/B/C/D).

        Args:
            correct_raw: Correct answer digit string from the database.
            student_normalized: Normalised student answer.

        Returns:
            Tuple (is_correct, format_valid).
        """
        correct_index_str = correct_raw.strip()

        # Convert student answer to index string
        student_index_str = self._mc_normalize(student_normalized)
        if student_index_str is None:
            return (False, False)

        return (student_index_str == correct_index_str, True)

    def _mc_normalize(self, answer: str) -> str | None:
        """Normalise a multiple-choice answer to a digit string.

        Accepts:
        - Digit characters: "0", "1", "2", "3"
        - Letters: "a"/"A" → "0", "b"/"B" → "1", etc.

        Args:
            answer: The normalised (stripped) student answer string.

        Returns:
            Digit string "0"-"3", or None if unparseable.
        """
        stripped = answer.strip().lower()

        if stripped in _MC_LETTER_MAP:
            return str(_MC_LETTER_MAP[stripped])

        if stripped in {"0", "1", "2", "3"}:
            return stripped

        return None

    def _normalize_answer(self, raw: str) -> str:
        """Normalise an answer string for comparison.

        Applies the following in order:
        1. Strip whitespace.
        2. Remove currency symbols (₹, $, €, £).
        3. Remove currency words (rupees, taka, etc.).
        4. Remove thousands-separator commas (3,500 → 3500).
        5. Remove trailing units (cm, kg, %, etc.).
        6. Strip Arabic/Devanagari comma variants.
        7. Strip again after all substitutions.

        Args:
            raw: Raw answer string (from DB or student input).

        Returns:
            Normalised string (may be empty if answer was blank/whitespace).
        """
        if not raw:
            return ""

        text = raw.strip()

        # Convert Bengali digits to ASCII (e.g., "৩" → "3")
        text = text.translate(_BENGALI_TO_ASCII)

        # Remove currency symbols
        text = _CURRENCY_SYMBOLS.sub("", text)

        # Remove currency words
        text = _CURRENCY_WORDS.sub("", text)

        # Remove thousands-separator commas (must loop for cases like "1,000,000")
        while _THOUSANDS_COMMA.search(text):
            text = _THOUSANDS_COMMA.sub(r"\1\2", text)

        # Remove Arabic/variant commas
        text = _ARABIC_COMMA.sub("", text)

        # Remove percent symbol
        text = _PERCENT_SYMBOL.sub("", text)

        # Remove trailing units (e.g., "300 cm" → "300")
        text = _TRAILING_UNITS.sub("", text)

        # Normalise power notation (x**2 → x^2) so both forms compare equal
        text = _DOUBLE_STAR.sub("^", text)

        return text.strip()

    def _derive_confidence(self, hints_used: int) -> str:
        """Map hints_used to a confidence level string.

        Args:
            hints_used: Number of hints used for this problem (0-3).

        Returns:
            "high" if no hints, "medium" if 1 or 2 hints, "low" if 3 hints.
        """
        if hints_used == 0:
            return "high"
        if hints_used >= MAX_HINTS_PER_PROBLEM:
            return "low"
        return "medium"
