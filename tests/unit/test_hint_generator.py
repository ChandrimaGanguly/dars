"""Unit tests for HintGenerator (PHASE5-B-1 / PHASE5-C-3).

All Claude API calls are mocked — these are pure unit tests.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from anthropic.types import Message, TextBlock, Usage

from src.services.hint_cache import HintCache
from src.services.hint_generator import _MAX_AI_HINTS_PER_DAY, HintGenerator

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_problem(
    problem_id: int = 1,
    grade: int = 7,
    question_en: str = "What is 2+2?",
    answer: str = "4",
    hints: list[str] | None = None,
) -> MagicMock:
    """Build a minimal mock Problem ORM object."""
    p = MagicMock()
    p.problem_id = problem_id
    p.grade = grade
    p.question_en = question_en
    p.answer = answer

    # get_hints() returns list of hint objects with to_dict()
    hint_texts = hints or ["Think about basic addition.", "Count on your fingers.", "2+2=4."]
    hint_mocks = []
    for text in hint_texts:
        h = MagicMock()
        h.to_dict.return_value = {"text_en": text, "text_bn": f"বাংলা: {text}"}
        hint_mocks.append(h)
    p.get_hints.return_value = hint_mocks
    return p


def _make_anthropic_response(text: str, in_tok: int = 50, out_tok: int = 30) -> MagicMock:
    """Build a mock Anthropic API response."""
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
# Tests: cache hit
# ---------------------------------------------------------------------------


class TestHintGeneratorCacheHit:
    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_text(self) -> None:
        cache = HintCache()
        cache.set(1, 1, "en", "Cached hint text")
        gen = HintGenerator(cache=cache)
        db = AsyncMock()
        problem = _make_problem()

        hint, is_ai, in_tok, out_tok = await gen.get_hint(
            db=db,
            problem=problem,
            student_answer="5",
            hint_number=1,
            student_id=42,
            language="en",
        )

        assert hint == "Cached hint text"
        assert is_ai is False
        assert in_tok is None
        assert out_tok is None

    @pytest.mark.asyncio
    async def test_cache_hit_does_not_call_api(self) -> None:
        cache = HintCache()
        cache.set(1, 1, "en", "Cached")
        gen = HintGenerator(cache=cache)
        db = AsyncMock()
        problem = _make_problem()

        with patch("src.services.hint_generator.anthropic.AsyncAnthropic") as mock_client:
            await gen.get_hint(
                db=db,
                problem=problem,
                student_answer="",
                hint_number=1,
                student_id=42,
            )
            mock_client.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: no API key → fallback
# ---------------------------------------------------------------------------


class TestHintGeneratorNoApiKey:
    @pytest.mark.asyncio
    async def test_no_api_key_returns_fallback(self) -> None:
        gen = HintGenerator()
        db = AsyncMock()
        problem = _make_problem()

        with patch("src.services.hint_generator.get_settings") as mock_settings:
            mock_settings.return_value.anthropic_api_key = ""
            hint, is_ai, in_tok, out_tok = await gen.get_hint(
                db=db,
                problem=problem,
                student_answer="5",
                hint_number=1,
                student_id=42,
                language="en",
            )

        assert hint == "Think about basic addition."
        assert is_ai is False
        assert in_tok is None
        assert out_tok is None

    @pytest.mark.asyncio
    async def test_no_api_key_bengali_fallback(self) -> None:
        gen = HintGenerator()
        db = AsyncMock()
        problem = _make_problem()

        with patch("src.services.hint_generator.get_settings") as mock_settings:
            mock_settings.return_value.anthropic_api_key = ""
            hint, is_ai, _, _ = await gen.get_hint(
                db=db,
                problem=problem,
                student_answer="",
                hint_number=1,
                student_id=42,
                language="bn",
            )

        assert "বাংলা" in hint
        assert is_ai is False


# ---------------------------------------------------------------------------
# Tests: rate limit → fallback
# ---------------------------------------------------------------------------


class TestHintGeneratorRateLimit:
    @pytest.mark.asyncio
    async def test_rate_limit_reached_returns_fallback(self) -> None:
        gen = HintGenerator()
        db = AsyncMock()
        problem = _make_problem()

        with (
            patch("src.services.hint_generator.get_settings") as mock_settings,
            patch.object(gen, "_ai_hints_today", new=AsyncMock(return_value=_MAX_AI_HINTS_PER_DAY)),
        ):
            mock_settings.return_value.anthropic_api_key = "sk-test"
            _, is_ai, in_tok, out_tok = await gen.get_hint(
                db=db,
                problem=problem,
                student_answer="",
                hint_number=1,
                student_id=42,
            )

        assert is_ai is False
        assert in_tok is None
        assert out_tok is None

    @pytest.mark.asyncio
    async def test_below_rate_limit_proceeds_to_api(self) -> None:
        gen = HintGenerator()
        db = AsyncMock()
        problem = _make_problem()
        mock_resp = _make_anthropic_response("AI hint here")

        with (
            patch("src.services.hint_generator.get_settings") as mock_settings,
            patch.object(
                gen, "_ai_hints_today", new=AsyncMock(return_value=_MAX_AI_HINTS_PER_DAY - 1)
            ),
            patch("src.services.hint_generator.anthropic.AsyncAnthropic") as mock_anthropic,
        ):
            mock_settings.return_value.anthropic_api_key = "sk-test"
            mock_anthropic.return_value.messages.create = AsyncMock(return_value=mock_resp)

            hint, is_ai, in_tok, out_tok = await gen.get_hint(
                db=db,
                problem=problem,
                student_answer="",
                hint_number=1,
                student_id=42,
            )

        assert hint == "AI hint here"
        assert is_ai is True
        assert in_tok == 50
        assert out_tok == 30


# ---------------------------------------------------------------------------
# Tests: successful API call
# ---------------------------------------------------------------------------


class TestHintGeneratorApiSuccess:
    @pytest.mark.asyncio
    async def test_api_returns_hint_text_and_tokens(self) -> None:
        gen = HintGenerator()
        db = AsyncMock()
        problem = _make_problem()
        mock_resp = _make_anthropic_response("Think about what operation applies here.", 80, 20)

        with (
            patch("src.services.hint_generator.get_settings") as mock_settings,
            patch.object(gen, "_ai_hints_today", new=AsyncMock(return_value=0)),
            patch("src.services.hint_generator.anthropic.AsyncAnthropic") as mock_anthropic,
        ):
            mock_settings.return_value.anthropic_api_key = "sk-test"
            mock_anthropic.return_value.messages.create = AsyncMock(return_value=mock_resp)

            hint, is_ai, in_tok, out_tok = await gen.get_hint(
                db=db,
                problem=problem,
                student_answer="3",
                hint_number=1,
                student_id=42,
            )

        assert hint == "Think about what operation applies here."
        assert is_ai is True
        assert in_tok == 80
        assert out_tok == 20

    @pytest.mark.asyncio
    async def test_api_result_stored_in_cache(self) -> None:
        cache = HintCache()
        gen = HintGenerator(cache=cache)
        db = AsyncMock()
        problem = _make_problem(problem_id=99)
        mock_resp = _make_anthropic_response("Cached after API call.")

        with (
            patch("src.services.hint_generator.get_settings") as mock_settings,
            patch.object(gen, "_ai_hints_today", new=AsyncMock(return_value=0)),
            patch("src.services.hint_generator.anthropic.AsyncAnthropic") as mock_anthropic,
        ):
            mock_settings.return_value.anthropic_api_key = "sk-test"
            mock_anthropic.return_value.messages.create = AsyncMock(return_value=mock_resp)

            await gen.get_hint(
                db=db, problem=problem, student_answer="", hint_number=2, student_id=1
            )

        assert cache.get(99, 2, "en") == "Cached after API call."

    @pytest.mark.asyncio
    async def test_bengali_prompt_appends_suffix(self) -> None:
        gen = HintGenerator()
        db = AsyncMock()
        problem = _make_problem()
        mock_resp = _make_anthropic_response("Bengali hint")
        captured_messages: list[list[dict[str, str]]] = []

        async def capture_create(**kwargs: object) -> MagicMock:
            captured_messages.append(kwargs.get("messages", []))  # type: ignore[arg-type]
            return mock_resp

        with (
            patch("src.services.hint_generator.get_settings") as mock_settings,
            patch.object(gen, "_ai_hints_today", new=AsyncMock(return_value=0)),
            patch("src.services.hint_generator.anthropic.AsyncAnthropic") as mock_anthropic,
        ):
            mock_settings.return_value.anthropic_api_key = "sk-test"
            mock_anthropic.return_value.messages.create = capture_create

            await gen.get_hint(
                db=db,
                problem=problem,
                student_answer="",
                hint_number=1,
                student_id=1,
                language="bn",
            )

        assert len(captured_messages) == 1
        prompt_content = captured_messages[0][0]["content"]
        assert "বাংলা" in prompt_content


# ---------------------------------------------------------------------------
# Tests: API failure → fallback
# ---------------------------------------------------------------------------


class TestHintGeneratorApiFallback:
    @pytest.mark.asyncio
    async def test_all_retries_fail_returns_fallback(self) -> None:
        import anthropic as anthropic_lib

        gen = HintGenerator()
        db = AsyncMock()
        problem = _make_problem()

        with (
            patch("src.services.hint_generator.get_settings") as mock_settings,
            patch.object(gen, "_ai_hints_today", new=AsyncMock(return_value=0)),
            patch("src.services.hint_generator.anthropic.AsyncAnthropic") as mock_anthropic,
            patch("src.services.hint_generator.asyncio.sleep", new=AsyncMock()),
        ):
            mock_settings.return_value.anthropic_api_key = "sk-test"
            mock_anthropic.return_value.messages.create = AsyncMock(
                side_effect=anthropic_lib.APIConnectionError(request=MagicMock())
            )

            hint, is_ai, _, _ = await gen.get_hint(
                db=db,
                problem=problem,
                student_answer="",
                hint_number=1,
                student_id=42,
            )

        assert hint == "Think about basic addition."
        assert is_ai is False

    @pytest.mark.asyncio
    async def test_auth_error_returns_fallback_without_retry(self) -> None:
        import anthropic as anthropic_lib

        gen = HintGenerator()
        db = AsyncMock()
        problem = _make_problem()
        call_count = 0

        async def raise_auth(*args: object, **kwargs: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            raise anthropic_lib.AuthenticationError(
                message="Invalid key",
                response=MagicMock(),
                body={},
            )

        with (
            patch("src.services.hint_generator.get_settings") as mock_settings,
            patch.object(gen, "_ai_hints_today", new=AsyncMock(return_value=0)),
            patch("src.services.hint_generator.anthropic.AsyncAnthropic") as mock_anthropic,
        ):
            mock_settings.return_value.anthropic_api_key = "sk-bad"
            mock_anthropic.return_value.messages.create = raise_auth

            _, is_ai, _, _ = await gen.get_hint(
                db=db,
                problem=problem,
                student_answer="",
                hint_number=1,
                student_id=42,
            )

        # Should break immediately on AuthenticationError — only 1 attempt
        assert call_count == 1
        assert is_ai is False


# ---------------------------------------------------------------------------
# Tests: fallback out-of-bounds
# ---------------------------------------------------------------------------


class TestHintGeneratorFallback:
    @pytest.mark.asyncio
    async def test_hint_number_out_of_range_returns_no_hint_message(self) -> None:
        gen = HintGenerator()
        db = AsyncMock()
        problem = _make_problem(hints=["Only one hint."])

        with patch("src.services.hint_generator.get_settings") as mock_settings:
            mock_settings.return_value.anthropic_api_key = ""
            hint, is_ai, _, _ = await gen.get_hint(
                db=db,
                problem=problem,
                student_answer="",
                hint_number=3,
                student_id=1,
                language="en",
            )

        assert "No hint available" in hint
        assert is_ai is False

    @pytest.mark.asyncio
    async def test_out_of_range_bengali_message(self) -> None:
        gen = HintGenerator()
        db = AsyncMock()
        problem = _make_problem(hints=["Only one hint."])

        with patch("src.services.hint_generator.get_settings") as mock_settings:
            mock_settings.return_value.anthropic_api_key = ""
            hint, _, _, _ = await gen.get_hint(
                db=db,
                problem=problem,
                student_answer="",
                hint_number=3,
                student_id=1,
                language="bn",
            )

        assert "hint পাওয়া যায়নি" in hint
