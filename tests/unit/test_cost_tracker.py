"""Unit tests for PHASE3-C-3: CostTracker service.

Tests verify:
  - record_hint_cost creates a CostRecord in the DB session.
  - Pre-written hints always have cost_usd = 0.00.
  - AI-generated hints calculate cost from token counts.
  - check_budget_alert returns True above the $0.10 ceiling and False below.
  - get_student_cost_this_month sums only the current calendar month.
  - Budget alert logs a WARNING with severity=HIGH.

All tests use mocked database sessions (no live DB required).
"""

import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.services.cost_tracker import (
    BUDGET_PER_STUDENT_USD,
    HAIKU_INPUT_COST_PER_TOKEN,
    HAIKU_OUTPUT_COST_PER_TOKEN,
    CostTracker,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_db() -> AsyncMock:
    """Return a minimal mock AsyncSession with add() and flush() available."""
    db = AsyncMock()
    db.add = MagicMock()  # synchronous add
    db.flush = AsyncMock()
    return db


def _make_scalar_result(value: float) -> MagicMock:
    """Return a mock DB result that returns `value` from scalar_one()."""
    result = MagicMock()
    result.scalar_one = MagicMock(return_value=value)
    return result


# ---------------------------------------------------------------------------
# TestRecordHintCost
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRecordHintCost:
    """Tests for CostTracker.record_hint_cost()."""

    @pytest.mark.asyncio
    async def test_record_hint_creates_cost_record(self) -> None:
        """record_hint_cost must add a CostRecord to the DB session."""
        db = _make_db()
        tracker = CostTracker()

        await tracker.record_hint_cost(
            db=db,
            student_id=1,
            session_id=10,
            hint_number=1,
        )

        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_hint_cost_is_zero_in_phase3(self) -> None:
        """Pre-written hint (is_ai_generated=False) must produce cost_usd = 0.00."""
        db = _make_db()
        tracker = CostTracker()

        record = await tracker.record_hint_cost(
            db=db,
            student_id=1,
            session_id=10,
            hint_number=1,
            is_ai_generated=False,
        )

        assert record.cost_usd == 0.0

    @pytest.mark.asyncio
    async def test_hint_cost_is_zero_when_no_tokens(self) -> None:
        """is_ai_generated=True but no token counts → cost must still be 0.00."""
        db = _make_db()
        tracker = CostTracker()

        record = await tracker.record_hint_cost(
            db=db,
            student_id=1,
            session_id=10,
            hint_number=2,
            is_ai_generated=True,
            input_tokens=None,
            output_tokens=None,
        )

        assert record.cost_usd == 0.0

    @pytest.mark.asyncio
    async def test_ai_hint_calculates_cost_from_tokens(self) -> None:
        """AI-generated hint with token counts must calculate correct cost."""
        db = _make_db()
        tracker = CostTracker()

        input_tokens = 100
        output_tokens = 50
        expected_cost = (
            input_tokens * HAIKU_INPUT_COST_PER_TOKEN + output_tokens * HAIKU_OUTPUT_COST_PER_TOKEN
        )

        record = await tracker.record_hint_cost(
            db=db,
            student_id=1,
            session_id=10,
            hint_number=1,
            is_ai_generated=True,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        assert abs(record.cost_usd - expected_cost) < 1e-10

    @pytest.mark.asyncio
    async def test_record_uses_hint_generation_operation(self) -> None:
        """CostRecord must have operation='hint_generation'."""
        from src.models.cost_record import OperationType

        db = _make_db()
        tracker = CostTracker()

        record = await tracker.record_hint_cost(
            db=db,
            student_id=5,
            session_id=20,
            hint_number=3,
        )

        assert record.operation == OperationType.HINT_GENERATION

    @pytest.mark.asyncio
    async def test_record_uses_claude_provider(self) -> None:
        """CostRecord must have api_provider='claude'."""
        from src.models.cost_record import ApiProvider

        db = _make_db()
        tracker = CostTracker()

        record = await tracker.record_hint_cost(
            db=db,
            student_id=5,
            session_id=20,
            hint_number=1,
        )

        assert record.api_provider == ApiProvider.CLAUDE

    @pytest.mark.asyncio
    async def test_record_stores_correct_student_id(self) -> None:
        """CostRecord must carry the correct student_id."""
        db = _make_db()
        tracker = CostTracker()

        record = await tracker.record_hint_cost(
            db=db,
            student_id=42,
            session_id=10,
            hint_number=1,
        )

        assert record.student_id == 42

    @pytest.mark.asyncio
    async def test_record_stores_correct_session_id(self) -> None:
        """CostRecord must carry the correct session_id."""
        db = _make_db()
        tracker = CostTracker()

        record = await tracker.record_hint_cost(
            db=db,
            student_id=1,
            session_id=99,
            hint_number=1,
        )

        assert record.session_id == 99

    @pytest.mark.asyncio
    async def test_record_allows_null_session_id(self) -> None:
        """session_id is nullable — None must be accepted."""
        db = _make_db()
        tracker = CostTracker()

        record = await tracker.record_hint_cost(
            db=db,
            student_id=1,
            session_id=None,
            hint_number=1,
        )

        assert record.session_id is None


# ---------------------------------------------------------------------------
# TestCheckBudgetAlert
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCheckBudgetAlert:
    """Tests for CostTracker.check_budget_alert()."""

    @pytest.mark.asyncio
    async def test_budget_alert_triggers_at_10_cents(self) -> None:
        """Monthly cost > $0.10 must return True."""
        db = AsyncMock()
        # Simulate get_student_cost_this_month returning $0.11
        db.execute = AsyncMock(return_value=_make_scalar_result(0.11))

        tracker = CostTracker()
        result = await tracker.check_budget_alert(db=db, student_id=1)

        assert result is True

    @pytest.mark.asyncio
    async def test_budget_alert_does_not_trigger_below_10_cents(self) -> None:
        """Monthly cost < $0.10 must return False."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_make_scalar_result(0.05))

        tracker = CostTracker()
        result = await tracker.check_budget_alert(db=db, student_id=1)

        assert result is False

    @pytest.mark.asyncio
    async def test_budget_alert_does_not_trigger_at_exact_ceiling(self) -> None:
        """Monthly cost == $0.10 exactly must return False (not over budget)."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_make_scalar_result(0.10))

        tracker = CostTracker()
        result = await tracker.check_budget_alert(db=db, student_id=1)

        assert result is False

    @pytest.mark.asyncio
    async def test_budget_alert_logs_warning_when_over(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Budget alert must emit a WARNING log when over budget."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_make_scalar_result(0.15))

        tracker = CostTracker()

        with caplog.at_level(logging.WARNING, logger="src.services.cost_tracker"):
            await tracker.check_budget_alert(db=db, student_id=1)

        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warning_records) >= 1

    @pytest.mark.asyncio
    async def test_budget_alert_warning_contains_severity_high(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Budget alert WARNING must contain severity=HIGH."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_make_scalar_result(0.20))

        tracker = CostTracker()

        with caplog.at_level(logging.WARNING, logger="src.services.cost_tracker"):
            await tracker.check_budget_alert(db=db, student_id=1)

        combined = " ".join(str(r.__dict__) for r in caplog.records)
        assert "HIGH" in combined

    @pytest.mark.asyncio
    async def test_budget_alert_no_warning_when_under(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """No WARNING should be emitted when student is under budget."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_make_scalar_result(0.03))

        tracker = CostTracker()

        with caplog.at_level(logging.WARNING, logger="src.services.cost_tracker"):
            await tracker.check_budget_alert(db=db, student_id=1)

        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warning_records) == 0

    @pytest.mark.asyncio
    async def test_budget_alert_zero_cost_is_safe(self) -> None:
        """Zero cost must always return False — no false positives."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_make_scalar_result(0.0))

        tracker = CostTracker()
        result = await tracker.check_budget_alert(db=db, student_id=1)

        assert result is False


# ---------------------------------------------------------------------------
# TestGetMonthlyCost
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetMonthlyCost:
    """Tests for CostTracker.get_student_cost_this_month()."""

    @pytest.mark.asyncio
    async def test_get_monthly_cost_returns_sum(self) -> None:
        """get_student_cost_this_month must return the DB aggregate value."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_make_scalar_result(0.07))

        tracker = CostTracker()
        result = await tracker.get_student_cost_this_month(db=db, student_id=1)

        assert abs(result - 0.07) < 1e-10

    @pytest.mark.asyncio
    async def test_get_monthly_cost_returns_zero_on_no_records(self) -> None:
        """NULL from DB aggregate (no records) must be coalesced to 0.0."""
        db = AsyncMock()
        # coalesce(..., 0.0) means the DB returns 0.0 for empty
        db.execute = AsyncMock(return_value=_make_scalar_result(0.0))

        tracker = CostTracker()
        result = await tracker.get_student_cost_this_month(db=db, student_id=99)

        assert result == 0.0

    @pytest.mark.asyncio
    async def test_get_monthly_cost_returns_float(self) -> None:
        """Return type must be float (not Decimal or other numeric type)."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_make_scalar_result(0.05))

        tracker = CostTracker()
        result = await tracker.get_student_cost_this_month(db=db, student_id=1)

        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# TestCostTrackerConstants
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCostTrackerConstants:
    """Tests verifying the pricing constants match expected values."""

    def test_haiku_input_cost_per_token(self) -> None:
        """Input cost must be $0.25 / 1M tokens."""
        expected = 0.25 / 1_000_000
        assert abs(HAIKU_INPUT_COST_PER_TOKEN - expected) < 1e-15

    def test_haiku_output_cost_per_token(self) -> None:
        """Output cost must be $1.25 / 1M tokens."""
        expected = 1.25 / 1_000_000
        assert abs(HAIKU_OUTPUT_COST_PER_TOKEN - expected) < 1e-15

    def test_budget_ceiling_is_10_cents(self) -> None:
        """Budget ceiling must be $0.10 per student per month."""
        assert BUDGET_PER_STUDENT_USD == 0.10
