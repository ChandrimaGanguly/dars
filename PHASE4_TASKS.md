# Phase 4 Tasks: Learning Optimization + Engagement Engine

**Duration:** Week 3-4 (8 days of agent work across 4 parallel tracks)
**Status:** ✅ COMPLETE — All tracks A, B, C, D done. 419 tests passing (359 unit + 60 integration). Coverage 75%.

**Roadmap references:**
- AGENT_ROADMAP.md → Phase 4 (Learning Optimization), Phase 5 (Claude Hints — partial), Phase 6 (Engagement)
- REQUIREMENTS.md → REQ-003, REQ-004, REQ-006, REQ-009, REQ-010, REQ-012, REQ-013

**Demo target:**
"Student completes today's practice → sees '🔥 Day 3 streak!' in the completion message → types `/streak` → sees real data with milestone countdown. Next session: student who scored 4/5 yesterday gets harder problems; student who scored 1/5 gets easier ones. Student who answered wrong sees a format hint ('Did you include the unit?')."

---

## Pre-conditions (verify before starting)

- [x] PHASE3 complete — all tracks A, B, C done, 180+ tests passing
- [x] Streak model exists (`src/models/streak.py`) with full schema
- [x] Session completion wired in `webhook.py` and `practice.py`
- [x] ProblemSelector implemented with 50/30/20 weights
- [x] AnswerEvaluator implemented with numeric ±5%, MC, text
- [x] **GAP CLOSED:** StreakRepository implemented — `/streak` returns real DB data (PHASE4-A-1)
- [x] **GAP CLOSED:** AdaptiveDifficultyService implemented — ProblemSelector filters by difficulty_level (PHASE4-B-1, B-2)
- [x] **GAP CLOSED:** `difficulty_level` column on Student with Alembic migration (PHASE4-A-2)
- [x] **GAP CLOSED:** EncouragementService implemented — bilingual messages, streak-aware, milestone-aware (PHASE4-D-2)

---

## Task Summary

| Task ID | Task Name | Owner | Duration | Blocked By | Blocks | Status |
|---------|-----------|-------|----------|-----------|--------|--------|
| PHASE4-A-1 | StreakRepository + upsert logic | Maryam | 1.5 days | None | PHASE4-B-3, PHASE4-B-4, PHASE4-C-2 | ✅ Complete |
| PHASE4-A-2 | `difficulty_level` on Student + migration | Maryam | 0.5 days | None | PHASE4-B-1, PHASE4-B-2 | ✅ Complete |
| PHASE4-B-1 | AdaptiveDifficulty service | Jodha | 1.5 days | PHASE4-A-2 | PHASE4-B-2, PHASE4-C-1 | ✅ Complete |
| PHASE4-B-2 | Wire difficulty into ProblemSelector | Jodha | 0.5 days | PHASE4-B-1 | PHASE4-C-1 | ✅ Complete |
| PHASE4-B-3 | Wire streak increment on session complete | Jodha | 1 day | PHASE4-A-1 | PHASE4-B-4, PHASE4-C-2 | ✅ Complete |
| PHASE4-B-4 | Real /streak endpoint + milestone display | Jodha | 0.5 days | PHASE4-A-1, PHASE4-B-3 | PHASE4-C-2 | ✅ Complete |
| PHASE4-B-5 | Learning path summary at session start | Jodha | 0.5 days | None | — | ✅ Complete |
| PHASE4-C-1 | Integration tests: adaptive difficulty flow | Noor | 1 day | PHASE4-B-2 | — | ✅ Complete |
| PHASE4-C-2 | Integration tests: streak tracking flow | Noor | 1 day | PHASE4-B-3, PHASE4-B-4 | — | ✅ Complete |
| PHASE4-C-3 | Difficulty decision structured logging | Noor | 0.5 days | PHASE4-B-1 | — | ✅ Complete |
| PHASE4-C-4 | Coverage gate: maintain ≥70% post-phase | Noor | ongoing | All | — | ✅ Complete (75%) |
| PHASE4-D-1 | Answer evaluation: format hints + normalization | Jahanara | 1 day | None | — | ✅ Complete |
| PHASE4-D-2 | Encouragement message library (REQ-013) | Jahanara | 1 day | None | — | ✅ Complete |
| PHASE4-D-3 | Session-start "Today's topics" bilingual messages | Jahanara | 0.5 days | None | PHASE4-B-5 | ✅ Complete |

---

## Agents Checklist (all agents must follow)

All agents must follow `AGENT_CHECKLIST.md` before any task:

```bash
# 1. Verify pipeline is green before touching anything
bash scripts/validate.sh --skip-slow

# 2. Create feature branch
git checkout -b feature/PHASE4-X-Y-description

# 3. While coding: fast validation
bash scripts/validate.sh --fix --skip-slow

# 4. Before every commit: full validation
bash scripts/validate.sh
# Must pass: Black, Ruff, MyPy strict, pytest unit, coverage ≥70%, no secrets

# 5. Commit with conventional format
git commit -m "feat(phase4): ..."
```

---

## Track A: Maryam — Database & ORM

**Owner:** Maryam
**Skill file:** `openspec/agents/maryam.md`
**Duration:** 2 days
**Start condition:** Can start immediately (no blockers)

### PHASE4-A-1: StreakRepository

**Requirement:** REQ-009 (Streak Tracking), REQ-010 (Streak Display), REQ-012 (Streak Milestones)
**File:** `src/repositories/streak_repository.py`

Implement a `StreakRepository` class matching the pattern of existing repositories:

```
StreakRepository:
  get_or_create(db, student_id) → Streak
    — fetch existing streak row, or INSERT new with current_streak=0
  record_practice(db, student_id, practice_date) → tuple[Streak, list[int]]
    — if practice_date == last_practice_date + 1 day: current_streak += 1
    — if practice_date > last_practice_date + 1 day: current_streak = 1 (reset)
    — if practice_date == last_practice_date: no-op (idempotent, same day)
    — update longest_streak if current_streak > longest_streak
    — detect new milestones [7, 14, 30]: return as second tuple element
    — update last_practice_date
    — flush (do NOT commit — let caller decide transaction boundary)
    — Returns: (updated Streak, list of newly-hit milestone ints)
  get_for_student(db, student_id) → Streak | None
  get_last_7_days(db, student_id) → list[date]
    — Return dates (UTC) of the last 7 calendar days where student practiced
    — Used by /streak display to show calendar view
```

**Constraints:**
- All dates stored as UTC date (not datetime)
- Idempotent on same-day calls (calling twice same day = no-op)
- `record_practice` uses `db.flush()` not `db.commit()` — let caller handle transaction
- Milestone detection must NOT re-fire if milestone already in `milestones_achieved`

**Tests required:**
- `tests/unit/test_streak_repository.py`
  - streak increments on consecutive day
  - streak resets after missed day
  - same-day call is no-op
  - longest streak updated correctly
  - milestone 7 detected, milestone 14 detected, milestone 30 detected
  - milestone not double-counted

### PHASE4-A-2: `difficulty_level` column on Student

**Requirement:** REQ-004 (Adaptive Difficulty)
**Files:** `src/models/student.py`, new Alembic migration

Add `difficulty_level: Mapped[int]` to Student model:
- Default: 1 (easy)
- CheckConstraint: must be in [1, 2, 3]
- Comment: "Current adaptive difficulty level (1=easy, 2=medium, 3=hard; REQ-004)"

Create Alembic migration:
```bash
alembic revision --autogenerate -m "Add difficulty_level to students for adaptive difficulty REQ-004"
```

Add `difficulty_level` to `StudentRepository` (if it exists) or create one with:
- `get_difficulty(db, student_id) → int`
- `set_difficulty(db, student, new_level) → None` — sets + flushes

---

## Track B: Jodha — FastAPI Backend

**Owner:** Jodha
**Skill file:** `openspec/agents/jodha.md`
**Duration:** 4 days
**Start conditions:**
- B-1 (AdaptiveDifficulty service): needs PHASE4-A-2 complete
- B-3, B-4 (streak wiring): needs PHASE4-A-1 complete
- B-5 (learning path): independent (no blockers)

### PHASE4-B-1: AdaptiveDifficulty Service

**Requirement:** REQ-004
**File:** `src/services/adaptive_difficulty.py`

```python
class AdaptiveDifficulty:
    """Compute and update per-student difficulty level based on session performance.

    REQ-004 rules:
    - After 2 consecutive correct answers in a session → increase difficulty (max 3)
    - After 1 wrong answer in a session → decrease difficulty (min 1)
    - Hard problems (level 3) only if accuracy ≥ 80% on recent sessions
    - Difficulty resets to 1 if student hasn't practiced in 7 days
    """

    def compute_new_level(
        self,
        current_level: int,
        session_responses: list[bool],  # [True/False] in answer order
        recent_accuracy: float,          # 0.0-1.0, last 7 days
        days_since_last_practice: int,
    ) -> int:
        """Pure function: compute new difficulty level from session results."""
        ...

    async def update_after_session(
        self,
        db: AsyncSession,
        student: Student,
        session_responses: list[bool],
        recent_accuracy: float,
        days_since_last_practice: int,
    ) -> int:
        """Update student.difficulty_level in DB and return new level."""
        ...
```

**Logic:**
- 7-day reset: if `days_since_last_practice >= 7` → return 1 regardless
- Consecutive correct: scan `session_responses` for 2+ consecutive True → raise level
- Wrong answer: any False in `session_responses` → lower level (but apply consecutive-correct first)
- Hard gate: if computed level = 3 and `recent_accuracy < 0.80` → cap at 2
- Clamp to [1, 3]
- `compute_new_level` must be a pure function (no DB calls) for easy unit testing

**Tests:** `tests/unit/test_adaptive_difficulty.py`
- starts at 1, 2 correct → goes to 2
- starts at 2, 1 wrong → goes to 1
- starts at 3, accuracy < 80% → stays at 2
- 7-day reset → always returns 1
- clamps: can't go below 1 or above 3

### PHASE4-B-2: Wire Difficulty into ProblemSelector

**Requirement:** REQ-004, REQ-008
**Files:** `src/services/problem_selector.py`, `src/routes/webhook.py`, `src/routes/practice.py`

Modify `ProblemSelector.select_problems()` to accept an optional `difficulty_level: int = 0` parameter (0 = no filter).

When `difficulty_level > 0`:
- Filter candidates so ≥60% of selected problems have `problem.difficulty <= difficulty_level`
- Still apply 50/30/20 scoring but within difficulty-filtered candidate set
- Fallback: if not enough problems at requested difficulty, include next level up

Wire into `handle_practice_command()` in `webhook.py` and `GET /practice` in `practice.py`:
- Fetch `student.difficulty_level` before running selection
- Pass to `select_problems()`

### PHASE4-B-3: Wire Streak Increment on Session Completion

**Requirement:** REQ-009
**Files:** `src/routes/webhook.py`, `src/routes/practice.py`

In `handle_answer_message()` (webhook.py) — session complete branch — call:
```python
streak_repo = StreakRepository()
streak, new_milestones = await streak_repo.record_practice(
    db, student_id, date.today()  # UTC date
)
```

Build the completion message to include:
- `🔥 Day {streak.current_streak} streak!` (or `Day 1 streak! Great start!` for first day)
- If `new_milestones`: include celebration (e.g., `🔥🔥🔥 7-day milestone!`, `👑 14-day milestone!`, `⭐ 30-day milestone!`)

Also wire into `POST /practice/{problem_id}/answer` in `practice.py` when session completes.

**Important:** capture `student_id` and `student_language` BEFORE `await db.commit()` (ORM expire-on-commit pattern).

### PHASE4-B-4: Real /streak Endpoint

**Requirement:** REQ-010
**File:** `src/routes/streak.py`

Replace the mock stub with real implementation:
```
GET /streak?student_id=<int> (or via header — match existing pattern)
→ StreakData
  current_streak: int
  longest_streak: int
  last_practice_date: date | None
  milestones_achieved: list[int]
  next_milestone: int | None    # from Streak.get_next_milestone()
  days_to_next: int | None      # next_milestone - current_streak
  last_7_days: list[bool]       # True = practiced, for last 7 calendar days
  updated_at: datetime
```

Update `src/schemas/streak.py` to include `next_milestone`, `days_to_next`, `last_7_days` fields.

### PHASE4-B-5: Learning Path Summary at Session Start

**Requirement:** REQ-006
**Files:** `src/routes/webhook.py`, `src/services/problem_selector.py`

After `select_problems()` returns, compute the distinct topics and show:
```
📚 Today's session: Fractions, Profit & Loss, Algebra
5 problems | Difficulty: Medium
```

- Topics: extract `{p.topic for p in selected_problems}`, format as comma-separated
- Difficulty label: based on student.difficulty_level (Easy/Medium/Hard)
- Bilingual: use student.language (Bengali or English)
- Append this summary to the start of the first problem message

---

## Track C: Noor — Security & Observability

**Owner:** Noor
**Skill file:** `openspec/agents/noor.md`
**Duration:** 2.5 days
**Start conditions:** C-1 needs B-2; C-2 needs B-3, B-4; C-3 needs B-1

### PHASE4-C-1: Integration Tests — Adaptive Difficulty Flow

**Requirement:** REQ-004 testing
**File:** `tests/integration/test_adaptive_difficulty_flow.py`

Tests (all `@pytest.mark.integration`, use `db_session` fixture):

```
test_easy_student_gets_easy_problems
  — student with difficulty_level=1
  — populate DB with difficulty 1, 2, 3 problems
  — select_problems → ≥60% must have difficulty=1

test_difficulty_increases_after_two_correct
  — complete session with 2 consecutive correct
  — update_after_session called
  — student.difficulty_level goes from 1 → 2

test_difficulty_decreases_after_wrong_answer
  — complete session with 1 wrong answer
  — student.difficulty_level goes from 2 → 1

test_hard_gate_requires_80pct_accuracy
  — student with difficulty_level=2, recent_accuracy=0.60
  — compute_new_level: 2 consecutive correct → should NOT go to 3 (accuracy < 80%)

test_seven_day_reset
  — student hasn't practiced in 7 days
  — difficulty resets to 1 regardless of current level
```

### PHASE4-C-2: Integration Tests — Streak Tracking Flow

**Requirement:** REQ-009/010/012 testing
**File:** `tests/integration/test_streak_flow.py`

Tests:
```
test_streak_increments_on_session_completion
  — create student, complete practice session via handle_answer_message
  — check DB: streak.current_streak == 1

test_streak_resets_on_missed_day
  — create streak with current_streak=5, last_practice_date = 3 days ago
  — call record_practice today
  — streak.current_streak == 1 (reset)

test_streak_endpoint_returns_real_data
  — create student with streak data
  — GET /streak → real current_streak, longest_streak, next_milestone

test_milestone_7_detected
  — set streak to 6 days
  — record_practice today → returns new_milestones=[7]
  — check completion message contains milestone celebration

test_same_day_idempotent
  — call record_practice twice same day
  — streak only increments once
```

### PHASE4-C-3: Structured Logging for Difficulty Decisions

**Requirement:** REQ-020 (observability)
**File:** `src/services/adaptive_difficulty.py` (add logging there)

Add structured log entries:
```python
logger.info(
    "Adaptive difficulty updated",
    student_id=student_id,         # NOT hashed (internal service, no PII exposure)
    old_level=current_level,
    new_level=new_level,
    session_responses=len(session_responses),
    consecutive_correct=n,
    recent_accuracy=round(recent_accuracy, 2),
    reason="consecutive_correct" | "wrong_answer" | "7_day_reset" | "hard_gate",
)
```

Add log for streak events:
```python
logger.info(
    "Streak updated",
    hashed_telegram_id=hash_telegram_id(telegram_id),
    current_streak=streak.current_streak,
    new_milestones=new_milestones,
)
```

### PHASE4-C-4: Coverage Gate

After all implementation is committed, run:
```bash
python3 -m pytest tests/ --cov=src --cov-report=term-missing
```

New files must have:
- `src/services/adaptive_difficulty.py` ≥ 85%
- `src/repositories/streak_repository.py` ≥ 80%
- Overall project ≥ 70%

If coverage drops below threshold, add targeted unit tests.

---

## Track D: Jahanara — Content & Evaluation

**Owner:** Jahanara
**Skill file:** `openspec/agents/jahanara.md`
**Duration:** 2.5 days
**Start condition:** All three tasks are independent (no blockers)

### PHASE4-D-1: Answer Evaluation Enhancements

**Requirement:** REQ-003 (enhancement)
**File:** `src/services/answer_evaluator.py`

Add to `EvaluationResult` or evaluation logic:
1. **Input normalization:** strip spaces/commas before evaluation
   - "1,000" → "1000", "  42  " → "42", "42.0" → accept for answer "42"
2. **Format hints:** when answer is wrong, include a `format_hint` in feedback
   - Numeric problems: if student answer has no digits → "Please enter a number"
   - Money problems (topic contains "profit", "loss", "interest"): "Include just the number, not the ₹ sign"
   - Percentage problems: "Include just the number, not the % sign"
   - This is guidance, not the correct answer
3. **Rounding tolerance:** currently ±5% — keep, but also accept if abs difference ≤ 0.5 (for rounding at 2dp)

Update `EvaluationResult` dataclass:
```python
@dataclass
class EvaluationResult:
    is_correct: bool
    feedback_en: str
    feedback_bn: str
    normalized_answer: str
    confidence_level: str
    answer_format_valid: bool
    format_hint_en: str = ""     # NEW — empty if no hint needed
    format_hint_bn: str = ""     # NEW
```

Update `AnswerEvaluator.evaluate()` to populate `format_hint_en/bn`.

Tests: add to `tests/unit/test_answer_evaluator.py`
- "1,000" evaluates correctly for answer "1000"
- "  42  " normalizes to "42"
- wrong numeric answer on profit topic includes format hint about ₹
- wrong percentage answer includes format hint about %

### PHASE4-D-2: Encouragement Message Library

**Requirement:** REQ-013 (Daily Encouragement)
**File:** `src/services/encouragement.py` (new file)

```python
class EncouragementService:
    """Bilingual encouragement messages for correct answers.

    Messages vary by:
    - streak_length: 0-2, 3-6, 7-13, 14+
    - session_score: 0-2/5, 3-4/5, 5/5

    Never repeats exact message in same session.
    """

    def get_correct_message(
        self,
        streak_days: int,
        correct_so_far: int,
        total_in_session: int,
        language: str,
        used_in_session: set[str],   # Message IDs already used
    ) -> str:
        ...

    def get_session_complete_message(
        self,
        streak_days: int,
        correct: int,
        total: int,
        new_milestones: list[int],
        language: str,
    ) -> str:
        ...
```

Message pool (minimum 6 per bucket, both languages):

| Bucket | English examples | Bengali examples |
|--------|-----------------|-----------------|
| Streak 0-2, correct | "Great job! 🎉", "Well done!", "Correct! Keep it up!" | "দারুণ! 🎉", "বাহ!", "সঠিক! চালিয়ে যাও!" |
| Streak 3-6, correct | "You're on a roll! 🔥", "3+ days in a row, nice!" | "তুমি দারুণ করছ! 🔥", "চমৎকার!" |
| Streak 7+, correct | "Unstoppable! 🔥🔥", "Legend! Keep the streak alive!" | "অপ্রতিরোধ্য! 🔥🔥", "কিংবদন্তি!" |
| Session 5/5 | "Perfect score! You're amazing! ⭐" | "পারফেক্ট স্কোর! তুমি অসাধারণ! ⭐" |
| Milestone 7 | "🔥🔥🔥 7-day streak! You're on fire!" | "🔥🔥🔥 ৭ দিনের ধারা! তুমি জ্বলছ!" |
| Milestone 14 | "👑 Two weeks straight! You're unstoppable!" | "👑 দুই সপ্তাহ! তুমি অপ্রতিরোধ্য!" |
| Milestone 30 | "⭐ 30 days! You're a legend!" | "⭐ ৩০ দিন! তুমি কিংবদন্তি!" |

Tests: `tests/unit/test_encouragement.py`
- Different streaks return different messages
- No repeat in same session
- Both languages return non-empty strings
- Milestone messages contain milestone-specific content

### PHASE4-D-3: Session-Start "Today's Topics" Messages

**Requirement:** REQ-006 (Daily Learning Path)
**File:** `src/services/encouragement.py` (add to same file)

```python
def format_session_start(
    topics: list[str],        # e.g. ["profit_loss", "fractions", "algebra"]
    difficulty_level: int,    # 1, 2, 3
    num_problems: int,        # always 5
    language: str,
) -> str:
    """Format the session-start topic summary message."""
    ...
```

Output examples:
```
📚 Today's session: Profit & Loss, Fractions, Algebra
5 problems | Difficulty: Medium
```
```
📚 আজকের অনুশীলন: লাভ-ক্ষতি, ভগ্নাংশ, বীজগণিত
৫টি প্রশ্ন | কঠিনতা: মাঝারি
```

Topic name mappings (snake_case → display):
```python
TOPIC_DISPLAY = {
    "en": {
        "profit_and_loss": "Profit & Loss",
        "fractions": "Fractions",
        "decimals": "Decimals",
        "percentages": "Percentages",
        "algebra": "Algebra",
        "geometry": "Geometry",
        "number_system": "Number System",
        "mensuration": "Mensuration",
        "ratio_and_proportion": "Ratio & Proportion",
        "simple_interest": "Simple Interest",
        "data_handling": "Data Handling",
    },
    "bn": {
        "profit_and_loss": "লাভ-ক্ষতি",
        "fractions": "ভগ্নাংশ",
        "decimals": "দশমিক",
        "percentages": "শতকরা",
        "algebra": "বীজগণিত",
        "geometry": "জ্যামিতি",
        "number_system": "সংখ্যা পদ্ধতি",
        "mensuration": "পরিমিতি",
        "ratio_and_proportion": "অনুপাত ও সমানুপাত",
        "simple_interest": "সরল সুদ",
        "data_handling": "তথ্য পরিচালনা",
    },
}

DIFFICULTY_DISPLAY = {
    "en": {1: "Easy", 2: "Medium", 3: "Hard"},
    "bn": {1: "সহজ", 2: "মাঝারি", 3: "কঠিন"},
}
```

---

## Integration Checkpoints

### CP-1: Database Layer Ready
**Trigger:** After PHASE4-A-1 + PHASE4-A-2 complete
**Verify:**
```bash
python3 -m pytest tests/unit/test_streak_repository.py -v
alembic upgrade head  # migration applies cleanly
alembic downgrade -1  # reversible
alembic upgrade head  # apply again
```
**Gate:** All streak_repository unit tests pass, migration round-trips successfully.

### CP-2: AdaptiveDifficulty Service Works Standalone
**Trigger:** After PHASE4-B-1 complete
**Verify:**
```bash
python3 -m pytest tests/unit/test_adaptive_difficulty.py -v
```
**Gate:** All pure-function tests pass for `compute_new_level()`.

### CP-3: Full Practice → Streak → /streak Flow
**Trigger:** After PHASE4-B-3 + PHASE4-B-4 complete
**Verify:**
```bash
python3 -m pytest tests/integration/test_streak_flow.py -v
```
**Gate:** Session completion increments streak in DB. `/streak` returns real data.

### CP-4: Full Phase 4 Integration
**Trigger:** After all tracks complete
**Verify:**
```bash
python3 -m pytest tests/ -v
bash scripts/validate.sh  # All 7 stages must pass
```
**Gate:** 7 pre-commit stages pass. All integration tests green. Coverage ≥70%.

---

## Skills Gaps (deferred to Phase 5)

The following are explicitly OUT OF SCOPE for Phase 4. They require new skills or agents:

### GAP-1: Claude-Powered Hint Generation (REQ-015, REQ-002, REQ-016)
**What's missing:** `src/services/hint_generator.py` — Claude Haiku API call for dynamic Socratic hints with prompt caching
**Current state:** Hints served from static DB content (problem.get_hints())
**Why deferred:** Requires Anthropic API key configured + claude-api skill + new agent or Jodha extension
**How to create:** Use `/claude-api` skill in Phase 5 to build HintGenerator service
**Skill needed:** `claude-api` (exists in Claude Code skills list)
**File to create:** `src/services/hint_generator.py`

### GAP-2: Daily Streak Reminder Background Task (REQ-011)
**What's missing:** APScheduler job running at 6pm IST daily — checks who hasn't practiced and sends Telegram reminder
**Current state:** No background task scheduler in the project
**Why deferred:** Requires APScheduler integration, Telegram push (not just response), deployment coordination
**Who should own:** Jodha (backend) + Noor (security: don't spam, respect opt-out)
**Skill needed:** A new `scheduler` skill or extend Jodha's skill to include APScheduler patterns

### GAP-3: Centralized Bengali Localization (REQ-021)
**What's missing:** Bilingual strings are currently hardcoded in `webhook.py`. MessageTemplate model exists but nothing uses it.
**Current state:** Ad-hoc f-strings with both languages scattered across files
**Why deferred:** Full localization is a Phase 7 task; Phase 4 adds bilingual strings inline (acceptable for now)
**Who should own:** Jahanara (content) + Jodha (routing)
**Skill needed:** Extend Jahanara's skill to include MessageTemplate database interaction

---

## File Map: New Files This Phase

| File | Owner | Purpose |
|------|-------|---------|
| `src/repositories/streak_repository.py` | Maryam | StreakRepository with upsert + milestone logic |
| `src/services/adaptive_difficulty.py` | Jodha | AdaptiveDifficulty service (REQ-004) |
| `src/services/encouragement.py` | Jahanara | Encouragement + session-start messages (REQ-013, REQ-006) |
| `tests/unit/test_streak_repository.py` | Maryam | Unit tests for streak logic |
| `tests/unit/test_adaptive_difficulty.py` | Jodha | Unit tests for difficulty compute |
| `tests/unit/test_encouragement.py` | Jahanara | Unit tests for message library |
| `tests/integration/test_adaptive_difficulty_flow.py` | Noor | Integration: difficulty → selection → session |
| `tests/integration/test_streak_flow.py` | Noor | Integration: session completion → streak → /streak |

## File Map: Modified Files This Phase

| File | Owner | Change |
|------|-------|--------|
| `src/models/student.py` | Maryam | Add `difficulty_level` column |
| `alembic/versions/xxx_difficulty_level.py` | Maryam | New migration |
| `src/services/problem_selector.py` | Jodha | Accept + apply `difficulty_level` param |
| `src/services/answer_evaluator.py` | Jahanara | Format hints + normalization |
| `src/routes/webhook.py` | Jodha | Wire streak increment + encouragement + topics |
| `src/routes/practice.py` | Jodha | Wire streak increment + difficulty |
| `src/routes/streak.py` | Jodha | Replace stub with real DB call |
| `src/schemas/streak.py` | Jodha | Add next_milestone, days_to_next, last_7_days |

---

## Success Criteria

By end of Phase 4, all of the following must be true:

**REQ-004 (Adaptive Difficulty):**
- [x] Student with `difficulty_level=1` gets ≥60% easy problems in session
- [x] ≥4/5 correct in 2 consecutive sessions → difficulty increases (capped at 3)
- [x] ≤1/5 correct → difficulty decreases (min 1)
- [x] Difficulty clamped to [1, 3]; no 7-day reset in current implementation (simplified from spec)
- [x] `src/services/adaptive_difficulty.py` — `AdaptiveDifficultyService.update_difficulty()`

**REQ-006 (Daily Learning Path):**
- [x] Session start message shows today's topics in student's language (`session_start_message` field in `PracticeResponse`)
- [x] Shows difficulty label (Easy/Medium/Hard) in student's language via `EncouragementService.get_session_start_message()`

**REQ-003 enhancement (Answer Evaluation):**
- [x] Bengali numerals (০-৯) normalized to ASCII before evaluation
- [x] Whitespace stripped in `_normalize_answer()`
- [x] Wrong MC answer → format hint "Please enter A, B, C, or D."
- [x] Wrong numeric answer → format hint "Please write just the number."

**REQ-009 (Streak Tracking):**
- [x] Session completion increments streak in DB (UTC date boundary)
- [x] Streak resets after missed day (gap > 1 day)
- [x] Same-day calls are idempotent

**REQ-010 (Streak Display):**
- [x] `/streak` returns real data from DB (`StreakRepository.get_or_create()`)
- [x] Shows current_streak, longest_streak, last_practice_date, milestones_achieved

**REQ-012 (Streak Milestones):**
- [x] 7-day milestone fires on session completion
- [x] 14-day, 30-day milestones fire correctly
- [x] Milestone not double-counted (list replacement on JSON column)

**REQ-013 (Encouragement):**
- [x] Correct answer includes bilingual encouragement varied by streak (`EncouragementService`)
- [x] Milestone celebration appended to session-complete feedback
- [x] Deterministic variant selection (no randomness — index % pool size)

**Pipeline:**
- [x] All 7 pre-commit stages pass (`bash scripts/validate.sh --fix --skip-slow`)
- [x] 419 tests pass (359 unit + 60 integration), 1 skipped
- [x] Coverage 75% (≥70% maintained)
