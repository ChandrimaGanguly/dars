"""Integration tests for HintGenerator end-to-end flow (PHASE5-C-1).

CP-2: Verifies the full hint pipeline using in-memory SQLite — from DB problem
retrieval through HintGenerator (with mocked Claude API) to cost recording.

These tests call the service/repository layer directly (not via HTTP).
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from anthropic.types import Message, TextBlock, Usage
from sqlalchemy import select

from src.models.cost_record import CostRecord, OperationType
from src.models.problem import Problem
from src.models.student import Student
from src.services.cost_tracker import CostTracker
from src.services.hint_cache import HintCache
from src.services.hint_generator import HintGenerator

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TELEGRAM_ID = 999888777


async def _create_student(db_session: Any, language: str = "en") -> Student:
    student = Student(
        telegram_id=TELEGRAM_ID,
        name="HintFlowStudent",
        grade=7,
        language=language,
    )
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)
    return student


async def _create_problem(db_session: Any) -> Problem:
    p = Problem(
        grade=7,
        topic="Arithmetic",
        question_en="What is 15 + 27?",
        question_bn="15 + 27 কত?",
        answer="42",
        hints=[
            {
                "hint_number": 1,
                "text_en": "Break it into tens and units.",
                "text_bn": "দশক ও একক আলাদা করো।",
                "is_ai_generated": False,
            },
            {
                "hint_number": 2,
                "text_en": "15 + 20 = 35, now add 7.",
                "text_bn": "15 + 20 = 35, এবার 7 যোগ করো।",
                "is_ai_generated": False,
            },
            {
                "hint_number": 3,
                "text_en": "The answer is 42.",
                "text_bn": "উত্তর 42।",
                "is_ai_generated": False,
            },
        ],
        difficulty=1,
        estimated_time_minutes=3,
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    return p


def _mock_api_response(text: str, in_tok: int = 60, out_tok: int = 25) -> MagicMock:
    block = MagicMock(spec=TextBlock)
    block.text = text
    usage = MagicMock(spec=Usage)
    usage.input_tokens = in_tok
    usage.output_tokens = out_tok
    resp = MagicMock(spec=Message)
    resp.content = [block]
    resp.usage = usage
    return resp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestHintGeneratorFlow:
    """End-to-end flow: DB problem → HintGenerator → cost recording."""

    async def test_fallback_hint_served_without_api_key(self, db_session: Any) -> None:
        """When no API key is set, the pre-written hint from the DB is returned."""
        student = await _create_student(db_session)
        student_id = student.student_id  # capture before next commit expires object
        problem = await _create_problem(db_session)

        gen = HintGenerator()

        with patch("src.services.hint_generator.get_settings") as mock_settings:
            mock_settings.return_value.anthropic_api_key = ""
            hint, is_ai, in_tok, out_tok = await gen.get_hint(
                db=db_session,
                problem=problem,
                student_answer="40",
                hint_number=1,
                student_id=student_id,
                language="en",
            )

        assert "Break it into tens" in hint
        assert is_ai is False
        assert in_tok is None
        assert out_tok is None

    async def test_ai_hint_served_when_api_key_present(self, db_session: Any) -> None:
        """When API key is set and under rate limit, AI hint is served."""
        student = await _create_student(db_session)
        student_id = student.student_id
        problem = await _create_problem(db_session)

        gen = HintGenerator()
        mock_resp = _mock_api_response("Consider breaking the problem into smaller parts.")

        with (
            patch("src.services.hint_generator.get_settings") as mock_settings,
            patch("src.services.hint_generator.anthropic.AsyncAnthropic") as mock_anthropic,
        ):
            mock_settings.return_value.anthropic_api_key = "sk-test"
            mock_anthropic.return_value.messages.create = AsyncMock(return_value=mock_resp)

            hint, is_ai, in_tok, out_tok = await gen.get_hint(
                db=db_session,
                problem=problem,
                student_answer="40",
                hint_number=1,
                student_id=student_id,
                language="en",
            )

        assert hint == "Consider breaking the problem into smaller parts."
        assert is_ai is True
        assert in_tok == 60
        assert out_tok == 25

    async def test_ai_hint_recorded_in_cost_table(self, db_session: Any) -> None:
        """AI hint token counts are persisted via CostTracker."""
        student = await _create_student(db_session)
        student_id = student.student_id  # capture before next commit expires object
        problem = await _create_problem(db_session)

        gen = HintGenerator()
        mock_resp = _mock_api_response("Think carefully.", in_tok=100, out_tok=40)

        with (
            patch("src.services.hint_generator.get_settings") as mock_settings,
            patch("src.services.hint_generator.anthropic.AsyncAnthropic") as mock_anthropic,
        ):
            mock_settings.return_value.anthropic_api_key = "sk-test"
            mock_anthropic.return_value.messages.create = AsyncMock(return_value=mock_resp)

            _, is_ai, in_tok, out_tok = await gen.get_hint(
                db=db_session,
                problem=problem,
                student_answer="",
                hint_number=1,
                student_id=student_id,
                language="en",
            )

        # Record cost via CostTracker (as practice.py would do)
        cost_tracker = CostTracker()
        await cost_tracker.record_hint_cost(
            db_session,
            student_id,
            None,
            1,
            is_ai_generated=is_ai,
            input_tokens=in_tok,
            output_tokens=out_tok,
        )
        await db_session.commit()

        result = await db_session.execute(
            select(CostRecord).where(
                CostRecord.student_id == student_id,
                CostRecord.operation == OperationType.HINT_GENERATION,
            )
        )
        record = result.scalar_one()
        assert record.cost_usd > 0.0
        assert record.input_tokens == 100
        assert record.output_tokens == 40

    async def test_fallback_hint_records_zero_cost(self, db_session: Any) -> None:
        """Pre-written fallback hints record cost_usd=0.00."""
        student = await _create_student(db_session)
        student_id = student.student_id  # capture before next commit expires object
        problem = await _create_problem(db_session)

        gen = HintGenerator()

        with patch("src.services.hint_generator.get_settings") as mock_settings:
            mock_settings.return_value.anthropic_api_key = ""
            _, is_ai, in_tok, out_tok = await gen.get_hint(
                db=db_session,
                problem=problem,
                student_answer="",
                hint_number=1,
                student_id=student_id,
                language="en",
            )

        cost_tracker = CostTracker()
        await cost_tracker.record_hint_cost(
            db_session,
            student_id,
            None,
            1,
            is_ai_generated=is_ai,
            input_tokens=in_tok,
            output_tokens=out_tok,
        )
        await db_session.commit()

        result = await db_session.execute(
            select(CostRecord).where(CostRecord.student_id == student_id)
        )
        record = result.scalar_one()
        assert record.cost_usd == 0.0

    async def test_cache_prevents_duplicate_api_calls(self, db_session: Any) -> None:
        """Second hint request for same problem/number uses cache, not API."""
        student = await _create_student(db_session)
        student_id = student.student_id  # capture before next commit expires object
        problem = await _create_problem(db_session)

        cache = HintCache()
        gen = HintGenerator(cache=cache)
        mock_resp = _mock_api_response("Use algebra.")

        with (
            patch("src.services.hint_generator.get_settings") as mock_settings,
            patch("src.services.hint_generator.anthropic.AsyncAnthropic") as mock_anthropic,
        ):
            mock_settings.return_value.anthropic_api_key = "sk-test"
            mock_anthropic.return_value.messages.create = AsyncMock(return_value=mock_resp)

            # First call — hits API
            hint1, is_ai1, _, _ = await gen.get_hint(
                db=db_session,
                problem=problem,
                student_answer="",
                hint_number=2,
                student_id=student_id,
            )
            api_call_count = mock_anthropic.return_value.messages.create.call_count

            # Second call — should use cache
            hint2, is_ai2, _, _ = await gen.get_hint(
                db=db_session,
                problem=problem,
                student_answer="",
                hint_number=2,
                student_id=student_id,
            )

        assert hint1 == hint2 == "Use algebra."
        assert is_ai1 is True
        assert is_ai2 is False  # from cache
        assert (
            mock_anthropic.return_value.messages.create.call_count == api_call_count
        )  # no extra call

    async def test_bengali_hint_returned_from_fallback(self, db_session: Any) -> None:
        """Bengali language requests return Bengali pre-written hints."""
        student = await _create_student(db_session, language="bn")
        student_id = student.student_id  # capture before next commit expires object
        problem = await _create_problem(db_session)

        gen = HintGenerator()

        with patch("src.services.hint_generator.get_settings") as mock_settings:
            mock_settings.return_value.anthropic_api_key = ""
            hint, _, _, _ = await gen.get_hint(
                db=db_session,
                problem=problem,
                student_answer="",
                hint_number=1,
                student_id=student_id,
                language="bn",
            )

        assert "দশক" in hint  # Bengali text from hint_bn
