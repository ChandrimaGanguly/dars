# Security & Fairness Review: PHASE3-B-1 Problem Selection Algorithm

**Reviewer:** Noor (Security & Observability Expert)
**Date:** 2026-03-04
**Scope:** `src/services/problem_selector.py` (algorithm spec in PHASE3_TASKS.md Track B)
**Status:** Design review (pre-implementation — reviewing the spec before code exists)

---

## 1. IDOR Risks in the Selector

**Finding: student_id scoping looks correct in spec, but must be verified in repo calls.**

- The `select_problems(db, student_id, grade)` signature accepts `student_id` as a
  positional argument. The spec shows it feeds directly into:
  - `problem_repo.get_recently_seen_problem_ids(db, student_id, days=7)`
  - `response_repo.get_topic_accuracy_for_student(db, student_id, ...)`
  - `response_repo.get_all_topic_accuracies(db, student_id, ...)`

- **Risk (LOW):** If these repo methods do NOT scope their SQL WHERE clauses to the
  provided `student_id`, a student could poison another student's recency/mastery data
  by some indirect means. However, since repo methods receive `student_id` explicitly,
  standard ORM query patterns (`.where(Response.student_id == student_id)`) will be safe.
  The risk is entirely in Maryam's repository implementation — not in the selector itself.

- **Recommendation for Maryam:** Every repo query in A-2 that takes `student_id` must
  include it in the WHERE clause, not just in the JOIN condition.

**Finding: No cross-student contamination path in the scoring algorithm itself.**

- `_score_problem()` receives `recent_topics`, `topic_accuracies` — both are dicts
  pre-fetched for the authenticated student. The scoring loop never touches another
  student's data. IDOR risk in the algorithm logic = **NONE**.

---

## 2. History Manipulation to Get Only Easy Problems

**Finding: Moderate manipulation risk — requires deliberate gaming behavior.**

A student who intentionally answers all hard problems wrong (or skips sessions) could
push their mastery score for hard topics below 40%, which causes `mastery_score = 1.0`
(struggling = high priority). Combined with `difficulty_variation_score`, positions 0-1
in the selection will still prefer `difficulty=1` (easy), so:

- Slot 1 (position 0): easy=1.0, medium=0.3, hard=0.1 — already biased to easy.
- Gaming mastery downward does NOT let a student escape hard problems entirely: position 4
  (slot 5) always prefers `difficulty=3` (easy=0.1, medium=0.5, hard=1.0).

**Conclusion:** The 3-slot difficulty distribution (positions 0-1 easy, 2-3 medium, 4 hard)
provides a structural floor. A student cannot game the algorithm to receive only easy
problems — slot 5 will always skew toward a hard problem regardless of mastery score.

**Recommendation:** Document this design intent explicitly in `ProblemSelector.__doc__`.
No code change needed for Phase 3.

---

## 3. Timing Attacks on Determinism

**Finding: Low risk — pure Python scoring, no secret values involved.**

The spec calls for `ties broken by problem_id ASC`. The determinism implementation
is a sorted comparison of floating-point scores + integer IDs — both are non-secret
values visible in the database.

- There is no timing variation that reveals secret data (no password/token comparison).
- The composite score formula uses only public data (grade, topic, difficulty, student
  history). A student who can read the DB has more information than any timing attack
  would reveal.
- `<500ms` performance requirement is a correctness/availability concern, not a security
  concern in this context.

**Conclusion:** No timing attack surface exists. The determinism requirement is purely
for test reproducibility.

---

## 4. student_id Scoping in Repository Queries

**Finding: Scoping must be verified in each repo method when Maryam implements A-2.**

Methods that must scope to student_id (from PHASE3_TASKS.md A-2 spec):

| Method | student_id must appear in WHERE? |
|---|---|
| `get_recently_seen_problem_ids(db, student_id, days=7)` | YES — join sessions + responses, filter `sessions.student_id = student_id` |
| `get_topic_accuracy_for_student(db, student_id, topic, days=30)` | YES — WHERE responses join sessions WHERE student_id |
| `get_all_topic_accuracies(db, student_id, days=30)` | YES — same as above, grouped by topic |

The `ProblemSelector` itself never reads response/session data directly — it delegates
entirely to repositories. As long as repos scope correctly, the selector is safe.

**Recommended integration test for CP3:** After A-2 is delivered, add an integration
test: create two students, add response history for student A only, call
`select_problems(student_id=B)` — verify student A's history does NOT affect
student B's selection.

---

## 5. Fairness Concerns

**Finding: Two fairness concerns with the current spec — neither a blocker for Phase 3.**

### 5a. New Students Always Get the Same First Session

The edge case spec says: "All topics recency=1.0, mastery=0.8; select 5 easiest from
diverse topics." With a fixed set of 280 problems, all new students in the same grade
will receive identical first sessions (determinism guarantee). This is a known product
constraint, not a bug.

- **Pilot impact:** For 50 students, some will discuss sessions and share answers.
  The identical first session design choice must be documented as a known trade-off.
- **Mitigation (post-pilot):** Add a randomized tie-breaking option controlled by a
  feature flag. Not needed for Phase 3.

### 5b. Students with Sparse History Disadvantaged on Mastery Score

New students and students who rarely complete sessions receive `mastery_score = 0.8`
for all topics (never attempted). This is higher than proficient students (0.2) but
lower than struggling students (1.0). The spec handles this correctly.

- **Concern:** A student who completes 1 response and gets it wrong (0% accuracy) gets
  `mastery_score = 1.0` (struggling), placing them in the highest-priority bucket
  immediately. A student with zero history gets 0.8. One wrong answer causes a jump in
  priority — this is correct pedagogically but means the algorithm is sensitive to first
  impressions.
- **Recommendation:** Document that mastery score requires at least 3 data points to be
  stable. No code change needed for Phase 3.

---

## 6. Summary Table

| Risk | Severity | Status |
|---|---|---|
| IDOR: selector using another student's history | LOW | Mitigated by student_id param passing |
| History manipulation → easy-only problems | LOW | Prevented by difficulty distribution structure |
| Timing attack on determinism | NONE | No secret values in comparison path |
| student_id missing in repo WHERE clauses | MEDIUM (dep on Maryam) | Needs verification at CP3 |
| Identical first sessions for new students | LOW (fairness) | Known trade-off, document it |
| Single-response mastery instability | LOW (fairness) | Document min 3 responses for reliability |

---

## 7. Handoff to Jodha

These items should be addressed **when implementing PHASE3-B-1**:

1. Add docstring to `ProblemSelector` noting that identical first sessions are expected.
2. Add docstring to `_score_problem()` noting the 3-data-point stability minimum.
3. When calling repos, pass `student_id` as a named argument to make scoping explicit.

These items should be verified **at CP3** (Maryam's repositories delivered):

1. Write integration test confirming student A history does not affect student B selection.
2. Review each repo method for correct WHERE clause scoping.
