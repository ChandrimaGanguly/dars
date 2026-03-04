"""
Unit tests for scripts/seed_problems.py.

Coverage target: ≥80% of seed_problems module.

Tests:
- test_yaml_load_counts: load one YAML file, assert expected problem count
- test_hint_conversion_hint_number: hints become 1-indexed hint_number
- test_answer_type_defaults_to_numeric: missing answer_type -> "numeric"
- test_idempotent_no_duplicates: running twice -> 0 inserts second time
- test_missing_answer_field_raises: YAML without 'answer' raises ValueError
- test_bilingual_hints_preserved: text_en and text_bn both populated
"""

import sys
from pathlib import Path
from typing import Any

import pytest

# Add project root to sys.path so the script is importable without installation.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Import functions to test from the seed script.
# Note: seed_problems.py lives in scripts/, which is not a package.
# We import it via importlib to avoid hardcoding path assumptions.
import importlib.util  # noqa: E402

from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool  # noqa: E402

from src.models.base import Base  # noqa: E402
from src.models.problem import Problem  # noqa: E402

_SEED_SCRIPT = _PROJECT_ROOT / "scripts" / "seed_problems.py"
_spec = importlib.util.spec_from_file_location("seed_problems", str(_SEED_SCRIPT))
assert _spec is not None and _spec.loader is not None
_seed_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_seed_module)  # type: ignore[union-attr]

convert_hints = _seed_module.convert_hints
validate_and_transform_problem = _seed_module.validate_and_transform_problem
load_yaml_files = _seed_module.load_yaml_files
seed_problems = _seed_module.seed_problems


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_raw_problem(**overrides: Any) -> dict[str, Any]:
    """Return a minimal valid raw problem dict, with optional overrides."""
    base: dict[str, Any] = {
        "grade": 7,
        "topic": "percentages",
        "question_en": "What is 25% of 80?",
        "question_bn": "৮০ এর ২৫% কত?",
        "answer": "20",
        "difficulty": 1,
        "hints": [
            {"en": "Think of 25% as 1/4.", "bn": "প্রথম ইঙ্গিত।"},
            {"en": "Multiply 80 by 0.25.", "bn": "দ্বিতীয় ইঙ্গিত।"},
            {"en": "80 * 0.25 = 20.", "bn": "তৃতীয় ইঙ্গিত।"},
        ],
    }
    base.update(overrides)
    return base


async def _make_test_session():
    """Create an in-memory SQLite engine + session for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    return engine, factory


# ---------------------------------------------------------------------------
# Tests: hint conversion
# ---------------------------------------------------------------------------


class TestConvertHints:
    """Tests for convert_hints()."""

    def test_hint_conversion_hint_number(self) -> None:
        """Hints must become 1-indexed hint_number in DB format."""
        raw_hints = [
            {"en": "First hint.", "bn": "প্রথম ইঙ্গিত।"},
            {"en": "Second hint.", "bn": "দ্বিতীয় ইঙ্গিত।"},
            {"en": "Third hint.", "bn": "তৃতীয় ইঙ্গিত।"},
        ]
        result = convert_hints(raw_hints)
        assert len(result) == 3
        assert result[0]["hint_number"] == 1
        assert result[1]["hint_number"] == 2
        assert result[2]["hint_number"] == 3

    def test_bilingual_hints_preserved(self) -> None:
        """Both text_en and text_bn must be populated from YAML 'en'/'bn' keys."""
        raw_hints = [
            {"en": "English hint text.", "bn": "বাংলা ইঙ্গিত।"},
        ]
        result = convert_hints(raw_hints)
        assert len(result) == 1
        assert result[0]["text_en"] == "English hint text."
        assert result[0]["text_bn"] == "বাংলা ইঙ্গিত।"

    def test_is_ai_generated_defaults_false(self) -> None:
        """All hints from YAML must have is_ai_generated=False."""
        raw_hints = [{"en": "A hint.", "bn": "একটি ইঙ্গিত।"}]
        result = convert_hints(raw_hints)
        assert result[0]["is_ai_generated"] is False

    def test_empty_hints_list_returns_empty(self) -> None:
        """Empty raw hints list returns empty list without error."""
        result = convert_hints([])
        assert result == []


# ---------------------------------------------------------------------------
# Tests: validate_and_transform_problem
# ---------------------------------------------------------------------------


class TestValidateAndTransformProblem:
    """Tests for validate_and_transform_problem()."""

    def test_answer_type_defaults_to_numeric(self) -> None:
        """A problem missing 'answer_type' in YAML must default to 'numeric'."""
        raw = _make_raw_problem()
        # Ensure answer_type is absent.
        raw.pop("answer_type", None)
        result = validate_and_transform_problem(raw, "test.yaml")
        assert result["answer_type"] == "numeric"

    def test_explicit_answer_type_preserved(self) -> None:
        """Explicit answer_type in YAML must be preserved."""
        raw = _make_raw_problem(answer_type="text")
        result = validate_and_transform_problem(raw, "test.yaml")
        assert result["answer_type"] == "text"

    def test_missing_answer_field_raises(self) -> None:
        """A problem missing 'answer' must raise ValueError."""
        raw = _make_raw_problem()
        del raw["answer"]
        with pytest.raises(ValueError, match="answer"):
            validate_and_transform_problem(raw, "test.yaml")

    def test_missing_question_en_raises(self) -> None:
        """A problem missing 'question_en' must raise ValueError."""
        raw = _make_raw_problem()
        del raw["question_en"]
        with pytest.raises(ValueError, match="question_en"):
            validate_and_transform_problem(raw, "test.yaml")

    def test_missing_hints_raises(self) -> None:
        """A problem missing 'hints' must raise ValueError."""
        raw = _make_raw_problem()
        del raw["hints"]
        with pytest.raises(ValueError, match="hints"):
            validate_and_transform_problem(raw, "test.yaml")

    def test_empty_hints_raises(self) -> None:
        """A problem with empty hints list must raise ValueError."""
        raw = _make_raw_problem(hints=[])
        with pytest.raises(ValueError, match="empty"):
            validate_and_transform_problem(raw, "test.yaml")

    def test_unknown_answer_type_falls_back_to_numeric(self) -> None:
        """Unknown answer_type must be silently normalised to 'numeric'."""
        raw = _make_raw_problem(answer_type="unknown_type")
        result = validate_and_transform_problem(raw, "test.yaml")
        assert result["answer_type"] == "numeric"

    def test_subtopic_optional(self) -> None:
        """Subtopic is optional and defaults to None when absent."""
        raw = _make_raw_problem()
        raw.pop("subtopic", None)
        result = validate_and_transform_problem(raw, "test.yaml")
        assert result["subtopic"] is None

    def test_difficulty_defaults_to_1(self) -> None:
        """Difficulty defaults to 1 when absent."""
        raw = _make_raw_problem()
        del raw["difficulty"]
        result = validate_and_transform_problem(raw, "test.yaml")
        assert result["difficulty"] == 1

    def test_tolerance_percent_passed_through(self) -> None:
        """acceptable_tolerance_percent is included in output when present."""
        raw = _make_raw_problem(acceptable_tolerance_percent=5.0)
        result = validate_and_transform_problem(raw, "test.yaml")
        assert result["acceptable_tolerance_percent"] == 5.0

    def test_multiple_choice_options_passed_through(self) -> None:
        """multiple_choice_options are included in output when present."""
        options = ["a", "b", "c", "d"]
        raw = _make_raw_problem(answer_type="multiple_choice", multiple_choice_options=options)
        result = validate_and_transform_problem(raw, "test.yaml")
        assert result["multiple_choice_options"] == options


# ---------------------------------------------------------------------------
# Tests: load_yaml_files
# ---------------------------------------------------------------------------


class TestLoadYamlFiles:
    """Tests for load_yaml_files()."""

    def test_yaml_load_counts(self) -> None:
        """Loading a known YAML file should return the expected number of problems."""
        # Use grade_7/percentages.yaml which has 30 problems.
        grade7_files = load_yaml_files(grade_filter=7)
        percentages_file = [(path, probs) for path, probs in grade7_files if "percentages" in path]
        assert len(percentages_file) == 1, "percentages.yaml not found for grade 7"
        _, problems = percentages_file[0]
        assert len(problems) == 30, f"Expected 30 percentages problems, got {len(problems)}"

    def test_load_all_grades_returns_problems(self) -> None:
        """Loading all grades must return at least 100 problems across all files."""
        all_files = load_yaml_files()
        total = sum(len(probs) for _, probs in all_files)
        assert total >= 100, f"Expected ≥100 total problems, got {total}"

    def test_grade_filter_only_returns_that_grade(self) -> None:
        """grade_filter=6 must only return grade 6 problem files."""
        grade6_files = load_yaml_files(grade_filter=6)
        assert len(grade6_files) > 0
        for path, _ in grade6_files:
            assert "grade_6" in path

    def test_invalid_grade_returns_empty(self) -> None:
        """grade_filter=5 (non-existent) must return empty list without error."""
        result = load_yaml_files(grade_filter=5)  # type: ignore[arg-type]
        assert result == []


# ---------------------------------------------------------------------------
# Tests: seed_problems (async, with in-memory DB)
# ---------------------------------------------------------------------------


class TestSeedProblems:
    """Integration-style tests for seed_problems() using in-memory SQLite."""

    @pytest.fixture
    def sample_raw_problems(self) -> list[dict[str, Any]]:
        """Return a list of valid raw problems for seeding tests."""
        return [
            _make_raw_problem(
                question_en="What is 25% of 80?",
                question_bn="৮০ এর ২৫% কত?",
                answer="20",
                answer_type="numeric",
            ),
            _make_raw_problem(
                question_en="What is 50% of 200?",
                question_bn="২০০ এর ৫০% কত?",
                answer="100",
                answer_type="numeric",
            ),
        ]

    @pytest.mark.asyncio
    async def test_seed_inserts_problems(self, sample_raw_problems: list[dict[str, Any]]) -> None:
        """Seeding valid problems must insert them into the database."""
        engine, factory = await _make_test_session()
        async with factory() as session, session.begin():
            inserted, skipped = await seed_problems(
                session, "test.yaml", sample_raw_problems, dry_run=False
            )
        assert inserted == 2
        assert skipped == 0
        await engine.dispose()

    @pytest.mark.asyncio
    async def test_idempotent_no_duplicates(
        self, sample_raw_problems: list[dict[str, Any]]
    ) -> None:
        """Running seed twice must produce 0 inserts on the second run."""
        engine, factory = await _make_test_session()

        # First run: inserts 2.
        async with factory() as session, session.begin():
            inserted1, skipped1 = await seed_problems(
                session, "test.yaml", sample_raw_problems, dry_run=False
            )
        assert inserted1 == 2
        assert skipped1 == 0

        # Second run: skips both.
        async with factory() as session, session.begin():
            inserted2, skipped2 = await seed_problems(
                session, "test.yaml", sample_raw_problems, dry_run=False
            )
        assert inserted2 == 0
        assert skipped2 == 2
        await engine.dispose()

    @pytest.mark.asyncio
    async def test_dry_run_does_not_insert(self, sample_raw_problems: list[dict[str, Any]]) -> None:
        """dry_run=True must report inserts but not write to the database."""
        from sqlalchemy import select

        engine, factory = await _make_test_session()
        async with factory() as session, session.begin():
            inserted, skipped = await seed_problems(
                session, "test.yaml", sample_raw_problems, dry_run=True
            )
        assert inserted == 2
        assert skipped == 0

        # Verify nothing was actually written.
        async with factory() as session:
            result = await session.execute(select(Problem))
            rows = result.scalars().all()
        assert len(rows) == 0, "dry_run should not write to the database"
        await engine.dispose()

    @pytest.mark.asyncio
    async def test_invalid_problem_is_skipped_not_aborted(self) -> None:
        """A single invalid problem must be skipped; valid ones still insert."""
        bad_problem: dict[str, Any] = {"grade": 7, "topic": "test"}  # missing answer
        good_problem = _make_raw_problem(question_en="Good one?", question_bn="ভালো?")
        raw_problems = [bad_problem, good_problem]

        engine, factory = await _make_test_session()
        async with factory() as session, session.begin():
            inserted, skipped = await seed_problems(
                session, "test.yaml", raw_problems, dry_run=False
            )
        # bad_problem is skipped due to ValueError; good_problem is inserted.
        assert inserted == 1
        assert skipped == 1
        await engine.dispose()
