"""
Problem selection algorithm for daily practice sessions.

Implements REQ-008: Intelligent problem selection using a 50/30/20 weighted scoring
algorithm that balances topic recency, mastery, and difficulty variation.

Algorithm weights (confirmed for MVP):
    score(problem) = 0.50 * recency_score + 0.30 * mastery_score + 0.20 * difficulty_score

Design notes:
    - ProblemRepository and ResponseRepository are defined as Protocols here so this
      service can be developed and tested independently of Maryam's Track A work.
    - Once PHASE3-A-2 delivers the real repositories, they will satisfy these Protocols
      structurally (duck-typing) with no changes needed here.
    - All scoring is computed in Python from pre-fetched data to keep queries simple and
      avoid N+1 issues. With 280 problems this is well within memory budget.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.problem import Problem

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROBLEMS_PER_SESSION: int = 5
RECENCY_WINDOW_DAYS: int = 7
MASTERY_WINDOW_DAYS: int = 30
MASTERY_LOW_THRESHOLD: float = 0.60  # Below 60% accuracy → high mastery need
NEW_TOPIC_MASTERY_SCORE: float = 0.50  # Neutral score for topics with no history

# Target difficulty distribution: 40% easy, 40% medium, 20% hard
TARGET_DIFFICULTY_DISTRIBUTION: dict[int, float] = {1: 0.40, 2: 0.40, 3: 0.20}

# Algorithm weights — confirmed for MVP (REQ-008)
WEIGHT_RECENCY: float = 0.50
WEIGHT_MASTERY: float = 0.30
WEIGHT_DIFFICULTY: float = 0.20


# ---------------------------------------------------------------------------
# Repository Protocols
# ---------------------------------------------------------------------------
# These Protocols define the minimal interface this service needs from the
# repository layer. The real implementations (delivered by PHASE3-A-2) must
# satisfy these contracts. Tests use AsyncMock objects that also satisfy them.


class ProblemRepository(Protocol):
    """Minimal interface for problem data access used by ProblemSelector."""

    async def get_by_grade(
        self,
        db: AsyncSession,
        grade: int,
    ) -> list[Problem]:
        """Return all problems for the given grade.

        Args:
            db: Active async database session.
            grade: Grade level (6, 7, or 8).

        Returns:
            List of Problem ORM objects for that grade. May be empty.
        """
        ...


class ResponseRepository(Protocol):
    """Minimal interface for response data access used by ProblemSelector."""

    async def get_recent_by_student(
        self,
        db: AsyncSession,
        student_id: int,
        since: datetime,
    ) -> list[dict[str, object]]:
        """Return recent responses for the student since a given timestamp.

        Each dict must contain:
            - "problem_id": int — ID of the problem answered
            - "topic": str — topic of the problem (denormalised for efficiency)
            - "is_correct": bool — whether the answer was correct
            - "answered_at": datetime — UTC timestamp of the answer

        Args:
            db: Active async database session.
            student_id: The student's primary key.
            since: Only return responses at or after this UTC datetime.

        Returns:
            List of response dicts. Empty list for new students.
        """
        ...


# ---------------------------------------------------------------------------
# Internal data structures
# ---------------------------------------------------------------------------


class _TopicStats:
    """Aggregated statistics for a single topic in a student's history."""

    __slots__ = ("correct_answers", "last_answered_at", "total_answers")

    def __init__(self) -> None:
        self.total_answers: int = 0
        self.correct_answers: int = 0
        self.last_answered_at: datetime | None = None

    def record(self, is_correct: bool, answered_at: datetime) -> None:
        """Update stats with one response."""
        self.total_answers += 1
        if is_correct:
            self.correct_answers += 1
        if self.last_answered_at is None or answered_at > self.last_answered_at:
            self.last_answered_at = answered_at

    @property
    def accuracy(self) -> float:
        """Return accuracy in [0.0, 1.0]. Returns 0.0 for no answers."""
        if self.total_answers == 0:
            return 0.0
        return self.correct_answers / self.total_answers


# ---------------------------------------------------------------------------
# ProblemSelector service
# ---------------------------------------------------------------------------


class ProblemSelector:
    """Select 5 problems per student using a weighted scoring algorithm.

    Algorithm (REQ-008):
        score(problem) = 0.50 * recency_score
                       + 0.30 * mastery_score
                       + 0.20 * difficulty_score

    Tie-breaking:
        When two problems have identical final scores, the problem with the
        lower problem_id wins. This guarantees determinism: identical inputs
        always produce identical outputs.

    Performance:
        All problems for a grade are fetched in a single query. Scoring is
        done in Python. With ≤320 problems per grade this is well within the
        <500ms budget including network latency.
    """

    def __init__(
        self,
        problem_repo: ProblemRepository | None = None,
        response_repo: ResponseRepository | None = None,
    ) -> None:
        self._problem_repo = problem_repo
        self._response_repo = response_repo

    async def select_problems(
        self,
        db: AsyncSession,
        student_id: int,
        grade: int,
        difficulty_level: int = 0,
        problem_repo: ProblemRepository | None = None,
        response_repo: ResponseRepository | None = None,
    ) -> list[Problem]:
        """Select up to 5 problems for a student's daily practice session.

        Returns exactly 5 problems when the grade has 5 or more problems.
        Returns all available problems when the grade has fewer than 5.

        Args:
            student_id: Primary key of the student.
            grade: Grade level (6, 7, or 8).
            difficulty_level: Student's adaptive difficulty level (1-3).
                When >0, only problems with difficulty ≤ difficulty_level are
                considered. 0 means no filtering (backward-compatible default).
            db: Active async database session.
            problem_repo: Repository for fetching problems.
            response_repo: Repository for fetching student responses.

        Returns:
            Ordered list of Problem objects (best-scoring first). Length is
            min(5, len(available_problems)).
        """
        now = datetime.now(UTC)
        p_repo = problem_repo if problem_repo is not None else self._problem_repo
        r_repo = response_repo if response_repo is not None else self._response_repo
        if p_repo is None or r_repo is None:
            raise ValueError(
                "ProblemSelector requires problem_repo and response_repo. "
                "Pass them to __init__ or to select_problems()."
            )

        # Fetch all problems for this grade (single query)
        problems = await p_repo.get_by_grade(db=db, grade=grade)

        # Filter by adaptive difficulty level when specified (REQ-004)
        if difficulty_level > 0:
            problems = [p for p in problems if p.difficulty <= difficulty_level]

        if not problems:
            logger.info("No problems found for grade %d (student_id=%d)", grade, student_id)
            return []

        # Fetch recent responses (covers recency + mastery windows)
        mastery_since = now - timedelta(days=MASTERY_WINDOW_DAYS)
        responses = await r_repo.get_recent_by_student(
            db=db,
            student_id=student_id,
            since=mastery_since,
        )

        # Build topic-level statistics from the fetched responses
        topic_stats = self._build_topic_stats(responses)

        # Identify problem IDs seen in the shorter recency window
        recency_cutoff = now - timedelta(days=RECENCY_WINDOW_DAYS)
        recently_seen_ids = self._recently_seen_problem_ids(responses, recency_cutoff)

        # Pre-compute difficulty distribution across ALL candidates.
        # This makes the difficulty score static and order-independent — critical
        # for determinism and correct tie-breaking.
        difficulty_counts: dict[int, int] = {1: 0, 2: 0, 3: 0}
        for p in problems:
            difficulty_counts[p.difficulty] = difficulty_counts.get(p.difficulty, 0) + 1

        # Score every candidate problem
        scored: list[tuple[float, int, Problem]] = []
        for problem in problems:
            score = self._score_problem(
                problem=problem,
                topic_stats=topic_stats,
                recently_seen_ids=recently_seen_ids,
                difficulty_counts=difficulty_counts,
            )
            # Store (score, problem_id, problem) for sorting
            scored.append((score, problem.problem_id, problem))

        # Sort: highest score first, then lowest problem_id on tie
        scored.sort(key=lambda t: (-t[0], t[1]))

        # Return top N, ordered easy → hard for static learning path
        n = min(PROBLEMS_PER_SESSION, len(scored))
        selected = [problem for _, _, problem in scored[:n]]
        selected.sort(key=lambda p: p.difficulty)

        logger.info(
            "Selected %d problems for student_id=%d grade=%d",
            len(selected),
            student_id,
            grade,
        )
        return selected

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_topic_stats(
        self,
        responses: list[dict[str, object]],
    ) -> dict[str, _TopicStats]:
        """Build per-topic statistics from a list of response dicts.

        Args:
            responses: List of response dicts with keys: problem_id, topic,
                is_correct, answered_at.

        Returns:
            Mapping from topic name to _TopicStats.
        """
        stats: dict[str, _TopicStats] = {}
        for resp in responses:
            topic = str(resp["topic"])
            is_correct = bool(resp["is_correct"])
            answered_at = resp["answered_at"]
            if not isinstance(answered_at, datetime):
                # Defensive: skip malformed entries
                continue
            if topic not in stats:
                stats[topic] = _TopicStats()
            stats[topic].record(is_correct=is_correct, answered_at=answered_at)
        return stats

    def _recently_seen_problem_ids(
        self,
        responses: list[dict[str, object]],
        cutoff: datetime,
    ) -> set[int]:
        """Return IDs of problems answered at or after cutoff.

        Args:
            responses: Response dicts from response_repo.
            cutoff: UTC datetime; responses on or after this are "recent".

        Returns:
            Set of problem_id integers seen recently.
        """
        seen: set[int] = set()
        for resp in responses:
            answered_at = resp.get("answered_at")
            if not isinstance(answered_at, datetime):
                continue
            if answered_at >= cutoff:
                seen.add(int(str(resp["problem_id"])))
        return seen

    def _score_problem(
        self,
        problem: Problem,
        topic_stats: dict[str, _TopicStats],
        recently_seen_ids: set[int],
        difficulty_counts: dict[int, int],
    ) -> float:
        """Compute the composite score for one problem.

        Args:
            problem: Candidate problem to score.
            topic_stats: Aggregated per-topic history for this student.
            recently_seen_ids: Set of problem IDs seen in the recency window.
            difficulty_counts: Total count of each difficulty level across all
                candidate problems (used to compute a static difficulty score).

        Returns:
            Score in [0.0, 1.0] — higher means the problem is more desirable.
        """
        recency = self._recency_score(problem, recently_seen_ids)
        mastery = self._mastery_score(problem, topic_stats)
        difficulty = self._difficulty_score_static(problem, difficulty_counts)
        return WEIGHT_RECENCY * recency + WEIGHT_MASTERY * mastery + WEIGHT_DIFFICULTY * difficulty

    def _recency_score(
        self,
        problem: Problem,
        recently_seen_ids: set[int],
    ) -> float:
        """Compute recency score.

        Problems NOT seen in the last 7 days score 1.0.
        Problems seen recently score 0.0.

        Args:
            problem: The candidate problem.
            recently_seen_ids: Set of recently-seen problem IDs.

        Returns:
            1.0 if not recently seen, 0.0 otherwise.
        """
        if problem.problem_id in recently_seen_ids:
            return 0.0
        return 1.0

    def _mastery_score(
        self,
        problem: Problem,
        topic_stats: dict[str, _TopicStats],
    ) -> float:
        """Compute mastery score for a problem's topic.

        Low accuracy (< 60%) → high score (student needs more practice).
        New topic (no history) → neutral score (0.5).
        High accuracy (≥ 60%) → lower score (inversely proportional to accuracy).

        Args:
            problem: The candidate problem.
            topic_stats: Per-topic aggregated history.

        Returns:
            Mastery score in [0.0, 1.0].
        """
        stats = topic_stats.get(problem.topic)
        if stats is None or stats.total_answers == 0:
            return NEW_TOPIC_MASTERY_SCORE

        accuracy = stats.accuracy
        # Inverse of accuracy: lower accuracy → higher mastery need score
        # Clamp to [0.0, 1.0] — accuracy is already in [0.0, 1.0]
        return 1.0 - accuracy

    def _difficulty_score_static(
        self,
        problem: Problem,
        difficulty_counts: dict[int, int],
    ) -> float:
        """Compute a static difficulty score that biases selection toward the target mix.

        The score is designed to nudge the 5-problem selection toward the target
        distribution (40% easy, 40% medium, 20% hard) while remaining completely
        independent of iteration order (fully deterministic).

        Strategy:
        - If the candidate pool has an over-representation of a difficulty level
          (more of that difficulty than the target proportion), problems of that
          difficulty receive a lower score — the pool "doesn't need" to bias toward
          them because they will naturally appear.
        - If a difficulty is absent from the pool entirely, problems that match it
          can't appear at all, so we score 0.0 (no effect).
        - The score is target_proportion / actual_proportion, clamped to [0.0, 1.0].
          This rewards under-represented difficulties and penalises over-represented ones.

        Example with a balanced pool (equal 10/10/10 split):
          - Easy  (target 40%, actual 33%): score = 0.40/0.33 = 1.2 → clamped to 1.0
          - Medium (target 40%, actual 33%): score = 1.0
          - Hard  (target 20%, actual 33%): score = 0.20/0.33 = 0.60

        This correctly penalises hard problems (over-represented relative to target)
        and equally rewards easy and medium (both under-represented).

        Args:
            problem: The candidate problem.
            difficulty_counts: Total count of each difficulty (1/2/3) across
                all candidate problems fetched from the database.

        Returns:
            Difficulty score in [0.0, 1.0].
        """
        target_proportion = TARGET_DIFFICULTY_DISTRIBUTION.get(problem.difficulty, 0.0)
        if target_proportion == 0.0:
            return 0.0

        total = sum(difficulty_counts.values())
        if total == 0:
            return target_proportion

        actual_proportion = difficulty_counts.get(problem.difficulty, 0) / total

        if actual_proportion == 0.0:
            # Difficulty absent from pool — score would be infinite; cap at 1.0.
            return 1.0

        ratio = target_proportion / actual_proportion
        return min(1.0, ratio)
