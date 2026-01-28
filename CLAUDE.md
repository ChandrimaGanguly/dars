# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**Dars** is an AI-powered tutoring platform designed for underserved students in South Asia. The MVP targets 50 students in Kolkata for an 8-week pilot through a Telegram bot interface.

**Key Constraint:** <$0.10/student/month cost ceiling

**Core Technologies:**
- Backend: FastAPI (Python 3.11+)
- Database: PostgreSQL + SQLAlchemy ORM + Alembic migrations
- Messaging: Telegram Bot API (webhook-based)
- AI: Claude API (Haiku model, prompt caching for cost control)
- Frontend: Admin dashboard (HTML/CSS/JS)

---

## Architecture & Design

### 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENTS                                  │
├──────────────────┬──────────────────┬──────────────────────┤
│  Telegram Bot    │  Admin Web UI    │  Future: Mobile App  │
│  (Webhook)       │  (HTML/JS)       │                      │
└──────┬───────────┴──────┬───────────┴──────┬───────────────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
                    ┌─────▼──────────┐
                    │  FastAPI       │
                    │  Backend       │
                    │  (Port 8000)   │
                    └─────┬──────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
    ┌───▼────┐      ┌────▼─────┐    ┌─────▼──────┐
    │PostgreSQL   │Claude API│    │Telegram    │
    │Database     │(Hints)   │    │Bot API     │
    │(Railway)    │          │    │            │
    └────────┘    └──────────┘    └────────────┘
```

### 2. Five Parallel Work Streams

The project is structured for 5 parallel work streams with explicit handoff points:

**Stream A: Backend Infrastructure (3-4 agents)**
- Owns: Database schema, FastAPI endpoints, authentication, health checks
- Deliverable: Working API serving all 12 REST endpoints
- Key handoffs: Day 2 (DB ready), Day 3 (API docs), Day 5 (security)

**Stream C: Content & Localization (2 agents + 1 human)**
- Owns: Problem curation (280 problems), curriculum mapping, Bengali translations
- Deliverable: Verified problems + localization strings
- Key handoff: Day 10 (content in database), Day 21 (translations ready)

**Stream D: Learning Algorithm (2-3 agents)**
- Owns: Problem selection, answer evaluation, adaptive difficulty, hints, streaks, engagement
- Services: 7 TypeScript service contracts (see API_ARCHITECTURE.md Part 3)
- Key handoffs: Day 13 (algorithm), Day 15 (practice flow), Day 17 (hints working)

**Stream E: Operations (1-2 agents)**
- Owns: Cost tracking, deployment (Railway), monitoring, backups
- Key handoffs: Day 29 (cost API), Day 35 (deployed)

**Stream B: Frontend (1 agent)**
- Owns: Admin dashboard
- Depends on: All APIs from Stream A
- Key handoff: Day 35 (dashboard complete)

### 3. REST API Structure

**12 Total Endpoints** (see API_ARCHITECTURE.md for OpenAPI 3.0 spec):

**Telegram Webhook:**
- `POST /webhook` - Receives Telegram updates, routes to message handlers

**Student Endpoints:**
- `GET /practice` - Retrieve 5 daily problems
- `POST /practice/{problem_id}/answer` - Submit answer, get evaluation
- `POST /practice/{problem_id}/hint` - Request Socratic hint (max 3/problem)
- `GET /streak` - Get streak info & milestones
- `GET /student/profile` - Get learning profile
- `PATCH /student/profile` - Update preferences (language, grade)

**Admin Endpoints:**
- `GET /admin/stats` - System statistics (students, engagement, cost)
- `GET /admin/students` - Paginated student list
- `GET /admin/cost` - Cost breakdown with budget alerts

**System:**
- `GET /health` - Health check (db + Claude API status)

### 4. Service Contracts (Internal)

Seven core service interfaces defined in API_ARCHITECTURE.md Part 3:

1. **ProblemSelector** - Select 5 problems per student (50% topic recency, 30% mastery, 20% difficulty)
2. **AnswerEvaluator** - Evaluate answers (numeric ±5%, MC exact, text semantic)
3. **AdaptiveDifficulty** - Adjust level (+1 on 2 correct, -1 on 1 incorrect)
4. **StreakTracker** - Track daily habits, milestones (7/14/30 days)
5. **HintGenerator** - Claude-powered Socratic hints (3 levels, cached)
6. **LearningPathGenerator** - Personalized daily/weekly paths
7. **NotificationService** - Reminders, encouragement messages, streak milestones

All service contracts specify:
- Input types (TypeScript interfaces)
- Output types (return values)
- Performance requirements (<500ms typical)
- Error handling strategy
- Cost implications (for Claude calls)

### 5. Data Models

**Core Entities:**
- `Student` - User profile (telegram_id, name, grade 6-8, language en/bn)
- `Problem` - Question (grade, topic, question_en/bn, answer, hints[3], difficulty 1-3)
- `Session` - Daily practice (5 problems, status, responses, timestamps)
- `Response` - Answer submission (problem_id, student_answer, is_correct, hints_used)
- `Streak` - Daily tracking (current, longest, milestones_achieved)
- `CostRecord` - API call logging (operation, tokens, cost_usd)

See API_ARCHITECTURE.md for complete schema definitions.

### 6. Dependency Map & Critical Path

**Critical Dependency Chain (32 days serial):**
```
REQ-017 (DB) → REQ-018 (API) → REQ-001 (Practice) → REQ-008 (Selection)
→ REQ-004 (Difficulty) → REQ-015 (Claude) → REQ-032 (Deploy)
```

**Parallelization reduces to 4-5 weeks with proper resource allocation:**
- REQ-005 (Content: 10 days) runs parallel with REQ-017-018 (DB/API: 2-3 days)
- REQ-014 (Telegram) runs parallel with REQ-018 (API)
- Streams don't block each other after initial handoffs

Full dependency graph: See DEPENDENCY_ANALYSIS.md

---

## Development Workflow

### 1. Set Up Environment

```bash
# Install project in editable mode with dev dependencies
pip install -e ".[dev]"

# Install git hooks (pre-commit validation)
bash scripts/setup-hooks.sh

# Verify setup
python -c "import fastapi; print('Setup OK')"
```

### 2. Build & Run

**Start development server:**
```bash
# Hot-reload FastAPI app on port 8000
uvicorn src.main:app --reload --port 8000

# Check it's running
curl http://localhost:8000/health
```

**Database migrations:**
```bash
# Create new migration (auto-detect changes)
alembic revision --autogenerate -m "Add student_id index"

# Apply migrations
alembic upgrade head

# Check current version
alembic current
```

### 3. Code Quality & Testing

**Pre-commit validation (automatic before every commit):**
```bash
# What runs automatically on git commit:
# 1. Black formatting (100 char line length, py311)
# 2. Ruff linting (E,W,F,I,C,B,UP,ARG,SIM,RUF rules)
# 3. MyPy type checking (strict mode, no implicit optional)
# 4. Pytest unit tests (tests/unit/*)
# 5. Coverage check (≥70% minimum)
# 6. Git status (no secrets detected)

# Manual pre-commit validation
bash scripts/validate.sh --skip-slow

# Auto-fix formatting/linting issues
bash scripts/validate.sh --fix --skip-slow
```

**Running tests:**
```bash
# All tests (unit + integration)
pytest

# Unit tests only (fast, ~5 seconds)
pytest tests/unit -v

# Integration tests only (slow, requires DB)
pytest tests/integration -v

# Single test file
pytest tests/unit/test_streaks.py -v

# Single test function
pytest tests/unit/test_streaks.py::test_streak_increments -v

# With coverage report
pytest --cov=src --cov-report=html
# Open htmlcov/index.html to view

# Run specific marker
pytest -m unit  # Only @pytest.mark.unit tests
pytest -m integration  # Only integration tests
```

**Linting & formatting:**
```bash
# Format code (Black)
black src/ tests/

# Check linting (Ruff)
ruff check src/ tests/

# Fix linting issues
ruff check --fix src/ tests/

# Type check (MyPy)
mypy src/
```

### 4. Common Development Commands

| Task | Command |
|------|---------|
| Run dev server | `uvicorn src.main:app --reload` |
| Run all tests | `pytest` |
| Run unit tests only | `pytest tests/unit -v` |
| Check a single file | `pytest tests/unit/test_example.py::test_something` |
| Format code | `bash scripts/validate.sh --fix --skip-slow` |
| Type check | `mypy src/` |
| View coverage report | `pytest --cov=src --cov-report=html && open htmlcov/index.html` |
| Database migrate | `alembic upgrade head` |
| Rollback database | `alembic downgrade -1` |

---

## Critical Implementation Details

### 1. Telegram Integration

**Webhook Flow:**
1. Telegram sends message → `POST /webhook` (Bearer token auth)
2. FastAPI extracts command (/start, /practice, /hint, etc.)
3. Handler processes (may call Claude, database, etc.)
4. Response sent back via Telegram API

**Phase 0 Authentication:** Hardcoded admin Telegram IDs (simple for pilot)
**Phase 1+:** JWT tokens via OAuth

**Message Idempotency:** Handle duplicate webhook deliveries gracefully (Telegram may retry)

### 2. Claude API Cost Control

**Budget: <$0.10/student/month** requires aggressive optimization:

1. **Model Selection:** Claude Haiku (10x cheaper than Sonnet)
2. **Prompt Caching:** Cache hints by (problem_id, hint_number) for 7+ days
   - Target cache hit rate: 70%+
   - Cost per hint: <$0.001
3. **Pre-generated Content:** Don't generate hints on-the-fly; use cached
4. **Rate Limiting:** Max 10 AI interactions/day per student

**Cost Tracking:**
- Log every Claude call with token count
- Track per-student costs
- Alert if extrapolated cost > $0.15/month

See CostTracker service contract in API_ARCHITECTURE.md

### 3. Answer Evaluation Strategy

**Numeric Problems:** Accept if exact OR within ±5% tolerance
```
Expected: 75
Student answer: 74 (within 5%) → ✓ Correct
Student answer: 70 (6.7% off) → ✗ Wrong
```

**Multiple Choice:** Exact index match required
```
Correct: option[1] (index 1)
Student selects: option[1] → ✓ Correct
Student selects: option[0] → ✗ Wrong
```

**Text Answers:** Future semantic evaluation via Claude (Phase 1+)

### 4. Streak & Milestone System

**UTC Boundary:** Streaks reset at midnight UTC (12am UTC = 5:30am IST)

**Increments:** +1 on each day student completes practice
**Resets:** On missed day
**Milestones:** Celebrate at 7, 14, 30 days with special messages

**Timezone Handling:** All dates stored as UTC, convert to IST for display (UTC+5:30)

### 5. Problem Weighting Algorithm

**Selection considers 3 factors:**
1. **Topic Recency (50%):** Haven't practiced this topic recently → prioritize
2. **Mastery (30%):** Low accuracy on this topic → include for reinforcement
3. **Difficulty Variation (20%):** Mix of easy/medium/hard to maintain engagement

**Deterministic:** Same input → Same output (critical for testing and reproducibility)

### 6. Bengali Localization

**Phase 0 Requirements:**
- All student-facing messages in Bengali (with English fallback)
- Problem statements in both languages
- Numbers/dates formatted for Indian context

**Message Management:**
- Centralized MessageKey enum (25+ keys)
- LocalizationService provides all strings
- Support for parameter interpolation: "Hello {name}, you got {correct}/{total}"

---

## Documentation Navigation

**For specific questions, consult these files:**

| Question | Document | Section |
|----------|----------|---------|
| What are the 40 requirements? | REQUIREMENTS.md | Section 1 |
| Which 16 requirements are Phase 0? | BUSINESS_VALUE_ANALYSIS.md | Value Tiers |
| What's the 8-week execution plan? | AGENT_ROADMAP.md | Phases 1-8 |
| How do work streams parallelize? | DEPENDENCY_ANALYSIS.md | Part 2 |
| What's the REST API contract? | API_ARCHITECTURE.md | Part 2 |
| How are service contracts defined? | API_ARCHITECTURE.md | Part 3 |
| What's the error handling standard? | API_ARCHITECTURE.md | Part 4 |
| Are interface contracts aligned? | INTERFACE_ALIGNMENT_ANALYSIS.md | Gap analysis |
| What's been done already? | PROJECT_STATUS.md | ✅ Completed |
| How do I set up to develop? | TESTING.md | Quick Start |
| What's the code quality pipeline? | VALIDATION_PIPELINE.md | 7-stage pipeline |

---

## OpenSpec & Proposals

When working on features, refer to OpenSpec instructions:

```bash
# View project spec & guidelines
cat openspec/AGENTS.md

# View current proposal
cat openspec/changes/dars/proposal.md

# View implementation tasks
cat openspec/changes/dars/tasks.md

# Create new change proposal (if needed)
openspec new change feature-name --description "What this changes"
```

**OpenSpec is used for:**
- Architectural decisions
- Breaking changes
- Performance/security work
- Ambiguous requirements needing spec before coding

---

## Key Files & Locations

| Purpose | Location |
|---------|----------|
| Python project config | `pyproject.toml` |
| Test configuration | `pytest.ini` |
| Pre-commit framework | `.pre-commit-config.yaml` |
| Validation pipeline | `scripts/validate.sh` |
| API specification | `API_ARCHITECTURE.md` |
| Requirements specification | `REQUIREMENTS.md` |
| Roadmap & phases | `AGENT_ROADMAP.md` |
| Dependency analysis | `DEPENDENCY_ANALYSIS.md` |
| Business value analysis | `BUSINESS_VALUE_ANALYSIS.md` |
| OpenSpec proposal | `openspec/changes/dars/proposal.md` |
| Implementation tasks | `openspec/changes/dars/tasks.md` |

---

## Important Constraints & Decisions

1. **Cost Ceiling:** <$0.10/student/month is non-negotiable. Every feature must be designed with cost in mind.

2. **Telegram-First:** Phase 0 uses Telegram (free, no approval needed). WhatsApp Business API deferred to Phase 1 (requires approval process).

3. **50-Student Pilot:** Phase 0 targets exactly 50 students for 8 weeks in Kolkata to validate core hypothesis (students will learn via AI tutoring via chat).

4. **Python 3.11+:** Strict requirement for type hints, performance.

5. **Strict MyPy:** All code must pass `mypy --strict` with no implicit optionals. This catches bugs early.

6. **70% Test Coverage Minimum:** Every commit blocks if coverage < 70%. Focus on meaningful tests, not just coverage percentage.

7. **Pre-commit Validation:** Must pass all 7 stages (formatting, linting, type check, unit tests, coverage) before commit succeeds. No exceptions.

8. **No Sensitive Data in Commits:** .env files, API keys, tokens will block commits. Use environment variables.

---

## Getting Help

**For questions about:**
- **Project architecture** → Read API_ARCHITECTURE.md (Part 1)
- **Requirements** → Read REQUIREMENTS.md or ROADMAP_SUMMARY.md
- **Parallel work streams** → Read DEPENDENCY_ANALYSIS.md (Part 3)
- **Testing approach** → Read TESTING.md
- **Code quality** → Read VALIDATION_PIPELINE.md
- **Business context** → Read BUSINESS_VALUE_ANALYSIS.md

**For immediate help with errors:**
1. Check VALIDATION_PIPELINE.md for validation errors
2. Check pyproject.toml for tool configuration
3. Check pytest.ini for test configuration
4. Run `bash scripts/validate.sh -v` for verbose output

---

## Next Phase: Implementation

Phase 1 (Backend Foundation) will begin once this infrastructure is complete. The 5 work streams will parallelize across:

- **Stream A:** Database schema + FastAPI endpoints + auth
- **Stream C:** Content curation + Bengali translations (longest single task: 10 days)
- **Stream D:** Learning algorithms (selection, evaluation, difficulty, hints)
- **Stream E:** Cost tracking + deployment
- **Stream B:** Admin dashboard (starts later, depends on APIs)

All handoff points and data formats are formally specified in API_ARCHITECTURE.md.
