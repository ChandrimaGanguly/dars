#!/usr/bin/env python3
"""
Seed script: load all YAML problem files into the problems table.

Usage:
    python scripts/seed_problems.py [--dry-run] [--grade N]

Options:
    --dry-run   Show what would be inserted without making any DB changes.
    --grade N   Only seed problems for the given grade (6, 7, or 8).

Idempotency:
    Uses (grade, topic, question_en) as the uniqueness key.
    Existing problems are skipped; new ones are inserted.
    Running twice produces 0 inserts on the second run.
"""

import argparse
import asyncio
import glob
import logging
import os
import sys
from pathlib import Path

import yaml

# Allow running as a top-level script from the project root.
# Adjust sys.path so that `src` can be imported regardless of cwd.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool  # noqa: E402

from src.models.problem import Problem  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# Content directory relative to project root.
CONTENT_DIR = _PROJECT_ROOT / "content" / "problems"


def get_database_url() -> str:
    """Return async-compatible DB URL from environment, falling back to SQLite for dev.

    Returns:
        Database connection string suitable for SQLAlchemy async engines.

    Raises:
        ValueError: If DATABASE_URL is set but cannot be normalised.
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        # Convenient default for local dev / CI without a full Postgres setup.
        sqlite_path = _PROJECT_ROOT / "test.db"
        url = f"sqlite+aiosqlite:///{sqlite_path}"
        logger.info("DATABASE_URL not set — using SQLite at %s", sqlite_path)
        return url

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return url


def convert_hints(raw_hints: list[dict[str, str]]) -> list[dict[str, object]]:
    """Convert YAML hint format to DB JSON format.

    YAML format:
        hints:
          - en: "Hint in English."
            bn: "ইঙ্গিত বাংলায়।"

    DB format:
        [{"hint_number": 1, "text_en": "...", "text_bn": "...", "is_ai_generated": false}]

    Args:
        raw_hints: List of dicts with keys 'en' and 'bn'.

    Returns:
        List of structured hint dicts with 1-based hint_number.
    """
    converted: list[dict[str, object]] = []
    for i, hint in enumerate(raw_hints, start=1):
        converted.append(
            {
                "hint_number": i,
                "text_en": hint.get("en", ""),
                "text_bn": hint.get("bn", ""),
                "is_ai_generated": False,
            }
        )
    return converted


def validate_and_transform_problem(raw: dict[str, object], source_file: str) -> dict[str, object]:
    """Validate a raw YAML problem dict and transform it to DB insert format.

    Args:
        raw: Raw dict loaded from YAML.
        source_file: Path of source YAML file (for error messages).

    Returns:
        Dict suitable for constructing a Problem ORM instance.

    Raises:
        ValueError: If required fields are missing or invalid.
    """
    # Required fields
    for field in ("grade", "topic", "question_en", "question_bn", "answer", "hints"):
        if field not in raw:
            raise ValueError(
                f"Problem in {source_file} is missing required field '{field}'. "
                f"Problem: {raw.get('question_en', '<no question_en>')!r}"
            )

    raw_hints = raw["hints"]
    if not isinstance(raw_hints, list) or len(raw_hints) == 0:
        raise ValueError(
            f"Problem in {source_file} has empty or invalid 'hints'. "
            f"Must be a non-empty list of {{en, bn}} dicts."
        )

    answer_type = str(raw.get("answer_type", "numeric"))
    if answer_type not in ("numeric", "multiple_choice", "text"):
        logger.warning(
            "Unknown answer_type '%s' in %s — defaulting to 'numeric'",
            answer_type,
            source_file,
        )
        answer_type = "numeric"

    return {
        "grade": int(raw["grade"]),
        "topic": str(raw["topic"]),
        "subtopic": str(raw["subtopic"]) if raw.get("subtopic") else None,
        "question_en": str(raw["question_en"]),
        "question_bn": str(raw["question_bn"]),
        "answer": str(raw["answer"]),
        "hints": convert_hints(raw_hints),
        "difficulty": int(raw.get("difficulty", 1)),
        "answer_type": answer_type,
        "acceptable_tolerance_percent": (
            float(raw["acceptable_tolerance_percent"])
            if raw.get("acceptable_tolerance_percent") is not None
            else None
        ),
        "multiple_choice_options": (
            list(raw["multiple_choice_options"])
            if raw.get("multiple_choice_options") is not None
            else None
        ),
    }


def load_yaml_files(grade_filter: int | None = None) -> list[tuple[str, list[dict[str, object]]]]:
    """Load all YAML problem files from the content directory.

    Handles two YAML top-level formats:
    - List format:  ``- grade: 6\n  topic: ...``  (most files)
    - Dict wrapper: ``problems:\n  - grade: 6\n    ...``  (some files)

    Args:
        grade_filter: If set, only load files for this grade level.

    Returns:
        List of (file_path, list_of_raw_problem_dicts) tuples.
    """
    pattern = (
        str(CONTENT_DIR / f"grade_{grade_filter}" / "*.yaml")
        if grade_filter is not None
        else str(CONTENT_DIR / "grade_*" / "*.yaml")
    )
    files = sorted(glob.glob(pattern))
    if not files:
        logger.warning("No YAML files matched pattern: %s", pattern)
        return []

    result: list[tuple[str, list[dict[str, object]]]] = []
    for file_path in files:
        with open(file_path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        if not data:
            logger.warning("Empty YAML file: %s", file_path)
            continue
        # Normalise: unwrap ``{problems: [...]}`` wrapper if present.
        if isinstance(data, dict):
            if "problems" in data and isinstance(data["problems"], list):
                data = data["problems"]
            else:
                # Unknown dict structure — skip with a warning.
                logger.warning(
                    "Unexpected dict structure in %s (keys: %s) — skipping.",
                    file_path,
                    list(data.keys()),
                )
                continue
        if not isinstance(data, list):
            logger.warning("Unexpected YAML type %s in %s — skipping.", type(data), file_path)
            continue
        result.append((file_path, data))

    return result


async def seed_problems(
    session: AsyncSession,
    file_path: str,
    raw_problems: list[dict[str, object]],
    dry_run: bool = False,
) -> tuple[int, int]:
    """Seed problems from one YAML file into the database.

    Uses (grade, topic, question_en) as the uniqueness key. Existing problems
    are skipped; new ones are inserted (or just counted in dry_run mode).

    Args:
        session: Async SQLAlchemy session (caller manages transaction).
        file_path: Source file path (used for logging and error messages).
        raw_problems: List of raw problem dicts from YAML.
        dry_run: If True, no inserts are performed.

    Returns:
        Tuple of (inserted_count, skipped_count).
    """
    inserted = 0
    skipped = 0

    for raw in raw_problems:
        try:
            transformed = validate_and_transform_problem(raw, file_path)
        except ValueError as exc:
            logger.error("Skipping invalid problem in %s: %s", file_path, exc)
            skipped += 1
            continue

        # Check for existing record using the uniqueness key.
        stmt = select(Problem).where(
            Problem.grade == transformed["grade"],
            Problem.topic == transformed["topic"],
            Problem.question_en == transformed["question_en"],
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            skipped += 1
            continue

        if not dry_run:
            problem = Problem(**transformed)
            session.add(problem)

        inserted += 1

    if not dry_run and inserted > 0:
        await session.flush()

    return inserted, skipped


async def run_seed(dry_run: bool = False, grade_filter: int | None = None) -> None:
    """Main seed entry point.

    Args:
        dry_run: If True, no database writes are performed.
        grade_filter: If set, only seed problems for this grade.
    """
    db_url = get_database_url()
    logger.info("Connecting to: %s (dry_run=%s)", db_url, dry_run)

    is_sqlite = "sqlite" in db_url
    engine = create_async_engine(
        db_url,
        poolclass=NullPool,
        **({"connect_args": {"check_same_thread": False}} if is_sqlite else {}),
    )

    factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    yaml_files = load_yaml_files(grade_filter)
    if not yaml_files:
        logger.warning("No YAML files found. Nothing to seed.")
        await engine.dispose()
        return

    total_inserted = 0
    total_skipped = 0

    async with factory() as session, session.begin():
        for file_path, raw_problems in yaml_files:
            inserted, skipped = await seed_problems(
                session, file_path, raw_problems, dry_run=dry_run
            )
            logger.info(
                "%s: inserted=%d, skipped=%d", file_path, inserted, skipped
            )
            total_inserted += inserted
            total_skipped += skipped

    await engine.dispose()

    action = "Would insert" if dry_run else "Inserted"
    logger.info(
        "Done. %s %d problem(s), skipped %d existing.",
        action,
        total_inserted,
        total_skipped,
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments.

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        description="Seed problems from YAML files into the database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show what would be inserted without making DB changes.",
    )
    parser.add_argument(
        "--grade",
        type=int,
        choices=[6, 7, 8],
        default=None,
        metavar="N",
        help="Only seed problems for grade N (6, 7, or 8).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_seed(dry_run=args.dry_run, grade_filter=args.grade))
