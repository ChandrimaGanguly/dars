# Phase 7 Tasks: Localization & Operations Monitoring

**Duration:** Week 5-6 (6-7 days of agent work across 4 parallel tracks)
**Status:** ⬜ TODO

**Roadmap references:**
- AGENT_ROADMAP.md → Phase 7 (Localization & Operations Monitoring)
- REQUIREMENTS.md → REQ-021, REQ-029, REQ-030, REQ-020

**Demo target:**
"Admin types `/admin stats` in Telegram (or hits GET /admin/stats) and sees real numbers: 48 students, 31 active this week, avg streak 4.2 days, $0.08/student cost. Student types `/language` and switches to Bengali — all subsequent messages arrive in Bengali. GET /admin/cost shows per-student cost breakdown with a budget alert flag if any student exceeds $0.10/month."

**Pre-conditions (verify before starting):**

- [x] PHASE5 complete — real Claude costs flowing into CostRecord table
- [x] PHASE6 complete — reminders, streak UX, non-repeat messages done
- [x] `src/routes/admin.py` exists — all 3 admin endpoints are stubs (TODO comments)
- [x] `src/models/cost_record.py` exists — `CostRecord` table populated from Phase 5
- [x] `src/models/message_template.py` exists — bilingual template model (unused)
- [x] `PATCH /student/profile` endpoint exists in `src/routes/student.py`
- [x] `student.language` column exists and is used by EncouragementService
- [ ] **GAP:** `/admin/stats`, `/admin/students`, `/admin/cost` return stub data (B-1, B-2, B-3 close this)
- [ ] **GAP:** No `/language` Telegram command — students cannot switch language interactively (A-1 closes this)
- [ ] **GAP:** Webhook.py hardcoded strings not routed through bilingual lookup (A-2 closes this)
- [ ] **GAP:** No cost alert in admin response or logs (C-1 closes this)
- [ ] **GAP:** No request-ID correlation in logs (C-2 closes this)

---

## Task Summary

| Task ID | Task | Owner | Duration | Blocked By | Blocks | Status |
|---------|------|-------|----------|------------|--------|--------|
| PHASE7-A-1 | `/language` Telegram command + profile update | Jahanara | 1 day | None | PHASE7-A-2, PHASE7-C-3 | ⬜ Todo |
| PHASE7-A-2 | Centralize webhook.py strings — bilingual routing | Jahanara | 1.5 days | PHASE7-A-1 | PHASE7-C-3 | ⬜ Todo |
| PHASE7-B-1 | Real GET /admin/stats — DB queries | Jodha | 1 day | None | PHASE7-C-2 | ⬜ Todo |
| PHASE7-B-2 | Real GET /admin/students — paginated list | Jodha | 0.5 days | None | PHASE7-C-2 | ⬜ Todo |
| PHASE7-B-3 | Real GET /admin/cost — cost breakdown + alert | Jodha | 1 day | None | PHASE7-C-1, PHASE7-C-2 | ⬜ Todo |
| PHASE7-C-1 | Cost alert system (budget threshold logging) | Noor | 0.5 days | PHASE7-B-3 | — | ⬜ Todo |
| PHASE7-C-2 | Integration tests: admin endpoints (real data) | Noor | 1 day | PHASE7-B-1, PHASE7-B-2, PHASE7-B-3 | — | ⬜ Todo |
| PHASE7-C-3 | Integration tests: language switch flow | Noor | 0.5 days | PHASE7-A-2 | — | ⬜ Todo |
| PHASE7-C-4 | Request-ID middleware + slow-query logging | Noor | 0.5 days | None | — | ⬜ Todo |
| PHASE7-C-5 | Coverage gate: maintain ≥70% | Noor | ongoing | All | — | ⬜ Todo |

**Parallel tracks:**
```
Track A (Localization): PHASE7-A-1 ──► PHASE7-A-2 ──► PHASE7-C-3

Track B (Admin ops):    PHASE7-B-1 ──┐
                        PHASE7-B-2 ──┤──► PHASE7-C-2
                        PHASE7-B-3 ──┘
                             │
                             ▼
                        PHASE7-C-1

Track C (Observability): PHASE7-C-4 (independent)
```

---

## Track A: Jahanara — Localization

**Owner:** Jahanara
**Duration:** 2.5 days
**Start condition:** No blockers — can start immediately

### PHASE7-A-1: `/language` Telegram Command

**Requirement:** REQ-021 (language preference)
**File:** `src/routes/webhook.py`

Add `handle_language_command()` to the webhook handler:

```
/language command flow:
1. Student sends "/language"
2. Bot replies: "Choose your language / আপনার ভাষা বেছে নিন:\n1. English\n2. বাংলা"
3. Student replies "1" or "2" (or "en"/"bn")
4. Bot calls PATCH /student/profile with {"language": "en" | "bn"}
5. Bot confirms in the NEW language:
   - en: "Language set to English! All future messages will be in English."
   - bn: "ভাষা বাংলায় সেট হয়েছে! সব ভবিষ্যৎ বার্তা বাংলায় আসবে।"
```

**Implementation notes:**
- Use the existing in-memory `_active_sessions` dict OR a separate `_pending_language_choice: dict[int, bool]` to track state between messages
- PATCH /student/profile must already accept `language` field — verify `src/routes/student.py`
- After update: `await db.refresh(student)` to confirm change persisted
- Validate input: only "1", "2", "en", "bn" accepted; invalid input re-prompts once

**Add `/language` to the bot's command list in `handle_start_command()` help text.**

### PHASE7-A-2: Centralize Webhook String Routing

**Requirement:** REQ-021 (all messages in student's language)
**File:** `src/routes/webhook.py`, new `src/services/messages.py`

**Audit** all hardcoded strings in `webhook.py` and categorize:

| String location | Current state | Target |
|----------------|---------------|--------|
| `/start` welcome | Hardcoded English | Bilingual |
| `/practice` session start | Uses EncouragementService | Already bilingual |
| Answer correct feedback | Uses EncouragementService | Already bilingual |
| Answer incorrect feedback | Uses EncouragementService | Already bilingual |
| Session complete message | Partial (milestone message bilingual, score not) | Fully bilingual |
| Hint responses | Uses HintGenerator (Phase 5) | Already bilingual |
| Error messages ("Something went wrong") | Hardcoded English | Bilingual |
| "No active session" response | Hardcoded English | Bilingual |
| "Already completed today" | Hardcoded English | Bilingual |
| `/streak` reminder | Phase 6 — already bilingual | Already bilingual |

Create `src/services/messages.py` — centralized bilingual message lookup:

```python
"""Centralized bilingual message strings for Telegram bot responses.

Strings are keyed by MessageKey enum. All student-facing strings
that are not already handled by EncouragementService live here.
"""

class MessageKey(str, Enum):
    WELCOME = "welcome"
    HELP = "help"
    SESSION_COMPLETE_SCORE = "session_complete_score"   # "You got {correct}/5!"
    NO_ACTIVE_SESSION = "no_active_session"
    ALREADY_COMPLETED = "already_completed"
    UNKNOWN_COMMAND = "unknown_command"
    ERROR_GENERIC = "error_generic"
    LANGUAGE_PROMPT = "language_prompt"
    LANGUAGE_CONFIRMED_EN = "language_confirmed_en"
    LANGUAGE_CONFIRMED_BN = "language_confirmed_bn"
    REGISTER_FIRST = "register_first"

MESSAGES: dict[str, dict[str, str]] = {
    MessageKey.WELCOME: {
        "en": "Welcome to Dars! I'm your AI math tutor. Send /practice to start.",
        "bn": "Dars-এ স্বাগতম! আমি তোমার গণিত শিক্ষক। /practice পাঠান শুরু করতে।",
    },
    MessageKey.SESSION_COMPLETE_SCORE: {
        "en": "Session complete! You got {correct}/5 correct. {emoji}",
        "bn": "সেশন শেষ! তুমি ৫টির মধ্যে {correct}টি সঠিক করেছ। {emoji}",
    },
    # ... etc
}

def get_message(key: MessageKey, language: str, **kwargs: str | int) -> str:
    """Return message in requested language, falling back to English."""
    lang = language if language in ("en", "bn") else "en"
    template = MESSAGES.get(key, {}).get(lang, MESSAGES.get(key, {}).get("en", str(key)))
    return template.format(**kwargs) if kwargs else template
```

Replace all identified hardcoded strings in `webhook.py` with `get_message(key, student.language)` calls.

**IMPORTANT:** Read `webhook.py` fully before editing. Make targeted replacements only — do not restructure the file.

---

## Track B: Jodha — Real Admin Endpoints

**Owner:** Jodha
**Duration:** 2.5 days
**Start condition:** No blockers — all three tasks are independent

### PHASE7-B-1: Real GET /admin/stats

**Requirement:** REQ-030 (Admin Commands)
**File:** `src/routes/admin.py`

Replace the TODO stub. Required DB queries:

```python
@router.get("/admin/stats", response_model=AdminStats)
async def get_admin_stats(
    admin_id: int = Depends(verify_admin),
    db: AsyncSession = Depends(get_session),
) -> AdminStats:
```

Queries to implement:
```python
# Total students
total_students = await db.scalar(select(func.count(Student.student_id)))

# Active this week (at least 1 session in last 7 days)
week_ago = datetime.now(UTC) - timedelta(days=7)
active_week = await db.scalar(
    select(func.count(func.distinct(Session.student_id)))
    .where(Session.completed_at >= week_ago)
)

# Average current streak
avg_streak = await db.scalar(select(func.avg(Streak.current_streak)))

# Total sessions this week
sessions_week = await db.scalar(
    select(func.count(Session.session_id))
    .where(Session.completed_at >= week_ago)
)

# Week-to-date cost
week_cost = await db.scalar(
    select(func.sum(CostRecord.cost_usd))
    .where(CostRecord.created_at >= week_ago)
) or 0.0
```

Update `src/schemas/admin.py` `AdminStats` schema to include all returned fields.

### PHASE7-B-2: Real GET /admin/students

**Requirement:** REQ-030
**File:** `src/routes/admin.py`

Replace the TODO stub:

```python
@router.get("/admin/students", response_model=StudentListResponse)
async def list_students(
    admin_id: int = Depends(verify_admin),
    db: AsyncSession = Depends(get_session),
    grade: int | None = Query(None, ge=6, le=8),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> StudentListResponse:
```

Return per-student: `student_id`, `name`, `grade`, `language`, `current_streak`, `longest_streak`, `last_practice_date`, `total_sessions`.

Join `Student` → `Streak` (left outer join, streak may not exist). Paginate with `offset((page-1) * page_size).limit(page_size)`.

### PHASE7-B-3: Real GET /admin/cost

**Requirement:** REQ-029 (Cost Tracking & Monitoring)
**File:** `src/routes/admin.py`

Replace the TODO stub:

```python
@router.get("/admin/cost", response_model=CostSummary)
async def get_cost_summary(
    admin_id: int = Depends(verify_admin),
    db: AsyncSession = Depends(get_session),
    period: str = Query("week", pattern="^(day|week|month)$"),
) -> CostSummary:
```

Compute for requested period:
- `total_cost_usd`: sum of all CostRecord.cost_usd in period
- `ai_hint_count`: count of is_ai_generated=True rows
- `per_student_avg_usd`: total_cost / active_student_count (avoid division by zero)
- `daily_avg_usd`: total_cost / days_in_period
- `projected_monthly_usd`: daily_avg * 30
- `budget_alert`: True if `per_student_avg_usd * 30 > BUDGET_PER_STUDENT_USD` (from cost_tracker.py)
- `cache_hit_count` / `cache_miss_count`: counts from CostRecord where is_ai_generated=False vs True (approximation)

Update `src/schemas/admin.py` `CostSummary` schema to include all new fields.

---

## Track C: Noor — Tests & Observability

**Owner:** Noor
**Duration:** 2.5 days

### PHASE7-C-1: Cost Alert System

**Requirement:** REQ-029
**File:** `src/services/cost_tracker.py`, `src/routes/admin.py`

When `record_hint_cost()` is called and the student's month-to-date cost would exceed `BUDGET_PER_STUDENT_USD`:

```python
if mtd_cost + this_call_cost > BUDGET_PER_STUDENT_USD:
    logger.warning(
        "cost_budget_exceeded",
        extra={
            "student_id": student_id,   # Internal service: student_id OK, not hashed
            "mtd_cost_usd": round(mtd_cost, 4),
            "budget_usd": BUDGET_PER_STUDENT_USD,
        },
    )
```

Also expose in `GET /admin/cost` response: `budget_alert: bool` field flags if ANY student has exceeded their monthly budget in the current period.

### PHASE7-C-4: Request-ID Middleware + Slow-Query Logging

**Requirement:** REQ-020 (enhanced logging)
**File:** `src/main.py` (middleware), `src/database.py`

1. Add request-ID middleware to FastAPI:
   ```python
   @app.middleware("http")
   async def request_id_middleware(request: Request, call_next: Callable) -> Response:
       request_id = request.headers.get("X-Request-ID", str(uuid4()))
       # Store in context var for structured logging
       response = await call_next(request)
       response.headers["X-Request-ID"] = request_id
       return response
   ```

2. Add slow-query warning in DB session: log `WARNING` if any `await db.execute()` takes >200ms.
   - Simplest approach: time the `await db.commit()` calls in repositories (not individual queries)
   - Log: `logger.warning("slow_db_operation", duration_ms=..., operation=...)`

### PHASE7-C-2: Integration Tests — Admin Endpoints

**File:** `tests/integration/test_admin_endpoints.py`

Tests (use `db_session` conftest fixture, seed real data):

```
test_admin_stats_returns_correct_student_count
  — seed 5 students
  — GET /admin/stats → total_students == 5

test_admin_stats_active_week_counts_only_recent_sessions
  — seed student with session 10 days ago + session today
  — active_week == 1 (only today's)

test_admin_students_paginates_correctly
  — seed 25 students
  — GET /admin/students?page=1&page_size=10 → 10 results
  — GET /admin/students?page=3&page_size=10 → 5 results

test_admin_students_filters_by_grade
  — seed 5 grade-7 + 3 grade-8 students
  — GET /admin/students?grade=7 → 5 results

test_admin_cost_calculates_real_cost
  — seed 3 CostRecord rows with cost_usd=0.01 each
  — GET /admin/cost?period=week → total_cost_usd == 0.03

test_admin_cost_budget_alert_fires
  — seed student with monthly cost > BUDGET_PER_STUDENT_USD
  — GET /admin/cost → budget_alert == True

test_admin_cost_no_alert_under_budget
  — seed student with small cost
  — GET /admin/cost → budget_alert == False

test_admin_requires_auth
  — GET /admin/stats without X-Admin-ID header → 401
  — GET /admin/stats with invalid admin ID → 403
```

### PHASE7-C-3: Integration Tests — Language Switch

**File:** `tests/integration/test_language_switch.py`

```
test_language_command_updates_student_profile
  — simulate /language → "2" message sequence
  — db.refresh(student) → student.language == "bn"

test_language_confirmed_message_in_new_language
  — switch to Bengali
  — confirmation message contains Bengali text (Unicode check)

test_subsequent_messages_use_new_language
  — switch student to Bengali
  — trigger any webhook message
  — response text is in Bengali
  — (check for Bengali Unicode chars ব-য range)

test_language_invalid_input_reprompts
  — /language → "xyz" (invalid)
  — response re-prompts language selection
  — student.language unchanged
```

---

## Integration Checkpoints

### CP-1: Admin Stats Return Real Data
**Trigger:** After PHASE7-B-1 complete
**Verify:**
```bash
python3 -m pytest tests/integration/test_admin_endpoints.py::test_admin_stats_returns_correct_student_count -v
```
**Gate:** No stub data. Real DB query returns seeded count.

### CP-2: Admin Cost Shows Real Costs + Alert
**Trigger:** After PHASE7-B-3 + PHASE7-C-1 complete
**Verify:**
```bash
python3 -m pytest tests/integration/test_admin_endpoints.py -v -k "cost"
```
**Gate:** `total_cost_usd` matches sum of CostRecord rows. `budget_alert` fires correctly.

### CP-3: Language Switch Works End-to-End
**Trigger:** After PHASE7-A-2 complete
**Verify:**
```bash
python3 -m pytest tests/integration/test_language_switch.py -v
```
**Gate:** Language saved to DB. All subsequent messages in new language.

### CP-4: Full Phase 7 Pipeline
**Trigger:** After all tracks complete
**Verify:**
```bash
python3 -m pytest tests/ -v
bash scripts/validate.sh
```
**Gate:** All 7 pre-commit stages pass. Coverage ≥70%. No MyPy errors.

---

## Skills Gaps (deferred to Phase 8)

### GAP-1: Weekly Cost Report Email/Telegram to Admin (REQ-029)
**What's missing:** Automated weekly cost report pushed to admin Telegram or email
**Current state:** Admin can query GET /admin/cost manually
**Why deferred:** Requires APScheduler job (Phase 6 adds this) and admin Telegram push
**Phase 8:** Add APScheduler weekly job that calls `send_admin_weekly_report()`

### GAP-2: Native Bengali Speaker Review (REQ-021)
**What's missing:** Human review of Bengali strings in `messages.py` and `encouragement.py`
**Current state:** Machine-generated Bengali (Unicode correct but idiomatic quality unknown)
**Why deferred:** Requires human; out of scope for automated implementation
**Action required:** Schedule with project coordinator before Phase 8 launch

### GAP-3: MessageTemplate DB Table (REQ-021)
**What's missing:** `MessageTemplate` model exists but unused; strings are in code
**Current state:** `src/services/messages.py` (new) holds strings in Python dict
**Why deferred:** DB-backed strings add complexity; code dict is sufficient for Phase 0
**Phase 1+:** Migrate `MESSAGES` dict to `MessageTemplate` rows for runtime editing

---

## File Map: New Files This Phase

| File | Owner | Purpose |
|------|-------|---------|
| `src/services/messages.py` | Jahanara | Centralized bilingual message lookup |
| `tests/integration/test_admin_endpoints.py` | Noor | Admin endpoint integration tests |
| `tests/integration/test_language_switch.py` | Noor | Language switch integration tests |

## File Map: Modified Files This Phase

| File | Owner | Change |
|------|-------|--------|
| `src/routes/admin.py` | Jodha | Replace all 3 TODO stubs with real DB queries |
| `src/routes/webhook.py` | Jahanara | Add `/language` command; route strings through messages.py |
| `src/schemas/admin.py` | Jodha | Add new fields to AdminStats, CostSummary |
| `src/services/cost_tracker.py` | Noor | Budget alert logging |
| `src/main.py` | Noor | Request-ID middleware, slow-query warning |

---

## Success Criteria

By end of Phase 7, all of the following must be true:

**REQ-021 (Bengali Language Support):**
- [ ] `/language` command works — student can switch en↔bn interactively
- [ ] All webhook.py user-facing strings routed through `messages.py` or `EncouragementService`
- [ ] Language change persists to DB via PATCH /student/profile
- [ ] Subsequent messages after language change use new language

**REQ-029 (Cost Tracking & Monitoring):**
- [ ] GET /admin/cost returns real aggregated data from CostRecord table
- [ ] `budget_alert: True` when any student projected > $0.10/month
- [ ] Budget warning logged in cost_tracker.py when threshold crossed
- [ ] `period` parameter (day/week/month) filters correctly

**REQ-030 (Admin Commands):**
- [ ] GET /admin/stats returns real student count, active-week count, avg streak
- [ ] GET /admin/students returns paginated list with streak data; grade filter works
- [ ] GET /admin/cost returns per-period cost breakdown
- [ ] All admin endpoints still require auth (no regression)

**REQ-020 (Enhanced Logging):**
- [ ] X-Request-ID header propagated on all responses
- [ ] Slow DB operations (>200ms) logged at WARNING
- [ ] No PII in logs (student_id OK in internal services; telegram_id hashed at boundary)

**Pipeline:**
- [ ] All 7 pre-commit stages pass
- [ ] All new tests pass
- [ ] Coverage ≥70% maintained
