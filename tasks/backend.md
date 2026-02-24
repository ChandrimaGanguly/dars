# Backend Tasks

> FastAPI server, database, Claude API integration, core business logic

## Active

### Phase 1: Foundation

- [ ] TASK-001: Initialize Python project with FastAPI
  - **Status:** ready
  - **Notes:** Create src/, tests/, scripts/. Dependencies: fastapi, uvicorn, python-telegram-bot, anthropic, sqlalchemy, asyncpg, alembic

- [ ] TASK-002: Set up PostgreSQL database schema
  - **Status:** ready
  - **Blocked by:** TASK-001
  - **Notes:** Tables: students, sessions, problems, responses, streaks. Use Alembic for migrations.

- [ ] TASK-005: Create core data models (SQLAlchemy)
  - **Status:** ready
  - **Blocked by:** TASK-002
  - **Notes:** Student, Problem, Session, Response, Streak models

### Phase 2: Onboarding

- [ ] TASK-006: Implement /start command flow
  - **Status:** ready
  - **Blocked by:** TASK-004, TASK-005
  - **Notes:** Detect new vs returning student, welcome in Bengali, store in DB

- [ ] TASK-007: Implement grade selection flow
  - **Status:** ready
  - **Blocked by:** TASK-006
  - **Notes:** Inline keyboard for grades 6, 7, 8

- [ ] TASK-008: Implement language preference
  - **Status:** ready
  - **Blocked by:** TASK-007
  - **Notes:** Bengali (default) or English

- [ ] TASK-009: Create message templates system
  - **Status:** ready
  - **Blocked by:** TASK-001
  - **Notes:** templates/ directory with Bengali and English strings

### Phase 3: Content System

- [ ] TASK-010: Design problem content schema
  - **Status:** ready
  - **Notes:** JSON/YAML format with question, answer, hints, difficulty, translations

- [ ] TASK-DB-001: Update hints_json column to support bilingual hint objects
  - **Status:** ready
  - **Assignee:** Maryam
  - **Flagged by:** Jahanara (content session 2026-02-24)
  - **Notes:** hints_json must store a list of objects with `{en, bn}` keys — not a flat string array. Current schema assumes `list[str]`. Content YAML already uses the new format. Update Problem model and Alembic migration before seeding. Example structure:
    ```json
    [
      {"en": "What does profit mean?", "bn": "লাভ মানে কী?"},
      {"en": "Profit = SP − CP. What are SP and CP here?", "bn": "লাভ = বিক্রয়মূল্য − ক্রয়মূল্য। এখানে কত?"},
      {"en": "SP = ₹540, CP = ₹450. Profit = ₹540 − ₹450. What is that?", "bn": "বিক্রয়মূল্য = ৫৪০, ক্রয়মূল্য = ৪৫০। লাভ = কত?"}
    ]
    ```

- [ ] TASK-DB-002: Add bn_reviewed boolean field to Problem model
  - **Status:** ready
  - **Assignee:** Maryam
  - **Flagged by:** Jahanara (content session 2026-02-24)
  - **Notes:** All Bengali translations produced by Jahanara are flagged `bn_reviewed: false` until reviewed by a native speaker. The Problem model needs a `bn_reviewed` boolean column (default False) so the admin dashboard and content pipeline can filter unreviewed translations. Add to Problem table + Alembic migration.

- [x] TASK-DB-003: Create MessageTemplate model for bilingual user-facing messages
  - **Status:** completed
  - **Assignee:** Maryam
  - **Flagged by:** User (2026-02-24)
  - **Completed:** 2026-02-24
  - **Notes:** Created `message_templates` table to store all user-facing messages (feedback, milestones, notifications, UI text, errors) in Bengali and English. Supports variable interpolation (e.g., `{student_name}`, `{days}`). Migration `4822235d35e4` includes 11 seed messages. See `BILINGUAL_CONTENT_COVERAGE.md` for full documentation.
  - **Migration:** `alembic/versions/4822235d35e4_add_message_templates_for_bilingual_.py`
  - **Files Added:**
    - `src/models/message_template.py` (MessageTemplate model + MessageCategory enum)
    - `BILINGUAL_CONTENT_COVERAGE.md` (comprehensive documentation)
  - **Files Modified:**
    - `src/models/__init__.py` (export MessageTemplate and MessageCategory)
    - `alembic/env.py` (import all models for autogenerate)

- [ ] TASK-012: Implement problem loader and selector
  - **Status:** ready
  - **Blocked by:** TASK-010, TASK-011
  - **Notes:** Load YAML, select 5 problems based on grade/difficulty/recency

- [ ] TASK-013: Create problem display formatter
  - **Status:** ready
  - **Blocked by:** TASK-012
  - **Notes:** Format for Telegram markdown, inline keyboards for MCQ

### Phase 4: AI Integration

- [ ] TASK-014: Set up Anthropic client wrapper
  - **Status:** ready
  - **Blocked by:** TASK-001
  - **Notes:** Async wrapper, retry logic, request logging

- [ ] TASK-015: Create Socratic hint generator
  - **Status:** ready
  - **Blocked by:** TASK-014
  - **Notes:** Prompt template for hints that guide without giving answers. Use Haiku.

- [ ] TASK-016: Implement response evaluator
  - **Status:** ready
  - **Blocked by:** TASK-014
  - **Notes:** Numeric: exact match. Text: Claude evaluation.

- [ ] TASK-017: Implement prompt caching layer
  - **Status:** ready
  - **Blocked by:** TASK-015
  - **Notes:** Cache common hints by problem_id. In-memory for MVP.

- [ ] TASK-018: Add encouragement message generator
  - **Status:** ready
  - **Blocked by:** TASK-014
  - **Notes:** Varied positive feedback, streak mentions

### Phase 5: Daily Practice Flow

- [ ] TASK-019: Implement /practice command
  - **Status:** ready
  - **Blocked by:** TASK-012, TASK-016
  - **Notes:** Check if completed today, start or resume session

- [ ] TASK-020: Build practice session state machine
  - **Status:** ready
  - **Blocked by:** TASK-019
  - **Notes:** States: AWAITING_ANSWER, SHOWING_HINT, SESSION_COMPLETE

- [ ] TASK-021: Implement answer submission handling
  - **Status:** ready
  - **Blocked by:** TASK-020
  - **Notes:** Evaluate, offer hints, max 3 attempts per problem

- [ ] TASK-022: Implement hint request handling
  - **Status:** ready
  - **Blocked by:** TASK-020, TASK-015
  - **Notes:** Fetch/generate hint, track hints_used

- [ ] TASK-023: Build session completion summary
  - **Status:** ready
  - **Blocked by:** TASK-021
  - **Notes:** Score, improvement areas, streak update

### Phase 6: Gamification

- [ ] TASK-024: Implement streak tracking logic
  - **Status:** ready
  - **Blocked by:** TASK-023
  - **Notes:** Increment if practiced yesterday, reset if missed

- [ ] TASK-025: Implement /streak command
  - **Status:** ready
  - **Blocked by:** TASK-024
  - **Notes:** Current streak, longest, 7-day calendar

- [ ] TASK-026: Add streak reminders
  - **Status:** ready
  - **Blocked by:** TASK-024
  - **Notes:** Daily reminder at 6 PM if not practiced

- [ ] TASK-027: Implement streak milestones
  - **Status:** ready
  - **Blocked by:** TASK-024
  - **Notes:** Celebrate 7, 14, 30 day streaks

### Phase 8: Admin

- [ ] TASK-038: Implement admin commands
  - **Status:** ready
  - **Blocked by:** TASK-032
  - **Notes:** /admin stats, /admin students, /admin cost

---

## Completed

_None yet_
