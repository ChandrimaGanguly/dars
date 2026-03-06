# Phase 6 Tasks: Engagement Completion — Reminders & UX Polish

**Duration:** Week 5 (3-4 days of agent work across 3 parallel tracks)
**Status:** ⬜ TODO

**Roadmap references:**
- AGENT_ROADMAP.md → Phase 6 (Engagement & Habit Formation)
- REQUIREMENTS.md → REQ-010 (display UX), REQ-011 (reminders), REQ-013 (non-repeat messages)

**Context — What Phase 4 already delivered (do not re-implement):**
- REQ-009: Streak tracking (StreakRepository, record_practice) ✅
- REQ-010: `/streak` REST endpoint with real DB data ✅
- REQ-012: Milestone detection (7/14/30 days) ✅
- REQ-013: EncouragementService with bilingual, streak-aware messages ✅

**Remaining gaps this phase closes:**
- REQ-011: Daily reminder background task (APScheduler) — NOT done
- REQ-010 UX: Telegram `/streak` command formatted as calendar view — NOT done (REST endpoint returns JSON; Telegram bot formats it plainly)
- REQ-013 non-repeat: Messages should not repeat for same student within 7 days — currently deterministic by index only

**Demo target:**
"Student hasn't practiced by 6pm IST — receives a Telegram message: 'Your 5-day streak is at risk! Complete today's practice. 🔥'. Student types `/streak` and sees a proper calendar view with filled/empty circles for the last 7 days and next milestone countdown."

**Pre-conditions (verify before starting):**

- [x] PHASE4 complete — streak tracking, milestones, encouragement all working
- [x] PHASE5 complete — hint system working (Phase 6 doesn't depend on Phase 5 directly)
- [x] `TelegramClient.send_message()` implemented in `src/services/telegram_client.py`
- [x] `StreakRepository.get_last_7_days()` implemented
- [x] `EncouragementService` exists with bilingual messages
- [ ] **GAP:** `apscheduler` not in `pyproject.toml` — must be added (PHASE6-A-1)
- [ ] **GAP:** No daily reminder background task (PHASE6-A-2 closes this)
- [ ] **GAP:** `/streak` Telegram bot command shows raw JSON-like output, not calendar (PHASE6-B-1 closes this)
- [ ] **GAP:** No per-student message tracking to prevent same-week repeats (PHASE6-B-2 closes this)

---

## Task Summary

| Task ID | Task | Owner | Duration | Blocked By | Blocks | Status |
|---------|------|-------|----------|------------|--------|--------|
| PHASE6-A-1 | Add APScheduler to pyproject.toml + app lifecycle | Maryam | 0.5 days | None | PHASE6-A-2 | ⬜ Todo |
| PHASE6-A-2 | Daily reminder job: query + send (REQ-011) | Jodha | 1.5 days | PHASE6-A-1 | PHASE6-C-1 | ⬜ Todo |
| PHASE6-B-1 | `/streak` Telegram command calendar view (REQ-010) | Jodha | 1 day | None | PHASE6-C-2 | ⬜ Todo |
| PHASE6-B-2 | Non-repeat messages: SentMessage model + tracking | Maryam | 1 day | None | PHASE6-C-2 | ⬜ Todo |
| PHASE6-C-1 | Integration tests: reminder flow | Noor | 1 day | PHASE6-A-2 | — | ⬜ Todo |
| PHASE6-C-2 | Integration tests: streak Telegram UX + non-repeat | Noor | 0.5 days | PHASE6-B-1, PHASE6-B-2 | — | ⬜ Todo |
| PHASE6-C-3 | Coverage gate: maintain ≥70% | Noor | ongoing | All | — | ⬜ Todo |

**Parallel tracks:**
```
Track A (Scheduler):  PHASE6-A-1 ──► PHASE6-A-2 ──► PHASE6-C-1
Track B (UX polish):  PHASE6-B-1 ──► PHASE6-C-2
                      PHASE6-B-2 ──►       │
                                           (merge)
```

---

## Track A: Scheduler — Daily Reminders

**Owner:** Jodha (wiring), Maryam (dependency management)
**Duration:** 2 days total

### PHASE6-A-1: Add APScheduler + App Lifecycle

**Requirement:** REQ-011
**Files:** `pyproject.toml`, `src/main.py`, `src/scheduler.py` (new)

1. Add dependency to `pyproject.toml`:
   ```toml
   "apscheduler>=3.10.0",
   ```

2. Create `src/scheduler.py`:
   ```python
   from apscheduler.schedulers.asyncio import AsyncIOScheduler

   scheduler = AsyncIOScheduler(timezone="UTC")

   def start_scheduler() -> None:
       """Register all background jobs and start the scheduler."""
       scheduler.add_job(
           send_daily_reminders,
           trigger="cron",
           hour=12,
           minute=30,   # 12:30 UTC = 18:00 IST
           id="daily_reminders",
           replace_existing=True,
       )
       scheduler.start()

   def stop_scheduler() -> None:
       scheduler.shutdown(wait=False)
   ```

3. Wire into `src/main.py` FastAPI lifespan:
   ```python
   @asynccontextmanager
   async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
       start_scheduler()
       yield
       stop_scheduler()
   ```

**Note:** If `main.py` already has `@app.on_event("startup")`, migrate to `lifespan` context manager (FastAPI recommended pattern).

### PHASE6-A-2: Daily Reminder Job

**Requirement:** REQ-011 (Streak Reminders)
**File:** `src/scheduler.py`

```python
async def send_daily_reminders() -> None:
    """Send Telegram reminders to students who haven't practiced today.

    REQ-011 rules:
    - Run once per day at 6pm IST (12:30pm UTC)
    - Send only if student has NOT completed practice today (UTC date)
    - Personalize by streak length
    - Max 1 reminder per student per day (guard against double-fire)
    - Students with streak=0 get motivational message (not "at risk")
    - Log: reminder_sent, reminder_skipped (already practiced)
    """
```

**Implementation steps:**
1. Open a new async DB session (use `async_sessionmaker` from `src/database.py`)
2. Query all active students (practiced at least once in last 30 days)
3. For each student:
   - Check `streak.last_practice_date` — if already today (UTC), skip
   - Build reminder message via `EncouragementService` or inline message:
     - streak == 0: `"Ready to start your first streak? Complete today's practice! 📚"`
     - streak >= 1: `"Your {streak}-day streak is at risk! Complete today's practice to keep it alive. 🔥"`
   - Send via `TelegramClient.send_message(student.telegram_id, message)`
   - Log: `logger.info("reminder_sent", student_id=..., streak=...)`
4. Handle send failures gracefully (log ERROR, continue to next student)

**Language:** Use `student.language` to select English or Bengali message.

**Bengali reminder example:**
```
আপনার {streak} দিনের ধারা ঝুঁকিতে আছে! আজকের অনুশীলন সম্পন্ন করুন। 🔥
```

---

## Track B: UX Polish

**Owner:** Jodha (B-1), Maryam (B-2)
**Duration:** 2 days total

### PHASE6-B-1: `/streak` Telegram Calendar View

**Requirement:** REQ-010 (Streak Display & Visualization)
**File:** `src/routes/webhook.py`

Find or create `handle_streak_command()` in webhook.py. Currently the Telegram `/streak` command may send raw data or a simple string. Replace with the formatted calendar view from REQ-010:

```
Formatted output (English):

🔥 Current Streak: 12 days
⭐ Longest Streak: 28 days

📅 Last 7 Days:
Mon ●  Tue ●  Wed ●  Thu ●  Fri ●  Sat ○  Sun ●

🎯 Next Milestone: 14 days (2 days away!)
```

```
Formatted output (Bengali):

🔥 বর্তমান ধারা: ১২ দিন
⭐ দীর্ঘতম ধারা: ২৮ দিন

📅 গত ৭ দিন:
সোম ●  মঙ্গল ●  বুধ ●  বৃহ ●  শুক্র ●  শনি ○  রবি ●

🎯 পরবর্তী মাইলস্টোন: ১৪ দিন (২ দিন বাকি!)
```

**Implementation:**
```python
async def _format_streak_message(streak: Streak, last_7_days: list[date], language: str) -> str:
    """Format streak data into Telegram-friendly calendar view."""
    ...
```

**Calendar logic:**
- Get day names for last 7 days (Mon-Sun or বাংলা names)
- For each of the last 7 calendar days: `●` if date in `last_7_days`, else `○`
- Next milestone: first of [7, 14, 30] greater than `current_streak`
- `days_away = next_milestone - current_streak`
- If `current_streak == 0`: show "Start your first streak! Complete today's practice."

**Zero-streak special case (REQ-010):**
```
📚 Start your first streak! Complete today's practice to begin your journey.
```

### PHASE6-B-2: Non-Repeat Message Tracking

**Requirement:** REQ-013 (never repeat same message in a week)
**Files:** `src/models/sent_message.py` (new), Alembic migration

Add a lightweight `SentMessage` model to track which message keys were sent to each student in the last 7 days:

```python
class SentMessage(Base):
    """Track messages sent to students to prevent repetition.

    Keyed on (student_id, message_key) where message_key is a stable
    identifier like "correct_streak_low_0" (message type + variant index).
    Records older than 7 days are ignored (soft TTL via query filter).
    """
    __tablename__ = "sent_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.student_id"), index=True)
    message_key: Mapped[str] = mapped_column(String(100))
    sent_at: Mapped[datetime] = mapped_column(default=func.now())
```

Update `EncouragementService`:
- Add `get_correct_message(..., db: AsyncSession, student_id: int)` variant
- Before returning a message, query `SentMessage` for this student in last 7 days
- Skip variants already sent in that window; cycle to next un-sent variant
- After returning, write `SentMessage` row (caller's responsibility OR service does it)

**Note:** For Phase 0 (50 students), this table will be small. No index needed beyond `student_id`.

**Create Alembic migration:**
```bash
alembic revision --autogenerate -m "Add sent_messages table for non-repeat tracking"
```

---

## Track C: Noor — Tests & Coverage

**Owner:** Noor
**Duration:** 1.5 days

### PHASE6-C-1: Integration Tests — Reminder Flow

**File:** `tests/integration/test_reminder_flow.py`

Tests (use in-memory SQLite, mock `TelegramClient.send_message`):

```
test_reminder_sent_to_student_who_has_not_practiced
  — create student with streak (last_practice_date = yesterday)
  — run send_daily_reminders()
  — TelegramClient.send_message called once with that student's telegram_id

test_no_reminder_to_student_who_practiced_today
  — create student, record_practice(date.today())
  — run send_daily_reminders()
  — TelegramClient.send_message NOT called

test_zero_streak_gets_motivational_not_at_risk_message
  — create student with current_streak=0
  — run send_daily_reminders()
  — message does NOT contain "at risk"

test_reminder_message_matches_student_language
  — student with language="bn"
  — send_daily_reminders()
  — message text is in Bengali (check for Bengali Unicode)

test_telegram_failure_does_not_crash_scheduler
  — mock TelegramClient.send_message raises Exception
  — send_daily_reminders() completes without raising
  — other students still processed
```

### PHASE6-C-2: Integration Tests — Streak UX + Non-Repeat

**File:** `tests/integration/test_streak_ux.py`

```
test_streak_telegram_command_includes_calendar
  — create student with 5-day streak, last_7_days with 2 gaps
  — trigger handle_streak_command (or call _format_streak_message directly)
  — output contains "●" and "○" characters

test_streak_shows_next_milestone
  — student with current_streak=5
  — output contains "7" and "2 days away"

test_streak_zero_shows_start_message
  — student with current_streak=0
  — output contains "first streak" / "প্রথম ধারা"

test_encouragement_non_repeat_within_7_days
  — send same correct-message type to student 6+ times in a row
  — no two consecutive messages are identical key
```

### PHASE6-C-3: Unit Tests — Scheduler Logic

**File:** `tests/unit/test_scheduler.py`

```
test_scheduler_jobs_registered
  — call start_scheduler() (mocked APScheduler)
  — "daily_reminders" job registered with hour=12, minute=30

test_reminder_skips_student_practiced_today
  — unit test: _should_send_reminder(streak) → False when last_practice_date == today

test_reminder_targets_student_who_missed_yesterday
  — _should_send_reminder(streak) → True when last_practice_date < today
```

---

## Integration Checkpoints

### CP-1: Scheduler Starts Without Error
**Trigger:** After PHASE6-A-1 complete
**Verify:**
```bash
python3 -c "from src.scheduler import start_scheduler, stop_scheduler; start_scheduler(); stop_scheduler()"
```
**Gate:** No import or runtime errors.

### CP-2: Reminder Sent to Correct Students
**Trigger:** After PHASE6-A-2 complete
**Verify:**
```bash
python3 -m pytest tests/integration/test_reminder_flow.py -v
```
**Gate:** Students who practiced today receive no reminder. Students who missed do.

### CP-3: `/streak` Calendar View
**Trigger:** After PHASE6-B-1 complete
**Verify:**
```bash
python3 -m pytest tests/integration/test_streak_ux.py -v
```
**Gate:** Formatted output includes ●/○ calendar, milestone countdown, zero-streak special case.

### CP-4: Full Phase 6 Pipeline
**Trigger:** After all tracks complete
**Verify:**
```bash
python3 -m pytest tests/ -v
bash scripts/validate.sh
```
**Gate:** All 7 pre-commit stages pass. Coverage ≥70%.

---

## Skills Gaps (deferred to Phase 7+)

### GAP-1: Opt-Out Preference (REQ-011)
**What's missing:** Student can disable reminders (`/remind off`)
**Current state:** All active students receive reminders
**Why deferred:** Requires preference column on Student and `/remind` command handling
**Phase 1+:** Add `reminders_enabled: bool` to Student; filter in `send_daily_reminders()`

### GAP-2: Reminder Retry on Send Failure (REQ-011)
**What's missing:** "Retry next hour" if Telegram send fails
**Current state:** Log error, continue
**Why deferred:** APScheduler retry logic adds complexity; acceptable for 50-student pilot

---

## File Map: New Files This Phase

| File | Owner | Purpose |
|------|-------|---------|
| `src/scheduler.py` | Jodha/Maryam | APScheduler setup + daily reminder job |
| `src/models/sent_message.py` | Maryam | SentMessage model for non-repeat tracking |
| `alembic/versions/xxx_sent_messages.py` | Maryam | Migration for sent_messages table |
| `tests/unit/test_scheduler.py` | Noor | Scheduler unit tests |
| `tests/integration/test_reminder_flow.py` | Noor | Reminder integration tests |
| `tests/integration/test_streak_ux.py` | Noor | Streak Telegram UX tests |

## File Map: Modified Files This Phase

| File | Owner | Change |
|------|-------|--------|
| `pyproject.toml` | Maryam | Add `apscheduler>=3.10.0` |
| `src/main.py` | Jodha | Wire scheduler start/stop via lifespan |
| `src/routes/webhook.py` | Jodha | `/streak` command → formatted calendar view |
| `src/services/encouragement.py` | Jodha | Non-repeat tracking via SentMessage |

---

## Success Criteria

By end of Phase 6, all of the following must be true:

**REQ-011 (Streak Reminders):**
- [ ] Scheduler fires daily at 12:30 UTC (6pm IST)
- [ ] Students who have NOT practiced today receive a reminder
- [ ] Students who HAVE practiced receive no reminder
- [ ] streak=0 students get motivational message, not "at risk" message
- [ ] Message uses student's language preference (en/bn)
- [ ] Send failures logged, do not crash scheduler

**REQ-010 (Streak Display UX):**
- [ ] Telegram `/streak` command shows calendar view (●/○ for last 7 days)
- [ ] Shows "Next milestone: X days (Y days away!)"
- [ ] Zero-streak shows "Start your first streak!" message
- [ ] Both languages display correctly

**REQ-013 (Non-Repeat Messages):**
- [ ] Same encouragement message key not sent twice in 7 days to same student
- [ ] SentMessage rows written after each encouragement sent
- [ ] Old rows (>7 days) ignored without deletion

**Pipeline:**
- [ ] All 7 pre-commit stages pass
- [ ] All new tests pass
- [ ] Coverage ≥70% maintained
