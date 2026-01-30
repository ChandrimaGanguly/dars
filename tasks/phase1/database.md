# PHASE1-A-1: Database Schema & Models

**Owner:** Maryam (Database & ORM Expert)
**Duration:** ~2 days
**Status:** Ready to start
**GitHub Issue:** #5

---

## Task Summary

| Subtask | Description | Status | Assignee |
|---------|-------------|--------|----------|
| PHASE1-A-1.1 | Create 6 SQLAlchemy models with relationships | 📋 Ready | Maryam |
| PHASE1-A-1.2 | Design relationships and foreign keys | 📋 Ready | Maryam |
| PHASE1-A-1.3 | Create Alembic migrations | 📋 Ready | Maryam |
| PHASE1-A-1.4 | Unit tests (≥80% coverage) | 📋 Ready | Maryam |
| PHASE1-A-1.5 | Verify with Jodha (imports work) | 📋 Blocked | Maryam + Jodha |

---

## Subtasks

### PHASE1-A-1.1: Create 6 SQLAlchemy Models

**Objective:** Create all core data models with proper relationships and constraints

**Models to Create:**
- [ ] **Student** - User profile
  - Fields: telegram_id (unique, indexed), name, grade (6-8), language (bn/en), created_at, updated_at
  - Relationships: sessions, streak, cost_records

- [ ] **Problem** - Math problem content
  - Fields: problem_id (PK), grade, topic, subtopic, question_en, question_bn, answer, difficulty (1-3), hints (JSON), created_at
  - Indexes: grade, topic, difficulty

- [ ] **Session** - Daily practice session
  - Fields: session_id (PK), student_id (FK), problem_ids (JSON), status (enum), date, expires_at, completed_at, total_time_seconds, problems_correct
  - Relationships: student, responses

- [ ] **Response** - Individual answer submission
  - Fields: response_id (PK), session_id (FK), problem_id (FK), student_answer, is_correct, time_spent_seconds, hints_used (0-3), evaluated_at
  - Indexes: session_id, problem_id

- [ ] **Streak** - Daily habit tracking
  - Fields: student_id (PK, one-to-one), current_streak, longest_streak, last_practice_date, milestones_achieved (JSON), updated_at

- [ ] **CostRecord** - API call cost tracking
  - Fields: cost_id (PK), student_id (FK, nullable), session_id (FK, nullable), operation, api_provider, input_tokens, output_tokens, cost_usd, recorded_at

**Code Quality:**
- [ ] All models have full type hints
- [ ] All relationships properly defined
- [ ] Cascade deletes where appropriate
- [ ] JSON fields with proper validation
- [ ] Enums for constrained fields (grade, language, status, confidence_level)

**Testing:**
- [ ] Unit tests for model creation
- [ ] Test relationships (foreign keys work)
- [ ] Test constraints (grade 6-8, enums)
- [ ] Test cascading deletes

---

### PHASE1-A-1.2: Design Relationships & Foreign Keys

**Objective:** Ensure proper data relationships and referential integrity

**Relationships to Implement:**
- [ ] Student → Sessions (one-to-many)
  - Cascade delete: ON DELETE CASCADE

- [ ] Student → Streak (one-to-one)
  - Cascade delete: ON DELETE CASCADE

- [ ] Student → CostRecord (one-to-many)
  - Cascade delete: ON DELETE SET NULL

- [ ] Session → Responses (one-to-many)
  - Cascade delete: ON DELETE CASCADE

- [ ] Problem → Response (one-to-many via session)
  - No cascade (problems are reusable)

**Indexes to Create:**
- [ ] `idx_students_telegram_id` - Fast lookup by Telegram ID
- [ ] `idx_sessions_student_id_date` - Fast lookup of student's sessions
- [ ] `idx_responses_session_id` - Fast lookup of session responses
- [ ] `idx_cost_records_student_id` - Fast cost aggregation per student

**Constraints:**
- [ ] Grade must be 6-8
- [ ] Language must be 'en' or 'bn'
- [ ] Difficulty must be 1-3
- [ ] Hints_used must be 0-3
- [ ] Status must be valid enum value

---

### PHASE1-A-1.3: Create Alembic Migrations

**Objective:** Generate database migration files

**Steps:**
- [ ] Initialize Alembic (if not done): `alembic init alembic`
- [ ] Configure alembic/env.py to use async database
- [ ] Create migration: `alembic revision --autogenerate -m "Initial schema with all models"`
- [ ] Verify migration file syntax
- [ ] Test migration up: `alembic upgrade head`
- [ ] Test migration down: `alembic downgrade -1`
- [ ] Verify tables exist and have correct structure

**Checklist:**
- [ ] All CREATE TABLE statements present
- [ ] All indexes defined
- [ ] All foreign keys configured
- [ ] All constraints in place
- [ ] Migration is idempotent (can run multiple times safely)

---

### PHASE1-A-1.4: Unit Tests (≥80% Coverage)

**Objective:** Comprehensive test coverage for all models

**Test Files:** `tests/unit/test_models.py`

**Test Cases:**

✅ **Student Model Tests**
- [ ] Create student with all fields
- [ ] Unique constraint on telegram_id
- [ ] Grade validation (6-8 only)
- [ ] Language validation (en/bn only)
- [ ] Timestamps auto-set
- [ ] Delete student → cascade delete sessions

✅ **Problem Model Tests**
- [ ] Create problem with all fields
- [ ] Difficulty range (1-3)
- [ ] JSON hints array structure
- [ ] Questions in both languages

✅ **Session Model Tests**
- [ ] Create session with problem_ids
- [ ] Status enum values
- [ ] Expire check (is_expired() method)
- [ ] Accuracy calculation (get_accuracy())
- [ ] Delete session → cascade delete responses

✅ **Response Model Tests**
- [ ] Create response with answer and evaluation
- [ ] Hints_used range (0-3)
- [ ] is_correct boolean
- [ ] Time_spent_seconds tracking
- [ ] Evaluated_at timestamp

✅ **Streak Model Tests**
- [ ] One-to-one relationship with student
- [ ] Milestone JSON structure
- [ ] Current/longest streak tracking

✅ **CostRecord Model Tests**
- [ ] Track API call costs
- [ ] Optional student/session (SET NULL)
- [ ] Operation type tracking

**Coverage Target:** ≥80% of model code

---

### PHASE1-A-1.5: Verify with Jodha

**Objective:** Ensure models integrate properly with API code

**Coordination Tasks:**
- [ ] Maryam notifies Jodha when PHASE1-A-1.1 & PHASE1-A-1.2 complete
- [ ] Jodha imports models in FastAPI routes
- [ ] Verify imports work without errors
- [ ] Verify SQLAlchemy session dependency works
- [ ] Check for any missing fields or relationships
- [ ] Resolve any integration issues

**Success Criteria:**
- [ ] `from src.models import Student, Problem, Session, Response, Streak, CostRecord` works
- [ ] All model relationships accessible
- [ ] No circular import errors
- [ ] FastAPI route can create/query models

---

## Success Criteria (Whole Task)

- ✅ All 6 models created with full type hints
- ✅ All relationships defined (foreign keys, cascade rules)
- ✅ All indexes created for performance
- ✅ Alembic migrations generated and tested
- ✅ Database schema verified (tables, columns, constraints)
- ✅ Unit tests pass with ≥80% coverage
- ✅ MyPy strict type checking passes
- ✅ Code review passed
- ✅ Integration with Jodha's API code verified

---

## Code Review Checklist (Self-Review)

- [ ] All models inherit from `Base`
- [ ] All columns have explicit types (not Optional unless nullable)
- [ ] Foreign keys point to correct tables
- [ ] Indexes created for frequently queried fields
- [ ] Constraints prevent invalid data (grades 6-8, language en/bn, etc.)
- [ ] Relationships use proper lazy loading strategy
- [ ] JSON fields have proper validation
- [ ] No N+1 query problems (proper eager loading setup)
- [ ] Timestamps (created_at, updated_at) auto-managed
- [ ] Cascade delete rules documented
- [ ] Tests cover all happy path and edge cases
- [ ] No hardcoded data or magic numbers
- [ ] Clear docstrings on complex fields

---

## References

- **PHASE1_TASKS.md** - Section 1 (Agent A: Database) for detailed specs
- **API_ARCHITECTURE.md** - Data model specifications
- **AGENT_CHECKLIST.md** - Development workflow
- **SQLAlchemy Docs** - ORM best practices
- **Alembic Docs** - Migration management

---

## Dependencies

- ✅ No upstream dependencies (can start immediately)
- ⏳ **Blocks:** PHASE1-B-1 (Jodha needs models for imports)
- ⏳ **Blocks:** PHASE1-C-1.6 (Noor needs complete API for testing)

---

## Timeline

| Day | Subtask | Deliverable |
|-----|---------|------------|
| 1 | PHASE1-A-1.1, PHASE1-A-1.2 | 6 models + relationships created |
| 1 | PHASE1-A-1.3 | Alembic migrations tested |
| 2 | PHASE1-A-1.4 | Unit tests (80%+ coverage) |
| 2 | PHASE1-A-1.5 | Integration verified with Jodha |

**Total Duration:** ~2 days

---

**Status:** 📋 Ready to start
**Last Updated:** 2026-01-30
**GitHub Issue:** #5
