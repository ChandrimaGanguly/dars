# Dars Implementation Tasks

> **Goal:** Build a Telegram-based AI tutoring bot for Phase 0 pilot (50 students, 8 weeks, Grade 7 Math, Kolkata)
>
> **Constraint:** $0.10/student/month cost ceiling
>
> **Timeline:** 2 weeks to MVP, then 8-week pilot

---

## Phase 1: Foundation

Infrastructure and project setup. No user-facing features yet.

- [ ] TASK-001: Initialize Python project with FastAPI
  - Create project structure: `src/`, `tests/`, `scripts/`
  - Set up Poetry or pip with `pyproject.toml`
  - Dependencies: `fastapi`, `uvicorn`, `python-telegram-bot`, `anthropic`, `sqlalchemy`, `asyncpg`, `alembic`
  - Create `.env.example` with required variables
  - **Output:** `python -m pytest` runs (even with no tests)

- [ ] TASK-002: Set up PostgreSQL database schema
  - Design tables: `students`, `sessions`, `problems`, `responses`, `streaks`
  - Create Alembic migration for initial schema
  - Add indexes for common queries (student lookups, daily practice)
  - **Output:** `alembic upgrade head` succeeds

- [ ] TASK-003: Create Telegram bot via BotFather
  - Register bot with @BotFather
  - Get bot token
  - Configure bot name: "Dars" with Bengali description
  - Set bot commands: `/start`, `/practice`, `/streak`, `/help`
  - Store token in `.env`
  - **Output:** Bot visible in Telegram search

- [ ] TASK-004: Implement basic Telegram webhook handler
  - Set up FastAPI route for Telegram webhook (`/webhook`)
  - Implement webhook verification
  - Parse incoming messages
  - Return 200 OK for all messages (echo test)
  - **Output:** Send message to bot, see log in console

- [ ] TASK-005: Create core data models (SQLAlchemy)
  - `Student`: telegram_id, name, grade, language, created_at
  - `Problem`: id, grade, topic, question_text, correct_answer, hints[], difficulty
  - `Session`: student_id, date, problems_attempted, problems_correct, completed
  - `Response`: session_id, problem_id, student_answer, is_correct, hints_used, timestamp
  - `Streak`: student_id, current_streak, longest_streak, last_practice_date
  - **Output:** Models importable, create test records

---

## Phase 2: Student Onboarding

First user-facing feature: students can start using the bot.

- [ ] TASK-006: Implement `/start` command flow
  - Detect new vs returning student
  - For new: Welcome message in Bengali, ask for name
  - Store student in database
  - Confirm registration with personalized greeting
  - **Output:** New user can register via `/start`

- [ ] TASK-007: Implement grade selection flow
  - After name, ask for grade (6, 7, 8) using inline keyboard
  - Store grade preference
  - Confirm selection
  - **Output:** Student grade stored in DB

- [ ] TASK-008: Implement language preference (Bengali/English)
  - Offer language choice via inline keyboard
  - Store preference
  - All subsequent messages respect language choice
  - Default to Bengali
  - **Output:** Messages appear in selected language

- [ ] TASK-009: Create message templates system
  - Create `templates/` directory with Bengali and English messages
  - Key messages: welcome, daily_practice_start, correct_answer, wrong_answer, hint, streak_update, encouragement
  - Load templates at startup
  - **Output:** All user-facing strings externalized

---

## Phase 3: Content System

Math problems and curriculum alignment.

- [ ] TASK-010: Design problem content schema
  - JSON/YAML format for problems
  - Fields: id, grade, topic, subtopic, question_bn, question_en, answer, answer_type (numeric/choice), hints_bn[], hints_en[], difficulty (1-3)
  - Support for variables (randomized numbers)
  - **Output:** Schema documented, 5 sample problems created

- [ ] TASK-011: Curate Week 1 math content (Grade 7, WBBSE)
  - Topics: Number System, Profit & Loss basics
  - 35 problems (5/day × 7 days)
  - 3 difficulty levels per topic
  - Bengali translations
  - 2-3 hints per problem
  - **Output:** `content/week1.yaml` with 35 problems

- [ ] TASK-012: Implement problem loader and selector
  - Load problems from YAML files
  - Select 5 problems for daily practice based on:
    - Student's grade
    - Topics not recently practiced
    - Adaptive difficulty (start easy, increase on success)
  - Randomize variable values in problems
  - **Output:** Given student_id, return 5 problems for today

- [ ] TASK-013: Create problem display formatter
  - Format problem for Telegram (markdown)
  - Support inline keyboard for multiple choice
  - Support text input for numeric answers
  - Handle Bengali text rendering
  - **Output:** Problems display correctly in Telegram

---

## Phase 4: AI Integration

Claude API for Socratic hints and personalized feedback.

- [ ] TASK-014: Set up Anthropic client wrapper
  - Initialize Claude client with API key
  - Create async wrapper for API calls
  - Implement retry logic with exponential backoff
  - Add request/response logging for debugging
  - **Output:** Can call Claude API from codebase

- [ ] TASK-015: Create Socratic hint generator
  - Prompt template for generating hints
  - Input: problem, student_answer, hint_number (1-3)
  - Output: Hint that guides without giving answer
  - Use Claude Haiku for cost efficiency
  - **Output:** Given wrong answer, get helpful hint

- [ ] TASK-016: Implement response evaluator
  - For numeric answers: exact match or within tolerance
  - For text answers: Claude evaluation
  - Return: is_correct, feedback_message
  - Handle edge cases (typos, units, etc.)
  - **Output:** Student answers evaluated correctly

- [ ] TASK-017: Implement prompt caching layer
  - Cache common hint patterns by problem_id
  - Cache structure: Redis or in-memory dict (for MVP)
  - TTL: 24 hours
  - Track cache hit rate for cost monitoring
  - **Output:** Repeated hints served from cache

- [ ] TASK-018: Add encouragement message generator
  - Personalized encouragement after correct answer
  - Vary messages to avoid repetition
  - Include streak mention if applicable
  - Bengali and English variants
  - **Output:** Students receive varied positive feedback

---

## Phase 5: Daily Practice Flow

The core learning loop.

- [ ] TASK-019: Implement `/practice` command
  - Check if student completed today's practice
  - If yes: show summary, encourage tomorrow
  - If no: start practice session
  - Create session record in DB
  - **Output:** `/practice` starts or resumes daily session

- [ ] TASK-020: Build practice session state machine
  - States: AWAITING_ANSWER, SHOWING_HINT, SESSION_COMPLETE
  - Track current problem index (1-5)
  - Handle: correct answer, wrong answer, hint request, skip
  - Persist state for session continuity
  - **Output:** Multi-turn practice conversation works

- [ ] TASK-021: Implement answer submission handling
  - Parse student's text response
  - Evaluate correctness
  - If correct: celebrate, move to next problem
  - If wrong (attempt 1): offer hint
  - If wrong (attempt 2): show another hint
  - If wrong (attempt 3): show answer, explain, move on
  - Record all attempts in `responses` table
  - **Output:** Full answer flow works

- [ ] TASK-022: Implement hint request handling
  - Student can request hint via button or "hint" message
  - Fetch/generate appropriate hint
  - Track hints_used in response record
  - Max 3 hints per problem
  - **Output:** Hints delivered on request

- [ ] TASK-023: Build session completion summary
  - Show score: "You got 4/5 correct!"
  - Highlight improvement areas
  - Update streak
  - Show streak status
  - Encourage next practice
  - **Output:** Session ends with summary

---

## Phase 6: Gamification (Streaks)

Habit formation through streaks.

- [ ] TASK-024: Implement streak tracking logic
  - On session complete: update streak
  - If practiced yesterday: increment current_streak
  - If missed a day: reset to 1
  - Update longest_streak if current > longest
  - **Output:** Streaks calculated correctly

- [ ] TASK-025: Implement `/streak` command
  - Show current streak with emoji (🔥)
  - Show longest streak
  - Show calendar view of last 7 days
  - Motivational message based on streak length
  - **Output:** Students can check their streak

- [ ] TASK-026: Add streak reminders
  - Check students who haven't practiced today
  - Send reminder at configured time (e.g., 6 PM)
  - Personalized message mentioning streak at risk
  - Respect a daily reminder limit (1 per day)
  - **Output:** Students get reminded to practice

- [ ] TASK-027: Implement streak milestones
  - Celebrate 7-day, 14-day, 30-day streaks
  - Special messages and emoji badges
  - Store milestone achievements
  - **Output:** Milestone celebrations trigger

---

## Phase 7: Deployment & Operations

Get it running in production.

- [ ] TASK-028: Set up Railway/Render deployment
  - Create project on Railway or Render
  - Configure build command
  - Set environment variables
  - Configure PostgreSQL add-on
  - **Output:** App deploys on git push

- [ ] TASK-029: Configure Telegram webhook for production
  - Set webhook URL to production endpoint
  - Verify webhook is receiving messages
  - Handle webhook errors gracefully
  - **Output:** Bot responds in production

- [ ] TASK-030: Implement health check endpoint
  - `/health` returns 200 if services OK
  - Check DB connection
  - Check Claude API reachability
  - **Output:** Health check passes

- [ ] TASK-031: Add logging and error tracking
  - Structured logging (JSON format)
  - Log all API calls with timing
  - Log errors with stack traces
  - Consider Sentry for error tracking (free tier)
  - **Output:** Errors visible in logs

- [ ] TASK-032: Implement cost tracking dashboard
  - Track Claude API calls per student
  - Calculate daily/weekly/monthly costs
  - Alert if approaching budget
  - Simple admin endpoint to view stats
  - **Output:** Know exactly what we're spending

---

## Phase 8: Content Expansion & Pilot Prep

Prepare for 8-week pilot with 50 students.

- [ ] TASK-033: Curate Weeks 2-4 math content
  - Topics: Fractions, Decimals, Percentages, Geometry basics
  - 35 problems per week (140 total)
  - Bengali translations
  - Progressive difficulty
  - **Output:** `content/week2-4.yaml` complete

- [ ] TASK-034: Curate Weeks 5-8 math content
  - Topics: Algebra intro, Ratio & Proportion, Data Handling, Mixed review
  - 140 more problems
  - Include review/reinforcement problems
  - **Output:** `content/week5-8.yaml` complete

- [ ] TASK-035: Create student onboarding guide
  - Step-by-step Telegram installation (for those who need it)
  - How to find and start Dars bot
  - Screenshots in Bengali
  - PDF and image formats
  - **Output:** Shareable onboarding guide

- [ ] TASK-036: Create teacher briefing materials
  - What is Dars, how it works
  - What students will experience
  - How to support students
  - FAQ
  - **Output:** Teacher one-pager ready

- [ ] TASK-037: Set up pilot tracking spreadsheet
  - Student list with Telegram usernames
  - Daily engagement tracking
  - Streak tracking
  - Notes field for observations
  - **Output:** Tracking sheet ready for Day 1

- [ ] TASK-038: Implement admin commands
  - `/admin stats` - show engagement metrics
  - `/admin students` - list active students
  - `/admin cost` - show AI cost summary
  - Restrict to admin Telegram IDs
  - **Output:** Can monitor pilot from Telegram

---

## Phase 9: Testing & Polish

Quality assurance before pilot launch.

- [ ] TASK-039: Write unit tests for core logic
  - Streak calculation tests
  - Problem selection tests
  - Answer evaluation tests
  - Session state machine tests
  - **Output:** `pytest` passes with >80% coverage on core

- [ ] TASK-040: End-to-end testing with test accounts
  - Create 3 test student accounts
  - Complete full onboarding flow
  - Complete 3 days of practice
  - Verify streaks work
  - Test edge cases (midnight, timezone)
  - **Output:** E2E test checklist passes

- [ ] TASK-041: Bengali language QA
  - Native speaker reviews all Bengali text
  - Check for awkward translations
  - Verify math terminology is correct
  - Fix any issues found
  - **Output:** Bengali content approved

- [ ] TASK-042: Load testing
  - Simulate 50 concurrent students
  - Verify response times <2 seconds
  - Check database performance
  - Verify no rate limiting issues
  - **Output:** System handles expected load

- [ ] TASK-043: Create runbook for common issues
  - Bot not responding
  - Database connection issues
  - Claude API errors
  - How to restart services
  - **Output:** Operations runbook documented

---

## Definition of Done (MVP)

MVP is complete when:

- [ ] Student can register via `/start`
- [ ] Student can complete daily 5-question practice
- [ ] Socratic hints work when student is stuck
- [ ] Streaks are tracked and displayed
- [ ] Bot responds in Bengali
- [ ] Content covers Week 1 (35 problems)
- [ ] Deployed to production
- [ ] Cost tracking in place
- [ ] 3 test students have completed 3+ days

---

## Dependency Graph

```
TASK-001 (project setup)
    └── TASK-002 (database)
        └── TASK-005 (models)
            ├── TASK-006 (onboarding)
            │   └── TASK-007 (grade selection)
            │       └── TASK-008 (language)
            └── TASK-010 (content schema)
                └── TASK-011 (week 1 content)
                    └── TASK-012 (problem selector)

TASK-003 (create bot)
    └── TASK-004 (webhook)
        └── TASK-006 (onboarding)

TASK-014 (Claude client)
    └── TASK-015 (hint generator)
        └── TASK-017 (caching)
    └── TASK-016 (answer evaluator)

TASK-009 (templates)
    └── TASK-018 (encouragement)

TASK-012 + TASK-016 + TASK-015
    └── TASK-019 (practice command)
        └── TASK-020 (state machine)
            └── TASK-021 (answer handling)
            └── TASK-022 (hint handling)
            └── TASK-023 (session summary)

TASK-023
    └── TASK-024 (streak tracking)
        └── TASK-025 (streak command)
        └── TASK-026 (reminders)
        └── TASK-027 (milestones)

TASK-028 (deployment)
    └── TASK-029 (webhook prod)
    └── TASK-030 (health check)
    └── TASK-031 (logging)
    └── TASK-032 (cost tracking)

All MVP tasks
    └── TASK-039-043 (testing & polish)
```

---

## Estimated Effort

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1: Foundation | 5 tasks | 1 day |
| Phase 2: Onboarding | 4 tasks | 0.5 day |
| Phase 3: Content | 4 tasks | 1 day |
| Phase 4: AI Integration | 5 tasks | 1 day |
| Phase 5: Daily Practice | 5 tasks | 1.5 days |
| Phase 6: Gamification | 4 tasks | 0.5 day |
| Phase 7: Deployment | 5 tasks | 0.5 day |
| Phase 8: Content & Prep | 6 tasks | 2 days |
| Phase 9: Testing | 5 tasks | 1 day |
| **Total** | **43 tasks** | **~9 days** |

Buffer for unknowns: +3 days → **12 days to pilot-ready**
