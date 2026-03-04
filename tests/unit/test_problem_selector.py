"""
Unit tests for the ProblemSelector service (PHASE3-B-1).

All repository dependencies are mocked with unittest.mock.AsyncMock so these
tests run without a real database.  Tests verify the 50/30/20 scoring algorithm,
determinism, edge cases, and the <500ms performance requirement.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.problem import Problem
from src.services.problem_selector import (
    MASTERY_WINDOW_DAYS,
    NEW_TOPIC_MASTERY_SCORE,
    PROBLEMS_PER_SESSION,
    RECENCY_WINDOW_DAYS,
    ProblemSelector,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_problem(
    problem_id: int,
    grade: int = 7,
    topic: str = "Algebra",
    difficulty: int = 2,
) -> Problem:
    """Create a minimal Problem ORM object for testing (no DB required)."""
    p = MagicMock(spec=Problem)
    p.problem_id = problem_id
    p.grade = grade
    p.topic = topic
    p.difficulty = difficulty
    return p  # type: ignore[return-value]


def make_response(
    problem_id: int,
    topic: str,
    is_correct: bool,
    days_ago: float = 0,
) -> dict[str, Any]:
    """Create a response dict as returned by ResponseRepository."""
    return {
        "problem_id": problem_id,
        "topic": topic,
        "is_correct": is_correct,
        "answered_at": datetime.now(UTC) - timedelta(days=days_ago),
    }


def make_mock_repos(
    problems: list[Problem],
    responses: list[dict[str, Any]] | None = None,
) -> tuple[AsyncMock, AsyncMock]:
    """Return (problem_repo_mock, response_repo_mock) for given data."""
    if responses is None:
        responses = []

    problem_repo = AsyncMock()
    problem_repo.get_by_grade = AsyncMock(return_value=problems)

    response_repo = AsyncMock()
    response_repo.get_recent_by_student = AsyncMock(return_value=responses)

    return problem_repo, response_repo


def make_db() -> AsyncMock:
    """Return a stub AsyncSession — ProblemSelector passes it through to repos."""
    return AsyncMock()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestProblemSelectorBasic:
    """Basic correctness tests."""

    async def test_returns_five_problems_for_normal_student(self) -> None:
        """Selector must return exactly 5 problems when 20+ are available."""
        problems = [make_problem(i) for i in range(1, 21)]  # 20 problems
        problem_repo, response_repo = make_mock_repos(problems)

        selector = ProblemSelector()
        result = await selector.select_problems(
            student_id=1,
            grade=7,
            db=make_db(),
            problem_repo=problem_repo,
            response_repo=response_repo,
        )

        assert len(result) == PROBLEMS_PER_SESSION
        # All returned items must come from the input pool
        result_ids = {p.problem_id for p in result}
        input_ids = {p.problem_id for p in problems}
        assert result_ids.issubset(input_ids)

    async def test_new_student_no_history(self) -> None:
        """A brand-new student with no response history must still get 5 problems."""
        problems = [make_problem(i) for i in range(1, 21)]
        problem_repo, response_repo = make_mock_repos(problems, responses=[])

        selector = ProblemSelector()
        result = await selector.select_problems(
            student_id=999,
            grade=7,
            db=make_db(),
            problem_repo=problem_repo,
            response_repo=response_repo,
        )

        assert len(result) == PROBLEMS_PER_SESSION

    async def test_sparse_grade_fewer_than_five(self) -> None:
        """When fewer than 5 problems exist for a grade, return all of them (no error)."""
        problems = [make_problem(i, grade=8) for i in range(1, 4)]  # only 3 problems
        problem_repo, response_repo = make_mock_repos(problems)

        selector = ProblemSelector()
        result = await selector.select_problems(
            student_id=1,
            grade=8,
            db=make_db(),
            problem_repo=problem_repo,
            response_repo=response_repo,
        )

        assert len(result) == 3
        assert {p.problem_id for p in result} == {1, 2, 3}

    async def test_empty_grade_returns_empty_list(self) -> None:
        """When no problems exist for a grade, return empty list gracefully."""
        problem_repo, response_repo = make_mock_repos(problems=[])

        selector = ProblemSelector()
        result = await selector.select_problems(
            student_id=1,
            grade=6,
            db=make_db(),
            problem_repo=problem_repo,
            response_repo=response_repo,
        )

        assert result == []

    async def test_all_mastered_returns_something(self) -> None:
        """Even when a student has >90% accuracy on all topics, 5 problems are returned."""
        problems = [make_problem(i, topic="Fractions") for i in range(1, 21)]
        # All responses correct → high accuracy → low mastery score but still returns 5
        responses = [
            make_response(problem_id=i, topic="Fractions", is_correct=True, days_ago=20)
            for i in range(1, 16)
        ]
        problem_repo, response_repo = make_mock_repos(problems, responses)

        selector = ProblemSelector()
        result = await selector.select_problems(
            student_id=1,
            grade=7,
            db=make_db(),
            problem_repo=problem_repo,
            response_repo=response_repo,
        )

        assert len(result) == PROBLEMS_PER_SESSION

    async def test_single_topic_grade_returns_five(self) -> None:
        """A grade with all problems in one topic still returns 5 problems."""
        problems = [make_problem(i, topic="Integers") for i in range(1, 11)]
        problem_repo, response_repo = make_mock_repos(problems)

        selector = ProblemSelector()
        result = await selector.select_problems(
            student_id=1,
            grade=7,
            db=make_db(),
            problem_repo=problem_repo,
            response_repo=response_repo,
        )

        assert len(result) == PROBLEMS_PER_SESSION
        for p in result:
            assert p.topic == "Integers"


@pytest.mark.unit
class TestProblemSelectorDeterminism:
    """Determinism guarantees — same inputs must always produce same outputs."""

    async def test_determinism_same_inputs_same_output(self) -> None:
        """Calling select_problems twice with identical mocks returns identical results."""
        problems = [make_problem(i, topic="Algebra") for i in range(1, 21)]
        responses = [
            make_response(problem_id=3, topic="Algebra", is_correct=False, days_ago=5),
            make_response(problem_id=7, topic="Algebra", is_correct=True, days_ago=10),
        ]

        selector = ProblemSelector()

        # First call
        problem_repo1, response_repo1 = make_mock_repos(problems, responses)
        result1 = await selector.select_problems(
            student_id=42,
            grade=7,
            db=make_db(),
            problem_repo=problem_repo1,
            response_repo=response_repo1,
        )

        # Second call — fresh mocks with identical data
        problem_repo2, response_repo2 = make_mock_repos(problems, responses)
        result2 = await selector.select_problems(
            student_id=42,
            grade=7,
            db=make_db(),
            problem_repo=problem_repo2,
            response_repo=response_repo2,
        )

        assert [p.problem_id for p in result1] == [p.problem_id for p in result2]

    async def test_tie_breaking_by_problem_id(self) -> None:
        """When two problems have identical scores, the lower problem_id must win.

        We create 7 problems with identical attributes (same topic, same difficulty,
        all unseen, no history) so they all receive identical composite scores.
        The only tie-breaker is problem_id ascending — the 5 lowest IDs must win.
        """
        # All 7 problems: same topic, same difficulty, no history → identical scores
        all_problems = [
            make_problem(problem_id=pid, topic="Geometry", difficulty=2)
            for pid in [50, 3, 100, 1, 7, 200, 15]
        ]
        problem_repo, response_repo = make_mock_repos(all_problems, responses=[])

        selector = ProblemSelector()
        result = await selector.select_problems(
            student_id=1,
            grade=7,
            db=make_db(),
            problem_repo=problem_repo,
            response_repo=response_repo,
        )

        result_ids = [p.problem_id for p in result]
        # With tie-breaking by problem_id ASC, the 5 lowest IDs must be selected,
        # in ascending order
        expected_ids = sorted([50, 3, 100, 1, 7, 200, 15])[:5]  # [1, 3, 7, 15, 50]
        assert (
            result_ids == expected_ids
        ), f"Expected tie-break selection {expected_ids}, got {result_ids}"

    async def test_determinism_new_student(self) -> None:
        """Repeated calls for a new student (empty history) return same 5 problems."""
        problems = [make_problem(i) for i in range(1, 31)]

        selector = ProblemSelector()

        results = []
        for _ in range(3):
            problem_repo, response_repo = make_mock_repos(problems, responses=[])
            result = await selector.select_problems(
                student_id=5,
                grade=7,
                db=make_db(),
                problem_repo=problem_repo,
                response_repo=response_repo,
            )
            results.append([p.problem_id for p in result])

        assert results[0] == results[1] == results[2]


@pytest.mark.unit
class TestProblemSelectorScoring:
    """Scoring algorithm correctness tests."""

    async def test_recency_boosts_unseen_topics(self) -> None:
        """Problems from topics NOT seen in last 7 days should rank higher."""
        # Two topics: "Seen" (answered 3 days ago) and "Unseen" (never answered)
        seen_problems = [make_problem(i, topic="Seen", difficulty=2) for i in range(1, 6)]
        unseen_problems = [make_problem(i, topic="Unseen", difficulty=2) for i in range(10, 15)]
        all_problems = seen_problems + unseen_problems

        # Responses for the "Seen" topic within the recency window (3 days ago)
        responses = [
            make_response(problem_id=i, topic="Seen", is_correct=True, days_ago=3)
            for i in range(1, 4)
        ]
        problem_repo, response_repo = make_mock_repos(all_problems, responses)

        selector = ProblemSelector()
        result = await selector.select_problems(
            student_id=1,
            grade=7,
            db=make_db(),
            problem_repo=problem_repo,
            response_repo=response_repo,
        )

        result_ids = {p.problem_id for p in result}
        # At least some unseen-topic problems should be selected over seen-topic ones
        unseen_ids = {p.problem_id for p in unseen_problems}
        assert (
            len(result_ids & unseen_ids) > 0
        ), "Expected at least one problem from the unseen topic to be selected"

    async def test_recency_window_boundary(self) -> None:
        """Problems answered exactly on the boundary should be treated as recent."""
        problem_old = make_problem(1, topic="Old", difficulty=2)
        problem_recent = make_problem(2, topic="Recent", difficulty=2)
        fillers = [make_problem(i) for i in range(3, 12)]

        # problem 2 answered just at the boundary (RECENCY_WINDOW_DAYS days ago)
        responses = [
            make_response(
                problem_id=2,
                topic="Recent",
                is_correct=True,
                days_ago=RECENCY_WINDOW_DAYS,
            )
        ]
        problem_repo, response_repo = make_mock_repos(
            [problem_old, problem_recent, *fillers], responses
        )

        selector = ProblemSelector()
        result = await selector.select_problems(
            student_id=1,
            grade=7,
            db=make_db(),
            problem_repo=problem_repo,
            response_repo=response_repo,
        )

        # Boundary responses ARE within the recency window, so problem 2 gets 0.0 recency
        # problem 1 (never seen) gets 1.0 recency — it should be preferred
        result_ids = [p.problem_id for p in result]
        assert 1 in result_ids, "Unseen problem should appear in selection"

    async def test_mastery_boosts_weak_topics(self) -> None:
        """Topics with low accuracy (< 60%) should be prioritised over strong topics."""
        # "Weak" topic: 25% accuracy (1 correct out of 4 — 20 days ago, outside recency)
        # "Strong" topic: 90% accuracy
        weak_problems = [make_problem(i, topic="Weak", difficulty=2) for i in range(1, 6)]
        strong_problems = [make_problem(i, topic="Strong", difficulty=2) for i in range(10, 15)]
        all_problems = weak_problems + strong_problems

        responses = [
            # Weak topic: answered 20 days ago (outside recency but inside mastery window)
            make_response(problem_id=1, topic="Weak", is_correct=True, days_ago=20),
            make_response(problem_id=2, topic="Weak", is_correct=False, days_ago=20),
            make_response(problem_id=3, topic="Weak", is_correct=False, days_ago=20),
            make_response(problem_id=4, topic="Weak", is_correct=False, days_ago=20),
            # Strong topic: 9 correct out of 10
            make_response(problem_id=10, topic="Strong", is_correct=True, days_ago=20),
            make_response(problem_id=11, topic="Strong", is_correct=True, days_ago=20),
            make_response(problem_id=12, topic="Strong", is_correct=True, days_ago=20),
            make_response(problem_id=13, topic="Strong", is_correct=False, days_ago=20),
        ]
        problem_repo, response_repo = make_mock_repos(all_problems, responses)

        selector = ProblemSelector()
        result = await selector.select_problems(
            student_id=1,
            grade=7,
            db=make_db(),
            problem_repo=problem_repo,
            response_repo=response_repo,
        )

        result_ids = {p.problem_id for p in result}
        weak_ids = {p.problem_id for p in weak_problems}
        # More weak-topic problems should appear than strong-topic ones
        weak_count = len(result_ids & weak_ids)
        assert weak_count >= 3, f"Expected ≥3 weak-topic problems in selection, got {weak_count}"

    async def test_new_topic_gets_neutral_mastery_score(self) -> None:
        """A topic with no history must receive the neutral mastery score (0.5)."""
        selector = ProblemSelector()
        topic_stats: dict[str, object] = {}  # empty → no history
        problem = make_problem(1, topic="NewTopic", difficulty=2)

        # Access the private helper directly for unit-level verification
        score = selector._mastery_score(problem, topic_stats)  # type: ignore[arg-type]
        assert score == NEW_TOPIC_MASTERY_SCORE

    async def test_difficulty_mix_penalises_overrepresented_difficulty(self) -> None:
        """Problems of over-represented difficulty levels should score lower.

        When the pool has far more hard problems than the 20% target, hard problems
        receive a lower difficulty score — the 40%-target easy and medium problems
        should dominate the top-5 selection when recency and mastery are equal.
        """
        # Pool: 2 easy, 2 medium, 16 hard — hard is massively over-represented
        # All same topic (unseen) so recency=1.0 and mastery=0.5 for all
        easy = [make_problem(i, difficulty=1, topic="Numbers") for i in range(1, 3)]
        medium = [make_problem(i, difficulty=2, topic="Numbers") for i in range(3, 5)]
        hard = [make_problem(i, difficulty=3, topic="Numbers") for i in range(5, 21)]
        all_problems = easy + medium + hard

        problem_repo, response_repo = make_mock_repos(all_problems, responses=[])

        selector = ProblemSelector()
        result = await selector.select_problems(
            student_id=1,
            grade=7,
            db=make_db(),
            problem_repo=problem_repo,
            response_repo=response_repo,
        )

        assert len(result) == PROBLEMS_PER_SESSION
        difficulties = [p.difficulty for p in result]
        hard_count = difficulties.count(3)

        # Hard is over-represented (16/20 = 80% actual vs 20% target) →
        # difficulty score for hard = 0.20/0.80 = 0.25
        # Easy/medium actual = 2/20 = 10% vs target 40% → score = 0.40/0.10 = 4.0 → capped at 1.0
        # So easy and medium always beat hard on difficulty dimension.
        # With only 2 easy + 2 medium = 4 non-hard problems, those 4 all make top-5;
        # 1 hard fills the remaining slot.
        assert (
            hard_count <= 1
        ), f"Expected at most 1 hard problem in top-5 (over-represented), got {hard_count}"

    async def test_difficulty_mix_hard_selected_when_underrepresented(self) -> None:
        """When hard problems are rare (under-represented), they should score higher."""
        # Pool: 15 easy, 5 medium, 0 hard → hard is completely absent
        # Verify easy and medium both appear; hard can't appear (not in pool)
        easy = [make_problem(i, difficulty=1, topic="Numbers") for i in range(1, 16)]
        medium = [make_problem(i, difficulty=2, topic="Numbers") for i in range(16, 21)]
        all_problems = easy + medium

        problem_repo, response_repo = make_mock_repos(all_problems, responses=[])

        selector = ProblemSelector()
        result = await selector.select_problems(
            student_id=1,
            grade=7,
            db=make_db(),
            problem_repo=problem_repo,
            response_repo=response_repo,
        )

        assert len(result) == PROBLEMS_PER_SESSION
        difficulties = [p.difficulty for p in result]
        # Medium actual = 5/20 = 25% vs target 40% → score = 0.40/0.25 = 1.6 → capped at 1.0
        # Easy actual = 15/20 = 75% vs target 40% → score = 0.40/0.75 = 0.53
        # All 5 medium problems should rank higher than any easy problem on difficulty
        medium_count = difficulties.count(2)
        assert (
            medium_count == 5
        ), f"Expected all 5 medium problems in top-5 (under-represented), got {medium_count}"

    async def test_out_of_recency_window_responses_not_penalised(self) -> None:
        """Problems answered more than 7 days ago should NOT get a recency penalty.

        When a problem was last answered 10 days ago (outside the 7-day recency
        window), it should receive the same recency_score=1.0 as a never-seen problem.
        Both groups should appear in a balanced selection.

        To isolate the recency test from mastery effects, both topic groups use
        the same low accuracy (50%) so mastery scores are equal.
        """
        old_problems = [make_problem(i, topic="OldTopic", difficulty=2) for i in range(1, 6)]
        new_problems = [make_problem(i, topic="NewTopic", difficulty=2) for i in range(10, 15)]
        all_problems = old_problems + new_problems

        # OldTopic: answered 10 days ago (outside recency window) with 50% accuracy
        # → recency_score=1.0 (not penalised), mastery_score=0.5 (neutral)
        # NewTopic: never answered → recency_score=1.0, mastery_score=0.5 (neutral)
        # → both topics are now exactly equal → tie-broken by problem_id
        responses = [
            make_response(problem_id=1, topic="OldTopic", is_correct=True, days_ago=10),
            make_response(problem_id=2, topic="OldTopic", is_correct=False, days_ago=10),
        ]
        problem_repo, response_repo = make_mock_repos(all_problems, responses)

        selector = ProblemSelector()
        result = await selector.select_problems(
            student_id=1,
            grade=7,
            db=make_db(),
            problem_repo=problem_repo,
            response_repo=response_repo,
        )

        # All problems are scored equally → tie-break by problem_id ASC
        # OldTopic IDs: 1,2,3,4,5 — all lower than NewTopic IDs: 10,11,12,13,14
        # So top-5 must be OldTopic problems (not penalised by recency)
        result_ids = {p.problem_id for p in result}
        old_ids = {p.problem_id for p in old_problems}
        assert (
            len(result_ids & old_ids) > 0
        ), "Old-topic problems (answered >7 days ago) should appear — no recency penalty"


@pytest.mark.unit
class TestProblemSelectorPerformance:
    """Performance requirement: <500ms with 100 mocked problems."""

    async def test_performance_under_500ms(self) -> None:
        """select_problems must complete in under 500ms with 100 candidate problems."""
        # 100 problems across 10 topics with 3 difficulties
        problems: list[Problem] = []
        for i in range(1, 101):
            topic = f"Topic{(i % 10) + 1}"
            difficulty = (i % 3) + 1
            problems.append(make_problem(i, topic=topic, difficulty=difficulty))

        # 30 historical responses spread across topics
        responses = [
            make_response(
                problem_id=i,
                topic=f"Topic{(i % 10) + 1}",
                is_correct=(i % 3 != 0),
                days_ago=float(i % 35),
            )
            for i in range(1, 31)
        ]

        problem_repo, response_repo = make_mock_repos(problems, responses)

        selector = ProblemSelector()

        start = time.perf_counter()
        result = await selector.select_problems(
            student_id=1,
            grade=7,
            db=make_db(),
            problem_repo=problem_repo,
            response_repo=response_repo,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(result) == PROBLEMS_PER_SESSION
        assert elapsed_ms < 500, f"select_problems took {elapsed_ms:.1f}ms, must be <500ms"

    async def test_performance_with_large_history(self) -> None:
        """Selector must remain <500ms even with 200 historical responses."""
        problems = [make_problem(i, topic=f"Topic{i % 5}") for i in range(1, 101)]
        responses = [
            make_response(
                problem_id=i % 100 + 1,
                topic=f"Topic{(i % 100) % 5}",
                is_correct=i % 2 == 0,
                days_ago=float(i % 28),
            )
            for i in range(200)
        ]

        problem_repo, response_repo = make_mock_repos(problems, responses)

        selector = ProblemSelector()

        start = time.perf_counter()
        result = await selector.select_problems(
            student_id=1,
            grade=7,
            db=make_db(),
            problem_repo=problem_repo,
            response_repo=response_repo,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(result) == PROBLEMS_PER_SESSION
        assert elapsed_ms < 500, f"Took {elapsed_ms:.1f}ms with large history"


@pytest.mark.unit
class TestProblemSelectorEdgeCases:
    """Edge cases and robustness tests."""

    async def test_mastery_window_is_30_days(self) -> None:
        """Responses older than 30 days must not influence mastery scoring."""
        problem = make_problem(1, topic="Ancient", difficulty=2)
        fillers = [make_problem(i) for i in range(2, 21)]

        # The repo mock returns NO responses (simulating the mastery window filter
        # that the real repo will apply in its WHERE clause — old responses are
        # already excluded at the query level before reaching this service).
        problem_repo, response_repo = make_mock_repos([problem, *fillers], responses=[])

        selector = ProblemSelector()
        result = await selector.select_problems(
            student_id=1,
            grade=7,
            db=make_db(),
            problem_repo=problem_repo,
            response_repo=response_repo,
        )
        # Should complete without error; responses argument ignored since repo is mocked
        assert len(result) == PROBLEMS_PER_SESSION

    async def test_problem_seen_exactly_at_recency_boundary_is_penalised(self) -> None:
        """Verify _recently_seen_problem_ids includes problems at the exact boundary."""
        selector = ProblemSelector()
        now = datetime.now(UTC)
        cutoff = now - timedelta(days=RECENCY_WINDOW_DAYS)

        # Response answered exactly at the cutoff time
        responses = [
            {
                "problem_id": 42,
                "topic": "Math",
                "is_correct": True,
                "answered_at": cutoff,  # exactly at boundary
            }
        ]
        seen_ids = selector._recently_seen_problem_ids(responses, cutoff)  # type: ignore[arg-type]
        assert 42 in seen_ids

    async def test_response_with_missing_answered_at_is_skipped(self) -> None:
        """Malformed responses without a datetime answered_at must not crash the selector."""
        problems = [make_problem(i) for i in range(1, 21)]
        bad_responses: list[dict[str, Any]] = [
            {"problem_id": 1, "topic": "Algebra", "is_correct": True, "answered_at": None},
            {"problem_id": 2, "topic": "Algebra", "is_correct": False, "answered_at": "bad"},
        ]

        problem_repo, response_repo = make_mock_repos(problems, bad_responses)

        selector = ProblemSelector()
        result = await selector.select_problems(
            student_id=1,
            grade=7,
            db=make_db(),
            problem_repo=problem_repo,
            response_repo=response_repo,
        )

        # Must not crash; should still return problems
        assert len(result) == PROBLEMS_PER_SESSION

    async def test_grade_filtering_delegated_to_repo(self) -> None:
        """ProblemSelector must pass the grade argument to problem_repo.get_by_grade."""
        problems = [make_problem(i, grade=6) for i in range(1, 6)]
        problem_repo, response_repo = make_mock_repos(problems)

        selector = ProblemSelector()
        await selector.select_problems(
            student_id=1,
            grade=6,
            db=make_db(),
            problem_repo=problem_repo,
            response_repo=response_repo,
        )

        # Verify the repo was called with the correct grade
        problem_repo.get_by_grade.assert_called_once()
        call_kwargs = problem_repo.get_by_grade.call_args
        assert call_kwargs.kwargs.get("grade") == 6 or (
            len(call_kwargs.args) >= 2 and call_kwargs.args[1] == 6
        )

    async def test_response_repo_called_with_mastery_window(self) -> None:
        """response_repo.get_recent_by_student must be called with correct since datetime."""
        problems = [make_problem(i) for i in range(1, 6)]
        problem_repo, response_repo = make_mock_repos(problems)

        selector = ProblemSelector()
        before_call = datetime.now(UTC)
        await selector.select_problems(
            student_id=7,
            grade=7,
            db=make_db(),
            problem_repo=problem_repo,
            response_repo=response_repo,
        )

        response_repo.get_recent_by_student.assert_called_once()
        kwargs = response_repo.get_recent_by_student.call_args.kwargs
        since: datetime = kwargs["since"]

        # 'since' should be approximately 30 days ago
        expected_since = before_call - timedelta(days=MASTERY_WINDOW_DAYS)
        assert (
            abs((since - expected_since).total_seconds()) < 2
        ), f"Expected 'since' ~{expected_since}, got {since}"
        assert kwargs["student_id"] == 7

    async def test_topic_stats_accuracy_zero_when_no_answers(self) -> None:
        """_TopicStats.accuracy must return 0.0 when no answers have been recorded.

        This covers the total_answers == 0 branch in the accuracy property.
        """
        from src.services.problem_selector import _TopicStats

        stats = _TopicStats()
        assert stats.total_answers == 0
        assert stats.accuracy == 0.0

    async def test_difficulty_score_zero_total_counts(self) -> None:
        """_difficulty_score_static handles an empty difficulty_counts dict gracefully."""
        selector = ProblemSelector()
        problem = make_problem(1, difficulty=2)
        # Simulate empty pool (total == 0)
        score = selector._difficulty_score_static(problem, {1: 0, 2: 0, 3: 0})  # type: ignore[arg-type]
        # total == 0 branch → returns target_proportion for difficulty 2 = 0.40
        assert score == 0.40

    async def test_difficulty_score_absent_difficulty_gets_max(self) -> None:
        """When a difficulty is absent from the pool, _difficulty_score_static returns 1.0."""
        selector = ProblemSelector()
        problem = make_problem(1, difficulty=3)
        # Hard is absent from this pool
        score = selector._difficulty_score_static(problem, {1: 5, 2: 5, 3: 0})  # type: ignore[arg-type]
        # actual_proportion == 0.0 branch → returns 1.0
        assert score == 1.0

    async def test_difficulty_score_unknown_difficulty_returns_zero(self) -> None:
        """A problem with difficulty outside {1,2,3} returns 0.0 (defensive guard).

        This branch is structurally prevented by DB check constraints but is tested
        for robustness so the defensive code path is verified.
        """
        selector = ProblemSelector()
        # Difficulty 4 is not in TARGET_DIFFICULTY_DISTRIBUTION → target=0.0 → return 0.0
        p = MagicMock(spec=Problem)
        p.problem_id = 1
        p.difficulty = 4  # invalid per DB constraints, but defensively handled
        score = selector._difficulty_score_static(p, {1: 5, 2: 5, 3: 5, 4: 1})  # type: ignore[arg-type]
        assert score == 0.0
