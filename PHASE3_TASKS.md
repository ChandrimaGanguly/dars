# Phase 3 Tasks: Core Learning Engine

**Duration:** Week 2-3 (8 days of agent work)
**Complexity:** M+M+M across three parallel tracks = ~8 days total
**Status:** ✅ COMPLETE — All tracks A, B, C done. 180 tests passing.

**Demo Target:** "Student sends `/practice`, receives 5 real problems from the database, submits answers, sees per-problem feedback in Bengali, and the session state is saved so they can resume after disconnect."

**Algorithm Weights Decision (REQ-008):**
> ✅ **CONFIRMED for MVP:** 50% topic recency / 30% mastery / 20% difficulty variation.
> These weights are used as-is for the pilot. Education expert review deferred to Week 3 pilot feedback.

**Pre-conditions (verify before starting):**
- [x] PHASE1-A-1 complete — all models migrated, DB running
- [x] PHASE1-B-1 complete — FastAPI routes exist, DB session dependency working
- [x] PHASE1-C-1 complete — SEC-003 verify_student active on all practice endpoints
- [x] PHASE2 complete — 280 problems in YAML files (grade_6: 77, grade_7: 141, grade_8: 42+)
- [ ] **GAP:** No database seeding script (PHASE3-A-1 closes this)
- [ ] **GAP:** `answer_type` column missing from Problem model (PHASE3-A-1 closes this)
- 🔄 **Grade 8 content expansion running in parallel** (Jahanara adding Mensuration, Geometry, Data Handling, Rational Numbers)

---

## Task Summary

| Task ID | Task Name | Owner | Duration | Blocked By | Blocks | Status |
|---------|-----------|-------|----------|-----------|--------|--------|
| PHASE3-A-1 | answer_type migration + seed script | Maryam | 2 days | None | PHASE3-A-2, PHASE3-B-2 | ✅ Complete |
| PHASE3-A-2 | Session, Response & Problem repositories | Maryam | 1.5 days | PHASE3-A-1 | PHASE3-B-2, PHASE3-B-3 | ✅ Complete |
| PHASE3-B-1 | Problem selection algorithm (REQ-008) | Jodha | 2.5 days | None (parallel with A-1) | PHASE3-B-3 | ✅ Complete |
| PHASE3-B-2 | Answer evaluation service (REQ-003) | Jodha | 1.5 days | PHASE3-A-1, PHASE3-A-2 | PHASE3-B-3 | ✅ Complete |
| PHASE3-B-3 | Wire practice.py endpoints end-to-end | Jodha | 2 days | PHASE3-B-1, PHASE3-B-2, PHASE3-A-2 | PHASE3-B-4, PHASE3-C-1,2,3 | ✅ Complete |
| PHASE3-B-4 | Telegram /practice command wiring | Jodha | 1 day | PHASE3-B-3 | Phase 4 | ✅ Complete |
| PHASE3-C-1 | Session ownership + IDOR prevention | Noor | 1.5 days | PHASE3-B-3 | Phase 4 | ✅ Complete |
| PHASE3-C-2 | Structured practice event logging | Noor | 1 day | PHASE3-B-3 | Phase 4 | ✅ Complete |
| PHASE3-C-3 | Cost tracking stubs for future Claude calls | Noor | 1 day | PHASE3-B-3 | Phase 4 | ✅ Complete |

**Dependency chain (critical path):**
```
PHASE3-A-1 ──► PHASE3-A-2 ──► PHASE3-B-2 ──► PHASE3-B-3 ──► PHASE3-B-4 ──► Phase 4
                                                          └──► PHASE3-C-1
                                                          └──► PHASE3-C-2
                                                          └──► PHASE3-C-3
PHASE3-B-1 ─────────────────────────────────► PHASE3-B-3
```

**Can run in parallel from Day 1:** A-1 (Maryam) and B-1 (Jodha) have no shared dependencies.
Noor (Track C) does design review and writes test scaffolding while waiting for B-3.

---

## Track A: Database Work (Maryam)

### PHASE3-A-1: answer_type Migration + Seed Script

**Task ID:** PHASE3-A-1
**Owner:** Maryam (Database & ORM Expert)
**Duration:** ~2 days
**Blocker:** None — starts Day 1
**Blocks:** PHASE3-A-2, PHASE3-B-2

#### Deliverables

- [ ] **PHASE3-A-1.1** — Alembic migration: add `answer_type`, `acceptable_tolerance_percent`, `multiple_choice_options` to `problems` table
- [ ] **PHASE3-A-1.2** — Update `src/models/problem.py` with the three new mapped_columns
- [ ] **PHASE3-A-1.3** — YAML loader utility `scripts/seed_problems.py`
- [ ] **PHASE3-A-1.4** — Seed ingests all YAML from `content/problems/` and transforms to DB format
- [ ] **PHASE3-A-1.5** — Idempotent seed: re-running does not duplicate problems
- [ ] **PHASE3-A-1.6** — Unit tests for YAML loader (≥80% coverage)
- [ ] **PHASE3-A-1.7** — Verify: `SELECT COUNT(*) FROM problems` returns 280

#### Detailed Work

##### 1. Alembic Migration [PHASE3-A-1.1]

**File to create:** `alembic/versions/XXXX_add_answer_type_to_problems.py`

Add three columns to `problems` table:

```python
op.add_column("problems", sa.Column(
    "answer_type",
    sa.String(20),
    nullable=False,
    server_default="numeric",
    comment="Answer type: numeric, multiple_choice, or text",
))
op.add_column("problems", sa.Column(
    "acceptable_tolerance_percent",
    sa.Float,
    nullable=True,
    server_default="5.0",
    comment="Tolerance % for numeric answers (default 5%)",
))
op.add_column("problems", sa.Column(
    "multiple_choice_options",
    sa.JSON,
    nullable=True,
    comment="Options for MC problems (JSON array of strings)",
))
op.create_check_constraint(
    "ck_problems_answer_type_valid",
    "problems",
    "answer_type IN ('numeric', 'multiple_choice', 'text')",
)
```

Verify round-trip: `alembic upgrade head` → `alembic downgrade -1` → `alembic upgrade head`

##### 2. Update Problem Model [PHASE3-A-1.2]

**File to modify:** `src/models/problem.py`

Add below the `difficulty` column:

```python
answer_type: Mapped[str] = mapped_column(
    String(20),
    nullable=False,
    server_default="numeric",
    comment="Answer type: numeric, multiple_choice, or text",
)

acceptable_tolerance_percent: Mapped[float | None] = mapped_column(
    Float,
    nullable=True,
    server_default="5.0",
    comment="Tolerance % for numeric answers (default 5%)",
)

multiple_choice_options: Mapped[list[dict[str, Any]] | None] = mapped_column(
    JSON,
    nullable=True,
    comment="Options for MC problems (JSON array)",
)
```

Add to `__table_args__`:
```python
CheckConstraint(
    "answer_type IN ('numeric', 'multiple_choice', 'text')",
    name="ck_problems_answer_type_valid",
),
```

##### 3. YAML Seed Script [PHASE3-A-1.3, PHASE3-A-1.4]

**File to create:** `scripts/seed_problems.py`

YAML → DB field mapping:

| YAML field | Problem column | Transform |
|---|---|---|
| `grade` | `grade` | int |
| `topic` | `topic` | str |
| `difficulty` | `difficulty` | int 1-3 |
| `question_en` | `question_en` | str |
| `question_bn` | `question_bn` | str |
| `answer` | `answer` | str |
| `answer_type` | `answer_type` | default "numeric" if absent |
| `hints[{en, bn}]` | `hints` (JSON) | convert to `{hint_number, text_en, text_bn, is_ai_generated}` (1-indexed) |

Hint transformation (YAML uses `{en, bn}` but DB uses `Hint.to_dict()` format):
```python
hints_db = [
    {
        "hint_number": i + 1,
        "text_en": h["en"],
        "text_bn": h["bn"],
        "is_ai_generated": False,
    }
    for i, h in enumerate(yaml_hints)
]
```

**Idempotency [PHASE3-A-1.5]:** Use `(grade, topic, question_en)` as uniqueness key.
Query before insert; skip if exists. Log counts: "Inserted 280, skipped 0".

CLI interface:
```bash
python scripts/seed_problems.py          # seed all
python scripts/seed_problems.py --dry-run   # preview counts, no insert
python scripts/seed_problems.py --grade 7   # seed grade 7 only
```

##### 4. Unit Tests [PHASE3-A-1.6]

**File to create:** `tests/unit/test_seed_problems.py`

- `test_yaml_load_counts()` — load grade_7/profit_and_loss.yaml, assert 20 problems
- `test_hint_conversion_hint_number()` — hint list becomes 1-indexed hint_number
- `test_answer_type_defaults_to_numeric()` — missing `answer_type` → "numeric"
- `test_idempotent_no_duplicates()` — second load run on same file → 0 inserts
- `test_missing_answer_field_raises()` — YAML without `answer` raises ValueError
- `test_bilingual_hints_preserved()` — `text_en` and `text_bn` both populated

#### Success Criteria

- [ ] `alembic upgrade head` succeeds, `alembic downgrade -1` succeeds
- [ ] `src/models/problem.py` has `answer_type`, `acceptable_tolerance_percent`, `multiple_choice_options`
- [ ] `python scripts/seed_problems.py` inserts 280 problems from YAML
- [ ] Re-running seed returns "Inserted 0, skipped 280" (idempotent)
- [ ] Unit tests ≥80% coverage on seed script
- [ ] `SELECT COUNT(*), grade FROM problems GROUP BY grade` shows expected distribution

---

### PHASE3-A-2: Session, Response & Problem Repositories

**Task ID:** PHASE3-A-2
**Owner:** Maryam (Database & ORM Expert)
**Duration:** ~1.5 days
**Blocked by:** PHASE3-A-1 (integration tests need seeded DB)
**Blocks:** PHASE3-B-2, PHASE3-B-3

#### Deliverables

- [ ] **PHASE3-A-2.1** — `src/repositories/problem_repository.py` — ProblemRepository
- [ ] **PHASE3-A-2.2** — `src/repositories/session_repository.py` — SessionRepository
- [ ] **PHASE3-A-2.3** — `src/repositories/response_repository.py` — ResponseRepository
- [ ] **PHASE3-A-2.4** — `src/repositories/__init__.py` exports all three
- [ ] **PHASE3-A-2.5** — Unit + integration tests ≥80% coverage
- [ ] **PHASE3-A-2.6** — Verify Jodha can import and call all methods

#### Detailed Work

##### 1. ProblemRepository [PHASE3-A-2.1]

**File to create:** `src/repositories/problem_repository.py`

Required async methods:

```python
class ProblemRepository:
    async def get_problems_by_grade(
        self, db, grade, difficulty=None, topic=None, exclude_ids=None
    ) -> list[Problem]: ...

    async def get_recently_seen_problem_ids(
        self, db, student_id, days=7
    ) -> list[int]:
        """Join sessions → responses, filter by date. Used by ProblemSelector."""

    async def get_problem_by_id(
        self, db, problem_id
    ) -> Problem | None: ...

    async def get_topics_for_grade(
        self, db, grade
    ) -> list[str]:
        """Distinct topic names. Used by selector for recency scoring."""

    async def get_problem_count_by_grade(
        self, db, grade
    ) -> int: ...
```

Query notes: all use indexed columns (`idx_problems_grade_topic`, `idx_problems_difficulty`).
`get_recently_seen_problem_ids` joins `sessions → responses`, filtered by `sessions.date`.

##### 2. SessionRepository [PHASE3-A-2.2]

**File to create:** `src/repositories/session_repository.py`

Required async methods:

```python
class SessionRepository:
    async def create_session(
        self, db, student_id, problem_ids
    ) -> Session:
        """Create in_progress session with expires_at = now + 30min.
        Calls db.flush() so session_id is available. REQ-007: persists before return."""

    async def get_active_session_for_today(
        self, db, student_id
    ) -> Session | None:
        """Return today's in_progress session, None if expired or not found."""

    async def get_session_by_id(
        self, db, session_id
    ) -> Session | None: ...

    async def mark_session_complete(
        self, db, session
    ) -> Session:
        """Set status=completed, completed_at=now()."""

    async def increment_correct_count(
        self, db, session
    ) -> Session: ...

    async def expire_stale_sessions(
        self, db
    ) -> int:
        """Mark ABANDONED any in_progress sessions past expires_at. Returns count."""

    async def get_completed_sessions_for_student(
        self, db, student_id, limit=10
    ) -> list[Session]: ...
```

**Important:** `create_session` must call `await db.flush()` (not commit) — the caller
(endpoint) holds the transaction and commits after returning problems to the student.

##### 3. ResponseRepository [PHASE3-A-2.3]

**File to create:** `src/repositories/response_repository.py`

Required async methods:

```python
class ResponseRepository:
    async def create_response(
        self, db, session_id, problem_id, student_answer,
        is_correct, hints_used, time_spent_seconds, confidence_level
    ) -> Response:
        """Persist immediately. Must flush so response survives disconnect (REQ-007)."""

    async def get_response_for_problem(
        self, db, session_id, problem_id
    ) -> Response | None:
        """Check for duplicate submission — same session+problem returns existing."""

    async def get_topic_accuracy_for_student(
        self, db, student_id, topic, days=30
    ) -> float:
        """Accuracy % for topic over last N days. Returns 0.0 on empty history."""

    async def get_all_topic_accuracies(
        self, db, student_id, days=30
    ) -> dict[str, float]:
        """{topic: accuracy} for all topics. Used by ProblemSelector mastery weight."""

    async def update_hint_count(
        self, db, response, new_hints_used, hint_viewed
    ) -> Response:
        """Increment hints_used and append to hints_viewed JSON array."""
```

##### 4. Tests [PHASE3-A-2.5]

**Files to create:**
- `tests/unit/test_session_repository.py`
- `tests/unit/test_response_repository.py`
- `tests/unit/test_problem_repository.py`

All use `db_session` fixture (SQLite in-memory via `tests/conftest.py`).

Key test cases:
- `test_create_session_expires_30min()` — expires_at = created_at + 30min exactly
- `test_active_session_not_returned_if_expired()` — expired session returns None
- `test_expire_stale_marks_abandoned()` — old sessions get ABANDONED status
- `test_duplicate_response_returns_existing()` — same session+problem → no new row
- `test_topic_accuracy_empty_history_returns_zero()` — no div-by-zero on empty
- `test_recently_seen_excludes_from_selection()` — exclude_ids works
- `test_get_problems_empty_grade_returns_empty()` — grade with 0 problems → []

#### Success Criteria

- [ ] All three repositories created with fully async methods
- [ ] `src/repositories/__init__.py` exports `ProblemRepository, SessionRepository, ResponseRepository`
- [ ] `SessionRepository.create_session()` persists (via flush) before returning
- [ ] Unit tests ≥80% coverage on all three files
- [ ] Integration test: create session → submit 5 responses → verify session.status == COMPLETED
- [ ] `from src.repositories import SessionRepository` works without import errors

---

## Track B: API & Services (Jodha)

### PHASE3-B-1: Problem Selection Algorithm (REQ-008)

**Task ID:** PHASE3-B-1
**Owner:** Jodha (FastAPI Backend Expert)
**Duration:** ~2.5 days
**Blocker:** None — starts Day 1 (can run with existing Problem model; answer_type not required yet)
**Blocks:** PHASE3-B-3

#### Deliverables

- [ ] **PHASE3-B-1.1** — `src/services/problem_selector.py` — ProblemSelector service
- [ ] **PHASE3-B-1.2** — Algorithm implements REQ-008 weights: 50% recency / 30% mastery / 20% difficulty
- [ ] **PHASE3-B-1.3** — Deterministic: same inputs → same problem_ids output
- [ ] **PHASE3-B-1.4** — All edge cases handled (new student, sparse grade, all topics mastered)
- [ ] **PHASE3-B-1.5** — Unit tests ≥80% coverage, all edge cases covered with mocked repos
- [ ] **PHASE3-B-1.6** — Performance: `select_problems()` completes in <500ms

#### Detailed Work

##### 1. ProblemSelector Service [PHASE3-B-1.1, PHASE3-B-1.2]

**File to create:** `src/services/problem_selector.py`

**Algorithm (REQ-008: 50% recency / 30% mastery / 20% difficulty):**

```
score(problem, position) =
    topic_recency_score(problem.topic)  * 0.50
  + mastery_score(problem.topic)        * 0.30
  + difficulty_variation_score(problem.difficulty, position) * 0.20
```

**topic_recency_score:**
- Topic not in last 7 days → 1.0
- Last practiced 4-6 days ago → 0.8
- Last practiced 1-3 days ago → 0.5
- Last practiced today → 0.2

**mastery_score:**
- Topic never attempted → 0.8 (new topic: moderate priority)
- Accuracy < 40% → 1.0 (struggling: high priority)
- Accuracy 40-70% → 0.6 (developing)
- Accuracy > 70% → 0.2 (proficient: deprioritize)

**difficulty_variation_score (sequencing easy → hard):**
- Position 0-1 (slots 1-2): prefer difficulty=1 (easy=1.0, medium=0.3, hard=0.1)
- Position 2-3 (slots 3-4): prefer difficulty=2 (easy=0.3, medium=1.0, hard=0.5)
- Position 4 (slot 5): prefer difficulty=3 (easy=0.1, medium=0.5, hard=1.0)

**Determinism:** Ties broken by `problem_id` ASC.

**Steps:**
1. Fetch `recent_problem_ids` (last 7 days) from ProblemRepository
2. Fetch `topic_accuracies: dict[str, float]` from ResponseRepository
3. Fetch `recent_topics: dict[str, int]` (days since last practice) from ResponseRepository
4. Fetch all problems for student.grade, excluding recent_problem_ids
5. Score every candidate problem using composite formula above
6. Select top-5 by score; sort final selection by difficulty ASC
7. If fewer than 5 available: include recently-seen problems to fill gaps

```python
@dataclass
class ProblemSelection:
    selected_problems: list[Problem]   # Ordered easy → hard
    selection_timestamp: datetime
    reasoning: list[str]               # Human-readable selection log

class ProblemSelector:
    def __init__(self, problem_repo: ProblemRepository, response_repo: ResponseRepository): ...

    async def select_problems(
        self, db: AsyncSession, student_id: int, grade: int
    ) -> ProblemSelection: ...

    def _score_problem(
        self, problem: Problem, recent_topics: dict[str, int],
        topic_accuracies: dict[str, float], position: int
    ) -> float: ...
```

##### 2. Edge Cases [PHASE3-B-1.4]

| Scenario | Behaviour |
|---|---|
| New student, no history | All topics recency=1.0, mastery=0.8; select 5 easiest from diverse topics |
| Grade has < 5 problems | Return all available (problem_count < 5 in response) |
| Student seen all grade problems in 7 days | Fall back to including recent problems |
| All topics mastered (>70%) | Select by recency only; lowest mastery score wins |
| Single topic grade | All 5 from same topic — allowed |

##### 3. Unit Tests [PHASE3-B-1.5]

**File to create:** `tests/unit/test_problem_selector.py`

All tests mock ProblemRepository and ResponseRepository (no DB).

- `test_returns_5_problems_normal_case()` — happy path
- `test_returns_fewer_for_sparse_grade()` — only 3 problems → returns 3
- `test_same_inputs_same_output()` — determinism check (call twice)
- `test_new_student_gets_easy_problems()` — no history → mostly difficulty=1
- `test_recency_weight_applied()` — yesterday's topic scores lower
- `test_mastery_weight_applied()` — 20% accuracy topic scores higher
- `test_output_ordered_easy_to_hard()` — difficulty 1, 1, 2, 2, 3
- `test_no_repeat_within_7_days()` — recently seen problem excluded
- `test_fallback_when_all_seen_recently()` — includes recent problems when no others available

#### Success Criteria

- [ ] Returns `ProblemSelection` with `selected_problems` and `reasoning`
- [ ] 50/30/20 weights correctly applied (verified by unit tests with known inputs)
- [ ] Deterministic output for same inputs
- [ ] All edge cases handled without exceptions
- [ ] No DB queries inside `_score_problem()` — all data fetched before the loop
- [ ] Unit tests ≥80% coverage

---

### PHASE3-B-2: Answer Evaluation Service (REQ-003)

**Task ID:** PHASE3-B-2
**Owner:** Jodha (FastAPI Backend Expert)
**Duration:** ~1.5 days
**Blocked by:** PHASE3-A-1 (answer_type column), PHASE3-A-2 (ResponseRepository)
**Blocks:** PHASE3-B-3

#### Deliverables

- [ ] **PHASE3-B-2.1** — `src/services/answer_evaluator.py` — AnswerEvaluator service
- [ ] **PHASE3-B-2.2** — Numeric evaluation with ±5% tolerance (REQ-003)
- [ ] **PHASE3-B-2.3** — Multiple choice exact index match (REQ-003)
- [ ] **PHASE3-B-2.4** — Input normalisation: strip ₹, commas, units, whitespace
- [ ] **PHASE3-B-2.5** — Confidence level from hints_used (0 hints=high, 1-2=medium, 3=low)
- [ ] **PHASE3-B-2.6** — Bilingual feedback (EN + BN)
- [ ] **PHASE3-B-2.7** — Unit tests ≥80% coverage, all edge cases

#### Detailed Work

##### 1. AnswerEvaluator [PHASE3-B-2.1]

**File to create:** `src/services/answer_evaluator.py`

```python
@dataclass
class EvaluationResult:
    is_correct: bool
    feedback_en: str
    feedback_bn: str
    normalized_answer: str       # What the system compared against
    confidence_level: str        # "low" | "medium" | "high"
    answer_format_valid: bool    # False if student's input was unparseable

class AnswerEvaluator:
    """Evaluate student answers (REQ-003). Pure computation — no I/O, <10ms."""

    def evaluate(
        self, problem: Problem, student_answer: str, hints_used: int
    ) -> EvaluationResult: ...

    def _evaluate_numeric(
        self, correct: str, student: str, tolerance_percent: float
    ) -> tuple[bool, bool]: ...   # (is_correct, format_valid)

    def _evaluate_multiple_choice(
        self, correct: str, student: str
    ) -> tuple[bool, bool]: ...

    def _normalize_answer(self, raw: str) -> str:
        """Strip spaces, commas (,/،), ₹$€£, trailing units (rupees, kg, cm...).
        '₹  75 rupees' → '75' | '3,500' → '3500'"""

    def _derive_confidence(self, hints_used: int) -> str:
        """0 → 'high', 1-2 → 'medium', 3 → 'low'."""
```

**Numeric tolerance (REQ-003: ±5%):**
```
tolerance = abs(correct_value × tolerance_percent / 100)
is_correct = abs(student_value − correct_value) ≤ tolerance
```
Edge: `correct_answer = "0"` → tolerance = 0, only exact match accepted.

**MC evaluation:** `correct_answer` stores index as string ("1" = second option).
Normalise student input: "a"→0, "b"→1, "c"→2, "d"→3, digits as-is.

**Feedback messages:**
- Correct: "Correct! ✅ Well done!" / "সঠিক! ✅ শাবাশ!"
- Wrong: "Not quite. Try again or ask for a hint." / "ঠিক হয়নি। আবার চেষ্টা করো বা hint চাও।"
- Format invalid: "Please write just the number." / "শুধু সংখ্যাটা লেখো।"

##### 2. Unit Tests [PHASE3-B-2.7]

**File to create:** `tests/unit/test_answer_evaluator.py`

- `test_numeric_exact_match()` — "75" == "75" → correct
- `test_numeric_within_tolerance()` — "74" for "75" (1.3%) → correct
- `test_numeric_outside_tolerance()` — "70" for "75" (6.7%) → wrong
- `test_numeric_zero_answer_exact_only()` — correct="0", any deviation → wrong
- `test_mc_exact_index()` — "1" == "1" → correct
- `test_mc_letter_input()` — "b" maps to index 1 → correct when answer="1"
- `test_normalize_rupee_symbol()` — "₹75" → "75"
- `test_normalize_trailing_units()` — "75 rupees" → "75"
- `test_normalize_commas()` — "3,500" → "3500"
- `test_blank_answer_format_invalid()` — "" → format_valid=False, is_correct=False
- `test_gibberish_format_invalid()` — "abc" → format_valid=False
- `test_confidence_no_hints()` — hints_used=0 → "high"
- `test_confidence_all_hints()` — hints_used=3 → "low"

#### Success Criteria

- [ ] Numeric ±5% tolerance correct on all test cases
- [ ] MC exact match handles letter and digit inputs
- [ ] Normalisation handles ₹, commas, trailing units, whitespace
- [ ] Blank/gibberish → format_valid=False, is_correct=False (no crash)
- [ ] `evaluate()` completes in <10ms (pure Python, no I/O)
- [ ] Unit tests ≥80% coverage

---

### PHASE3-B-3: Wire Practice Endpoints End-to-End (REQ-001, REQ-007)

**Task ID:** PHASE3-B-3
**Owner:** Jodha (FastAPI Backend Expert)
**Duration:** ~2 days
**Blocked by:** PHASE3-B-1, PHASE3-B-2, PHASE3-A-2
**Blocks:** PHASE3-C-1, PHASE3-C-2, PHASE3-C-3

#### Deliverables

- [ ] **PHASE3-B-3.1** — `GET /practice` — real problem selection + session creation, no mock data
- [ ] **PHASE3-B-3.2** — `POST /practice/{problem_id}/answer` — real evaluation + persisted response
- [ ] **PHASE3-B-3.3** — `POST /practice/{problem_id}/hint` — session/problem validated, pre-written hint served
- [ ] **PHASE3-B-3.4** — Session resume logic (REQ-007): reconnecting student gets remaining problems
- [ ] **PHASE3-B-3.5** — Session expiry: stale sessions auto-abandoned on next `/practice` call
- [ ] **PHASE3-B-3.6** — "Already completed today" response when session is COMPLETED
- [ ] **PHASE3-B-3.7** — Feedback language follows student.language (Bengali or English)
- [ ] **PHASE3-B-3.8** — Integration tests ≥70% coverage on `src/routes/practice.py`

#### Detailed Work

##### 1. GET /practice [PHASE3-B-3.1, PHASE3-B-3.4, PHASE3-B-3.5, PHASE3-B-3.6]

Replace all mock data in `src/routes/practice.py`:

```
1. verify_student (already a Depends)
2. Fetch Student by telegram_id → get student.student_id, student.grade
3. session_repo.expire_stale_sessions(db)  # clean up abandoned
4. existing = session_repo.get_active_session_for_today(db, student_id)
   → If COMPLETED: return {session_id, problems:[], already_complete:True}
   → If IN_PROGRESS (resume): filter out answered problems, return remaining
   → If None: run selection
5. selection = problem_selector.select_problems(db, student_id, student.grade)
6. session = session_repo.create_session(db, student_id, selection.problem_ids)
7. Return PracticeResponse(session_id, problems_without_answers, problem_count, expires_at)
```

**Resume state:** `answered_ids = {r.problem_id for r in session.responses}`
Return problems whose `problem_id` not in `answered_ids`, in original order.

##### 2. POST /practice/{problem_id}/answer [PHASE3-B-3.2, PHASE3-B-3.7]

```
1. verify_student (Depends)
2. Validate session_id (body) — fetch session, check ownership (Noor wires this in C-1)
3. Verify problem_id in session.problem_ids
4. Check duplicate: response_repo.get_response_for_problem(session_id, problem_id) → return existing if found
5. Fetch Problem from problem_repo
6. hints_used = existing_response.hints_used if exists else 0
7. result = answer_evaluator.evaluate(problem, student_answer, hints_used)
8. response_repo.create_response(session_id, problem_id, student_answer, result.is_correct, hints_used, ...)
9. If result.is_correct: session_repo.increment_correct_count(session)
10. Find next_problem_id: next unanswered in session.problem_ids
11. If no next: session_repo.mark_session_complete(session)
12. Feedback text = result.feedback_bn if student.language == "bn" else result.feedback_en
13. Return AnswerResponse(is_correct, feedback_text, next_problem_id)
```

##### 3. POST /practice/{problem_id}/hint [PHASE3-B-3.3]

```
1. verify_student (Depends)
2. Validate session ownership + problem in session (Noor wires C-1 here)
3. Fetch Problem from problem_repo
4. existing_response = response_repo.get_response_for_problem(session_id, problem_id)
5. hints_already_used = existing_response.hints_used if exists else 0
6. If hints_already_used >= 3: raise 400 ERR_HINT_LIMIT_EXCEEDED
7. If hint_number <= hints_already_used: return cached (idempotent)
8. hint = problem.get_hints()[hint_number - 1]
9. hint_text = hint.text_bn if student.language == "bn" else hint.text_en
10. Create or update Response (stub with is_correct=False if no submission yet)
11. response_repo.update_hint_count(response, hints_already_used + 1, hint.to_dict())
12. Return HintResponse(hint_text, hint_number, hints_remaining=3 - hint_number)
```

Note: Claude API integration is Phase 4 (TASK-015). Phase 3 serves pre-written hints only.
`hint.is_ai_generated == False` confirms source.

##### 4. Integration Tests [PHASE3-B-3.8]

**File to create:** `tests/integration/test_practice_flow.py`

Uses `AsyncClient` wrapping FastAPI app + seeded DB.

- `test_get_practice_returns_5_real_problems()` — not mock data
- `test_session_persisted_before_response_returned()` — DB check after GET /practice
- `test_submit_correct_answer_numeric()` — "90" for correct "90" → is_correct=True
- `test_submit_wrong_answer_numeric()` — "999" → is_correct=False
- `test_submit_5_answers_completes_session()` — session.status == COMPLETED
- `test_resume_mid_session()` — 2 answers → reconnect → GET /practice returns 3 remaining
- `test_expired_session_creates_new()` — set expires_at to past → new session created
- `test_hint_returns_prewritten_not_claude()` — hint.is_ai_generated == False
- `test_hint_limit_exceeded()` — 4th hint request → 400
- `test_already_completed_returns_empty_problems()` — second GET /practice after completion

#### Success Criteria

- [ ] `GET /practice` returns real problems from DB (no mock data)
- [ ] Session row created in DB before response returned (REQ-007)
- [ ] `POST /practice/{problem_id}/answer` evaluates correctly + persists Response
- [ ] `session.problems_correct` increments on each correct answer
- [ ] Session auto-completes when all 5 problems answered
- [ ] Resume: second GET /practice returns remaining unanswered problems
- [ ] Feedback language follows student.language
- [ ] Pre-written hints served from `Problem.hints` JSON
- [ ] All endpoints return correct error codes (ERR_SESSION_EXPIRED, ERR_HINT_LIMIT_EXCEEDED, etc.)
- [ ] Integration tests ≥70% coverage on practice.py

---

### PHASE3-B-4: Telegram /practice Command Wiring

**Task ID:** PHASE3-B-4
**Owner:** Jodha (FastAPI Backend Expert)
**Duration:** ~1 day
**Blocked by:** PHASE3-B-3 (REST endpoints must work before wiring Telegram to them)
**Blocks:** Phase 4

#### Deliverables

- [ ] **PHASE3-B-4.1** — `/practice` Telegram command → calls `GET /practice` internally, sends 5 problems as numbered messages
- [ ] **PHASE3-B-4.2** — Answer submission: text message during active session → `POST /practice/{problem_id}/answer`
- [ ] **PHASE3-B-4.3** — `/hint` Telegram command → `POST /practice/{problem_id}/hint`
- [ ] **PHASE3-B-4.4** — In-session state tracking: store `(session_id, current_problem_id)` per telegram_id
- [ ] **PHASE3-B-4.5** — Bilingual responses: sends Bengali text if student.language == "bn"
- [ ] **PHASE3-B-4.6** — `/practice` on completed session: sends "আজকের অনুশীলন শেষ! কাল আবার এসো।"
- [ ] **PHASE3-B-4.7** — Integration test: simulate Telegram webhook payload → assert bot reply messages

#### Detailed Work

##### 1. Telegram Session State [PHASE3-B-4.4]

The Telegram webhook is stateless — each message arrives independently.
Between messages, the bot must remember which session and problem a student is currently on.

**Approach:** Store `(session_id, current_problem_index)` in the database on the Student model
or as a simple in-memory dict keyed by `telegram_id` (acceptable for 50-student pilot).

For MVP: use a module-level dict in `src/routes/webhook.py`:
```python
# In-memory state for active sessions (sufficient for 50-student pilot)
# Maps telegram_id → {session_id: int, current_problem_id: int}
_active_sessions: dict[int, dict] = {}
```

Phase 4/5: migrate to Redis or a `student_sessions` DB column if pilot scales.

##### 2. /practice Command Handler [PHASE3-B-4.1]

**File to modify:** `src/routes/webhook.py`

Add command handler called when Telegram message text == "/practice":

```python
async def handle_practice_command(telegram_id: int, db: AsyncSession) -> str:
    """Handle /practice command. Returns message text to send back to student."""
    # 1. Fetch or create student (already exists from /start)
    # 2. Call practice endpoint logic directly (reuse service layer, not HTTP call)
    # 3. If already_complete: return completion message in student's language
    # 4. Store {session_id, current_problem_id: first_problem.problem_id} in _active_sessions
    # 5. Format problems as numbered list and return
```

**Message format for 5 problems:**
```
📚 আজকের অনুশীলন শুরু হচ্ছে! (5টি প্রশ্ন)

প্রশ্ন ১/৫:
একজন দোকানদার ৪৫০ টাকায় আলু কিনে ৫৪০ টাকায় বিক্রি করল। লাভ কত?

উত্তর দিতে শুধু সংখ্যাটা লেখো। Hint পেতে /hint লেখো।
```

##### 3. Answer Message Handler [PHASE3-B-4.2]

When a message arrives from a student who has an active session in `_active_sessions`:

```python
async def handle_answer_message(telegram_id: int, text: str, db: AsyncSession) -> str:
    """Handle free-text answer during active session."""
    state = _active_sessions.get(telegram_id)
    if not state:
        return "কোনো সক্রিয় অনুশীলন নেই। /practice লিখে শুরু করো।"

    # Call answer evaluation logic directly (reuse AnswerEvaluator + ResponseRepository)
    # Update _active_sessions to point to next_problem_id
    # If session complete: remove from _active_sessions, return score summary
    # Return feedback + next problem text (or final score if done)
```

**Score summary on completion:**
```
✅ অনুশীলন শেষ! তোমার স্কোর: ৩/৫

কাল আবার এসো। /practice
```

##### 4. /hint Command Handler [PHASE3-B-4.3]

```python
async def handle_hint_command(telegram_id: int, db: AsyncSession) -> str:
    state = _active_sessions.get(telegram_id)
    if not state:
        return "কোনো সক্রিয় প্রশ্ন নেই।"

    # Determine hint_number from current response.hints_used + 1
    # Call hint logic directly (reuse Problem.get_hints())
    # Return hint text in student's language
```

##### 5. Routing Logic in webhook.py [PHASE3-B-4.1 to 4.3]

Update the main `POST /webhook` handler to route messages:

```python
text = update.message.text.strip() if update.message else ""

if text == "/practice":
    reply = await handle_practice_command(telegram_id, db)
elif text == "/hint":
    reply = await handle_hint_command(telegram_id, db)
elif telegram_id in _active_sessions:
    reply = await handle_answer_message(telegram_id, text, db)
else:
    reply = await handle_unknown_message(telegram_id, text)  # existing handler
```

##### 6. Integration Test [PHASE3-B-4.7]

**File to create:** `tests/integration/test_telegram_practice_flow.py`

Uses `AsyncClient` with mock Telegram webhook payloads.

- `test_practice_command_sends_5_problems()` — POST /webhook with `/practice` → response body contains problem text
- `test_answer_message_evaluates_and_replies()` — send answer text → response has "সঠিক" or "ঠিক হয়নি"
- `test_hint_command_returns_hint()` — `/hint` during session → returns hint text
- `test_5_answers_sends_score_summary()` — complete session via Telegram → score message sent
- `test_practice_command_after_completion()` — second `/practice` → "আজকের অনুশীলন শেষ" message

#### Success Criteria

- [ ] `/practice` via Telegram returns 5 real problems as numbered messages
- [ ] Student can submit answer by typing a number — bot replies with correct/wrong feedback
- [ ] `/hint` returns Hint 1 → Hint 2 → Hint 3 progressively
- [ ] Score summary sent when all 5 problems answered
- [ ] All messages in Bengali if `student.language == "bn"`
- [ ] Integration tests pass for full Telegram practice flow

---

## Track C: Security & Observability (Noor)

### PHASE3-C-1: Session Ownership + IDOR Prevention

**Task ID:** PHASE3-C-1
**Owner:** Noor (Security & Logging Expert)
**Duration:** ~1.5 days
**Blocked by:** PHASE3-B-3 (endpoints must exist to harden them)
**Blocks:** Phase 4 launch

#### Deliverables

- [ ] **PHASE3-C-1.1** — `src/auth/session.py` — `verify_session_owner()` FastAPI dependency
- [ ] **PHASE3-C-1.2** — `verify_problem_in_session()` guard function
- [ ] **PHASE3-C-1.3** — Both answer + hint endpoints use `Depends(verify_session_owner)`
- [ ] **PHASE3-C-1.4** — Expired session returns HTTP 410 Gone (not 400 or 404)
- [ ] **PHASE3-C-1.5** — IDOR attempts logged at WARNING with student hashes
- [ ] **PHASE3-C-1.6** — Security tests: IDOR, expired, completed, problem not in session

#### Detailed Work

##### 1. verify_session_owner Dependency [PHASE3-C-1.1]

**File to create:** `src/auth/session.py`

```python
async def verify_session_owner(
    session_id: int,                                    # from request body
    student_id: int = Depends(verify_student),          # already-verified telegram_id
    db: AsyncSession = Depends(get_session),
) -> Session:
    """Verify the authenticated student owns the session.

    Prevents IDOR (CWE-639): Student A cannot submit into Student B's session.

    Raises:
        404: Session not found
        403: Session owned by a different student (logs IDOR attempt)
        410: Session expired (use 410 Gone)
        409: Session already completed
    """
    session = await session_repo.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(404, detail="Session not found")

    student = await student_repo.get_by_telegram_id(db, student_id)
    if session.student_id != student.student_id:
        logger.warning(
            "IDOR attempt",
            extra={
                "event": "practice.security.idor_attempt",
                "attacker_hash": sha256(str(student_id)),
                "target_session_id": session_id,
                "target_owner_hash": sha256(str(session.student_id)),
                "severity": "HIGH",
            },
        )
        raise HTTPException(403, detail="Not your session")

    if session.is_expired():
        raise HTTPException(410, detail="Session expired")

    if session.status == SessionStatus.COMPLETED:
        raise HTTPException(409, detail="Session already completed")

    return session
```

##### 2. verify_problem_in_session [PHASE3-C-1.2]

```python
def verify_problem_in_session(problem_id: int, session: Session) -> None:
    """Verify problem_id belongs to this session (prevents IDOR on problem resource).

    Raises:
        400 ERR_PROBLEM_NOT_FOUND: problem not in session.problem_ids
    """
    if problem_id not in session.problem_ids:
        raise HTTPException(
            400,
            detail=f"Problem {problem_id} is not part of session {session.session_id}",
            headers={"X-Error-Code": "ERR_PROBLEM_NOT_FOUND"},
        )
```

##### 3. Security Tests [PHASE3-C-1.6]

**File to create:** `tests/unit/test_session_security.py`

- `test_cross_student_session_access_returns_403()` — IDOR → 403
- `test_expired_session_returns_410_not_400()` — must be 410 Gone
- `test_completed_session_returns_409()` — re-submission blocked
- `test_problem_not_in_session_returns_400()` — problem from different session
- `test_nonexistent_session_returns_404()`
- `test_idor_attempt_logged_at_warning()` — log contains severity=HIGH

#### Success Criteria

- [ ] Student A cannot access Student B's session (403 returned, not 404 or 500)
- [ ] Expired session returns 410 (not 400 or 404)
- [ ] `verify_session_owner` is a `Depends` on both answer + hint endpoints
- [ ] IDOR attempt logged at WARNING with hashed student IDs (no raw telegram_id)
- [ ] Security tests 100% coverage on `src/auth/session.py`

---

### PHASE3-C-2: Structured Practice Event Logging

**Task ID:** PHASE3-C-2
**Owner:** Noor (Security & Logging Expert)
**Duration:** ~1 day
**Blocked by:** PHASE3-B-3

#### Deliverables

- [ ] **PHASE3-C-2.1** — 5 structured log events emitted on every practice action
- [ ] **PHASE3-C-2.2** — `student_answer` never appears in any log line
- [ ] **PHASE3-C-2.3** — `telegram_id` never logged raw — SHA-256 hash only
- [ ] **PHASE3-C-2.4** — Unit tests verify log format and PII absence

#### Detailed Work

##### 1. Log Events Required [PHASE3-C-2.1]

Add structured log calls to `src/routes/practice.py`:

| Event | Trigger | Key Fields |
|---|---|---|
| `practice.session.created` | GET /practice (new session) | session_id, grade, problem_count, problem_ids, expires_at, selection_reasoning |
| `practice.session.resumed` | GET /practice (resume) | session_id, remaining_problems, problems_already_answered |
| `practice.answer.submitted` | POST /practice/{id}/answer | session_id, problem_id, topic, is_correct, hints_used, confidence_level, time_spent_seconds |
| `practice.hint.requested` | POST /practice/{id}/hint | session_id, problem_id, hint_number, hints_remaining, hint_source="prewritten" |
| `practice.session.completed` | When 5th answer submitted | session_id, problems_correct, total_problems, accuracy_percent |

**Never log:** `student_answer`, raw `telegram_id`, `student_name`.

##### 2. PII Masking [PHASE3-C-2.3]

```python
def _hash_student_id(telegram_id: int) -> str:
    return hashlib.sha256(str(telegram_id).encode()).hexdigest()[:16]
```

Verify `SensitiveDataFilter` in `src/logging/config.py` blocks `student_answer` and `telegram_id` field names.

##### 3. Tests [PHASE3-C-2.4]

**File to create:** `tests/unit/test_practice_logging.py`

- `test_session_created_event_emitted()` — mock logger, event="practice.session.created"
- `test_student_answer_not_in_logs()` — "student_answer" not in captured log output
- `test_telegram_id_not_logged_raw()` — raw telegram_id value not in any log line
- `test_idor_attempt_severity_high()` — security event logged with severity="HIGH"

#### Success Criteria

- [ ] All 5 event types logged on every corresponding action
- [ ] `student_answer` field absent from all log output
- [ ] Raw `telegram_id` absent — only 16-char SHA-256 prefix logged
- [ ] Log schema consistent: every event has `event`, `student_id_hash`, `session_id`

---

### PHASE3-C-3: Cost Tracking Stubs for Future Claude Calls

**Task ID:** PHASE3-C-3
**Owner:** Noor (Security & Logging Expert)
**Duration:** ~1 day
**Blocked by:** PHASE3-B-3
**Blocks:** Phase 4 (Claude hint integration plugs into this)

#### Deliverables

- [ ] **PHASE3-C-3.1** — `src/services/cost_tracker.py` — CostTracker service
- [ ] **PHASE3-C-3.2** — `request_hint` endpoint calls `cost_tracker.record_hint_cost()`
- [ ] **PHASE3-C-3.3** — Every hint creates a CostRecord with cost_usd=0.00 (pre-written)
- [ ] **PHASE3-C-3.4** — `check_budget_alert()` warns when projected cost > $0.10/student/month
- [ ] **PHASE3-C-3.5** — Unit tests ≥80% coverage

#### Detailed Work

##### 1. CostTracker Service [PHASE3-C-3.1]

**File to create:** `src/services/cost_tracker.py`

```python
# Claude Haiku pricing (as of 2026): $0.25/1M input, $1.25/1M output
HAIKU_INPUT_COST_PER_TOKEN = 0.25 / 1_000_000
HAIKU_OUTPUT_COST_PER_TOKEN = 1.25 / 1_000_000
BUDGET_PER_STUDENT_USD = 0.10   # Non-negotiable ceiling (CLAUDE.md)

class CostTracker:
    """Track API costs for $0.10/student/month ceiling (REQ-032).

    Phase 3: Records $0.00 for pre-written hints.
    Phase 4: Pass real token counts to record actual Claude costs.
    Design: endpoint code does NOT change between Phase 3 and Phase 4.
    """

    async def record_hint_cost(
        self, db, student_id, session_id, hint_number,
        is_ai_generated=False,
        input_tokens=None, output_tokens=None,
    ) -> CostRecord:
        """Cost = $0.00 for pre-written; calculated from tokens for Claude."""
        cost_usd = 0.0
        if is_ai_generated and input_tokens and output_tokens:
            cost_usd = (
                input_tokens * HAIKU_INPUT_COST_PER_TOKEN
                + output_tokens * HAIKU_OUTPUT_COST_PER_TOKEN
            )
        # create CostRecord, db.flush(), return

    async def get_student_cost_this_month(
        self, db, student_id
    ) -> float:
        """Total cost for student in current calendar month."""

    async def check_budget_alert(
        self, db, student_count: int
    ) -> bool:
        """Return True if projected monthly cost per student > $0.10."""
```

##### 2. Unit Tests [PHASE3-C-3.5]

- `test_prewritten_hint_zero_cost()` — is_ai_generated=False → cost_usd=0.0
- `test_claude_hint_calculates_cost()` — 100 input + 50 output → correct USD
- `test_budget_alert_above_threshold()` — projected > $0.10/student → True
- `test_budget_alert_below_threshold()` — projected < $0.10 → False

#### Success Criteria

- [ ] Every hint request creates a CostRecord (even at $0.00)
- [ ] Phase 4 only needs `is_ai_generated=True` + token counts — no endpoint changes
- [ ] `check_budget_alert()` uses $0.10/student ceiling from CLAUDE.md
- [ ] Unit tests ≥80% coverage

---

## Parallel Execution Timeline

```
Day 1          Day 2          Day 3          Day 4          Day 5          Day 6
┌──────────────────────────────────────────────────────────────────────────────┐
│ MARYAM (Track A)                                                             │
│ [PHASE3-A-1: Migration + Seed ────────────] [PHASE3-A-2: Repositories ────] │
│ ←────────────── 2 days ───────────────────→ ←──────── 1.5 days ───────────→ │
├──────────────────────────────────────────────────────────────────────────────┤
│ JODHA (Track B)                                                              │
│ [PHASE3-B-1: Problem Selector ────────────────] [B-2: Evaluator] [B-3: Wire]│
│ ←───────────── 2.5 days ──────────────────────→ ←── 1.5d ──────→ ←─ 2d ──→ │
├──────────────────────────────────────────────────────────────────────────────┤
│ NOOR (Track C)                                                               │
│ [Design review / test scaffolding ────────────────────] [C-1] [C-2] [C-3]   │
│ ←──────────────── 3 days prep ────────────────────────→ ←1.5→ ←1d→ ←1d→    │
└──────────────────────────────────────────────────────────────────────────────┘

Day 7-8: Cross-track integration testing + demo rehearsal
```

**Serial critical path:** A-1 → A-2 → B-2 → B-3 → C-1,2,3 = 8 days
**With parallelisation:** ~6 days elapsed (A-1 and B-1 run concurrently from Day 1)

---

## Phase 3 Go/No-Go Criteria

Before marking Phase 3 complete and starting Phase 4:

- [ ] `python scripts/seed_problems.py` inserts 280 problems — `SELECT COUNT(*)` confirms
- [ ] `GET /practice` returns 5 real DB problems (not mock data)
- [ ] `POST /practice/{id}/answer` persists response in DB and evaluates numeric ±5%
- [ ] Session resume: disconnect + reconnect returns remaining unanswered problems
- [ ] Student A cannot access Student B's session (403 verified by security test)
- [ ] All integration tests pass: `pytest tests/integration/test_practice_flow.py`
- [ ] All unit tests pass: `pytest tests/unit/ -v`
- [ ] Coverage ≥70%: `pytest --cov=src --cov-report=term`
- [ ] Demo script runs end-to-end without errors

**Hand-off to Phase 4:**
- `responses` table populated → adaptive difficulty algorithm can read performance data
- Cost tracking wired → Phase 4 plugs in Claude API by changing `is_ai_generated=True`
- Session state persisted → streak tracking (Phase 4/5) reads completed sessions

---

## Notes & Constraints

1. **Grade 8 content:** Zero grade_8 YAML files seeded yet. ProblemSelector must handle empty grade without exception. Alert Jahanara/content team.
2. **Bengali translations:** All YAML marked `bn_reviewed: false`. Do NOT gate Phase 3 on review — that is a content milestone.
3. **Streak update:** When session completes, log intent but don't implement. Streaks are Phase 4 (TASK-024).
4. **Claude integration:** Hint endpoint serves pre-written hints only. Claude API (TASK-015) is Phase 4. Cost stubs are wired and ready.
5. **Session auto-expire scheduler:** REQ-007 mentions background expiry. Phase 3 handles expiry reactively (on next `/practice` call). Background scheduler is Phase 7 (operations).
