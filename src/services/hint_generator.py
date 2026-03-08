"""Claude Haiku-powered Socratic hint generator.

PHASE5-B-1

Implements REQ-002 (Socratic hints) and REQ-015 (Claude API integration).

Business rules:
- Cache first: check HintCache before calling the API (REQ-016).
- Rate limit: max 10 AI calls per student per day; fall back to pre-written
  hints when the limit is reached.
- Fallback: if API key is absent, rate limit is hit, or all 3 retry
  attempts fail, return the pre-written hint from the problem's hints list.
- Cost transparency: caller receives raw token counts so it can pass them
  to CostTracker for accurate cost_usd recording.
- Language: append Bengali instruction when language="bn".

Returns a 4-tuple: (hint_text, is_ai_generated, input_tokens, output_tokens).
Callers own the transaction boundary and cost-recording call.
"""

import asyncio
from datetime import UTC, date, datetime

import anthropic
from anthropic.types import TextBlock
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.logging import get_logger
from src.models.cost_record import CostRecord, OperationType
from src.models.problem import Problem
from src.services.hint_cache import HintCache

logger = get_logger(__name__)

# Claude model — cheapest, fastest (REQ-015)
_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 150
_MAX_AI_HINTS_PER_DAY = 10
_MAX_RETRIES = 3

# Prompt template (REQ-015)
_PROMPT_TEMPLATE = """\
Problem: {question}
Student's Answer: {student_answer}
Correct Answer: {correct_answer}
Hint Number: {hint_number} of 3

You are tutoring a Grade {grade} student in India using the Socratic method.
- Hint 1: Ask a guiding question that makes the student think about their approach.
- Hint 2: Point out the specific concept or step they are missing.
- Hint 3: Give step-by-step guidance but DO NOT reveal the correct answer.

Generate Hint {hint_number} ONLY. No preamble. Maximum 2 sentences. \
Use simple language appropriate for a Grade {grade} student.\
"""

_BENGALI_SUFFIX = "\nRespond in Bengali (বাংলা)."


class HintGenerator:
    """Generate Socratic hints via Claude Haiku with cache and fallback.

    Example::

        cache = HintCache()
        gen = HintGenerator(cache=cache)
        hint, is_ai, in_tok, out_tok = await gen.get_hint(
            db, problem, student_answer="60", hint_number=1,
            student_id=42, language="en",
        )
        # is_ai=True  → AI-generated, record real cost
        # is_ai=False → pre-written fallback, cost_usd=0.00
    """

    def __init__(self, cache: HintCache | None = None) -> None:
        """Initialise with an optional shared cache instance.

        Args:
            cache: Shared HintCache. If None a local (non-shared) cache is created.
        """
        self._cache: HintCache = cache if cache is not None else HintCache()

    async def get_hint(
        self,
        db: AsyncSession,
        problem: Problem,
        student_answer: str,
        hint_number: int,
        student_id: int,
        language: str = "en",
    ) -> tuple[str, bool, int | None, int | None]:
        """Return the best available hint for this problem and hint level.

        Resolution order:
        1. HintCache hit → return cached text (is_ai_generated=False).
        2. API key missing → pre-written fallback.
        3. Daily AI rate limit reached → pre-written fallback.
        4. Claude Haiku API call (up to 3 retries with backoff).
        5. All retries fail → pre-written fallback.

        Args:
            db: Active async DB session (read-only; no flush/commit here).
            problem: The Problem ORM instance.
            student_answer: Student's most recent answer string.
            hint_number: Hint level requested (1, 2, or 3).
            student_id: Internal student PK (for rate-limit check).
            language: "en" or "bn" — controls prompt and response language.

        Returns:
            Tuple of (hint_text, is_ai_generated, input_tokens, output_tokens).
            input_tokens and output_tokens are None when is_ai_generated=False.
        """
        # 1. Cache hit (language-scoped — en and bn stored independently)
        cached = self._cache.get(problem.problem_id, hint_number, language)
        if cached is not None:
            logger.debug(
                "hint_cache_hit",
                extra={"problem_id": problem.problem_id, "hint_number": hint_number},
            )
            return cached, False, None, None

        fallback_text = self._fallback(problem, hint_number, language)

        # 2. API key required
        settings = get_settings()
        if not settings.anthropic_api_key:
            logger.debug("hint_generator_no_api_key")
            return fallback_text, False, None, None

        # 3. Daily rate limit
        if await self._ai_hints_today(db, student_id) >= _MAX_AI_HINTS_PER_DAY:
            logger.info(
                "hint_rate_limit_reached",
                extra={"student_id": student_id, "limit": _MAX_AI_HINTS_PER_DAY},
            )
            return fallback_text, False, None, None

        # 4. Claude API with retry
        prompt = self._build_prompt(problem, student_answer, hint_number, language)
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

        for attempt in range(_MAX_RETRIES):
            try:
                response = await client.messages.create(
                    model=_MODEL,
                    max_tokens=_MAX_TOKENS,
                    messages=[{"role": "user", "content": prompt}],
                )
                block = response.content[0]
                hint_text = block.text.strip() if isinstance(block, TextBlock) else ""
                in_tok: int = response.usage.input_tokens
                out_tok: int = response.usage.output_tokens

                # Cache by (problem_id, hint_number, language) so en/bn are independent
                self._cache.set(problem.problem_id, hint_number, language, hint_text)

                logger.info(
                    "hint_ai_generated",
                    extra={
                        "problem_id": problem.problem_id,
                        "hint_number": hint_number,
                        "input_tokens": in_tok,
                        "output_tokens": out_tok,
                        "attempt": attempt + 1,
                    },
                )
                return hint_text, True, in_tok, out_tok

            except (
                anthropic.APIConnectionError,
                anthropic.APITimeoutError,
                anthropic.InternalServerError,
                anthropic.RateLimitError,
            ) as exc:
                if attempt < _MAX_RETRIES - 1:
                    wait = 2**attempt  # 1s, 2s
                    logger.warning(
                        "hint_api_retry",
                        extra={
                            "attempt": attempt + 1,
                            "wait_seconds": wait,
                            "error": str(exc),
                        },
                    )
                    await asyncio.sleep(wait)
                else:
                    logger.error(
                        "hint_api_failed_all_retries",
                        extra={"error": str(exc), "problem_id": problem.problem_id},
                    )

            except (anthropic.AuthenticationError, anthropic.BadRequestError) as exc:
                logger.error(
                    "hint_api_auth_or_billing_error",
                    extra={"error_type": type(exc).__name__, "error": str(exc)},
                )
                break  # No point retrying auth/billing failures

        # 5. All retries exhausted — serve pre-written fallback
        return fallback_text, False, None, None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_prompt(
        self,
        problem: Problem,
        student_answer: str,
        hint_number: int,
        language: str,
    ) -> str:
        """Assemble the Socratic hint prompt for Claude."""
        base = _PROMPT_TEMPLATE.format(
            question=problem.question_en,
            student_answer=student_answer or "(no answer given)",
            correct_answer=problem.answer,
            hint_number=hint_number,
            grade=problem.grade,
        )
        return base + _BENGALI_SUFFIX if language == "bn" else base

    def _fallback(self, problem: Problem, hint_number: int, language: str) -> str:
        """Return the pre-written hint text for the given level and language."""
        hints = problem.get_hints()
        idx = hint_number - 1
        if idx >= len(hints):
            return "কোনো hint পাওয়া যায়নি।" if language == "bn" else "No hint available."
        h = hints[idx].to_dict()
        return str(h["text_bn"] if language == "bn" else h["text_en"])

    async def _ai_hints_today(self, db: AsyncSession, student_id: int) -> int:
        """Count AI-generated hint CostRecords for this student today (UTC).

        AI-generated hints have cost_usd > 0 in the cost_records table.
        Pre-written hints record cost_usd = 0.00 so they do not count.
        """
        today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=UTC)
        result = await db.execute(
            select(func.count(CostRecord.cost_id)).where(
                CostRecord.student_id == student_id,
                CostRecord.operation == OperationType.HINT_GENERATION,
                CostRecord.cost_usd > 0,
                CostRecord.recorded_at >= today_start,
            )
        )
        return int(result.scalar_one())
