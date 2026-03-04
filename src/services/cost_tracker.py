"""Cost tracking for Claude API hint generation and future AI calls.

PHASE3-C-3: CostTracker service.

Phase 3 role (stub phase):
  - Records every hint request as a CostRecord with cost_usd=0.00.
  - Pre-written hints have no real AI cost, but the record must exist so
    Phase 4 (real Claude integration) only needs to pass is_ai_generated=True
    plus token counts — no endpoint or service changes required.

Phase 4 transition:
  - Pass is_ai_generated=True and real input_tokens/output_tokens to
    record_hint_cost(). The cost calculation happens here automatically.
  - Endpoint code (src/routes/practice.py) does NOT need to change.

Budget ceiling: <$0.10/student/month (CLAUDE.md non-negotiable constraint).
Alert threshold: > $0.10/student triggers WARNING log (PHASE3-C-3.4).

Claude Haiku pricing (2026):
  $0.25 / 1M input tokens
  $1.25 / 1M output tokens
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.cost_record import ApiProvider, CostRecord, OperationType

logger = logging.getLogger(__name__)

# Claude Haiku pricing (2026 rates)
HAIKU_INPUT_COST_PER_TOKEN: float = 0.25 / 1_000_000
HAIKU_OUTPUT_COST_PER_TOKEN: float = 1.25 / 1_000_000

# Non-negotiable budget ceiling from CLAUDE.md
BUDGET_PER_STUDENT_USD: float = 0.10


class CostTracker:
    """Track API costs for the $0.10/student/month ceiling.

    All hint requests — pre-written or AI-generated — create a CostRecord.
    This ensures the audit trail is complete and Phase 4 requires no
    structural changes to enable real cost tracking.

    Attributes:
        None (stateless — all state lives in the database).
    """

    async def record_hint_cost(
        self,
        db: AsyncSession,
        student_id: int,
        session_id: int | None,
        hint_number: int,
        is_ai_generated: bool = False,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
    ) -> CostRecord:
        """Create a CostRecord for a hint request.

        Phase 3: cost_usd = 0.00 (is_ai_generated=False, no tokens).
        Phase 4: pass is_ai_generated=True with real token counts to record
                 the actual Claude Haiku cost automatically.

        Args:
            db: Async database session (caller manages the transaction).
            student_id: Internal student PK (not telegram_id).
            session_id: Session PK (nullable — hint may arrive without session).
            hint_number: Which hint was served (1, 2, or 3).
            is_ai_generated: True if hint came from Claude API (Phase 4+).
            input_tokens: Claude input token count (Phase 4+ only).
            output_tokens: Claude output token count (Phase 4+ only).

        Returns:
            Persisted CostRecord (flushed but not committed — caller commits).

        Raises:
            SQLAlchemyError: Propagated from db.flush() if DB write fails.
        """
        cost_usd: float = 0.0
        if is_ai_generated and input_tokens is not None and output_tokens is not None:
            cost_usd = (
                input_tokens * HAIKU_INPUT_COST_PER_TOKEN
                + output_tokens * HAIKU_OUTPUT_COST_PER_TOKEN
            )

        cost_record = CostRecord(
            student_id=student_id,
            session_id=session_id,
            operation=OperationType.HINT_GENERATION,
            api_provider=ApiProvider.CLAUDE,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            recorded_at=datetime.now(UTC),
        )
        db.add(cost_record)

        # Flush so cost_id is populated and record survives disconnect
        await db.flush()

        logger.info(
            "Hint cost recorded",
            extra={
                "event": "cost.hint_recorded",
                "student_id": student_id,
                "session_id": session_id,
                "hint_number": hint_number,
                "is_ai_generated": is_ai_generated,
                "cost_usd": cost_usd,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        )

        return cost_record

    async def get_student_cost_this_month(
        self,
        db: AsyncSession,
        student_id: int,
    ) -> float:
        """Sum all cost_usd for this student in the current calendar month.

        Uses UTC month boundaries. Filters to hint_generation operations
        and the Claude provider (primary cost driver).

        Args:
            db: Async database session.
            student_id: Internal student PK.

        Returns:
            Total cost in USD for this student this month (0.0 if no records).
        """
        now = datetime.now(UTC)
        # First moment of the current month (UTC)
        month_start = datetime(now.year, now.month, 1, tzinfo=UTC)

        result = await db.execute(
            select(func.coalesce(func.sum(CostRecord.cost_usd), 0.0)).where(
                CostRecord.student_id == student_id,
                CostRecord.recorded_at >= month_start,
            )
        )
        total: float = result.scalar_one()
        return float(total)

    async def check_budget_alert(
        self,
        db: AsyncSession,
        student_id: int,
    ) -> bool:
        """Return True if this student has exceeded the $0.10/month budget ceiling.

        Logs a WARNING if the ceiling is exceeded so operations can respond.
        The $0.10 ceiling is non-negotiable per CLAUDE.md.

        Args:
            db: Async database session.
            student_id: Internal student PK.

        Returns:
            True if monthly cost > BUDGET_PER_STUDENT_USD, False otherwise.
        """
        monthly_cost = await self.get_student_cost_this_month(db, student_id)
        over_budget = monthly_cost > BUDGET_PER_STUDENT_USD

        if over_budget:
            logger.warning(
                "Student has exceeded monthly budget ceiling",
                extra={
                    "event": "cost.budget_alert",
                    "student_id": student_id,
                    "monthly_cost_usd": monthly_cost,
                    "budget_ceiling_usd": BUDGET_PER_STUDENT_USD,
                    "overage_usd": monthly_cost - BUDGET_PER_STUDENT_USD,
                    "severity": "HIGH",
                },
            )

        return over_budget
