# Phase 1: Backend & Integration Foundation

**Duration:** Week 1 (5 days of agent work)
**Complexity:** 4-6 days total (2-3 days backend + API, 2-3 days security)
**Status:** Ready for implementation
**Start Date:** 2026-02-03 (planned)

---

## Overview

Phase 1 is the critical foundation phase where three specialized agents work in parallel to:

1. **Build database models and migrations (Maryam)**
2. **Implement FastAPI REST API with 12 endpoints (Jodha)**
3. **Implement 8 critical security requirements (Noor)**

This folder contains agent-specific task breakdowns using the **PHASE1-X-X** labelling system for clear ownership and parallel execution.

---

## Files in This Folder

### Primary Task Files

| File | Owner | Task ID | Duration | GitHub Issue |
|------|-------|---------|----------|--------------|
| **database.md** | Maryam | PHASE1-A-1 | 2 days | #5 |
| **api.md** | Jodha | PHASE1-B-1 | 2 days | #6 |
| **security.md** | Noor | PHASE1-C-1 | 2-3 days | #7 |
| **README.md** | - | - | - | - |

### Reference Files (Root Level)

| File | Purpose |
|------|---------|
| `/PHASE1_TASKS.md` | Master task tracker (comprehensive view) |
| `/PROJECT_PROGRESS.md` | Status dashboard with critical path |
| `/AGENT_ROADMAP.md` | 8-week roadmap context |
| `/SECURITY_ROADMAP_INTEGRATION.md` | Security audit findings |
| `../TASK_MAPPING.md` | Legacy TASK-XXX to PHASE1-X-X mapping |

---

## Parallel Execution Model

```
Week 1: Three agents work simultaneously

Track A (Maryam)           Track B (Jodha)            Track C (Noor)
Database Models            FastAPI API                Security Hardening
(2 days)                   (2 days, depends on A)     (2-3 days, independent)
│                          │                          │
├─ PHASE1-A-1.1 ─────┐    │                          │
├─ PHASE1-A-1.2 ─────┤────└─► PHASE1-B-1.1          ├─ PHASE1-C-1.1
├─ PHASE1-A-1.3       │        PHASE1-B-1.2 ────┐   ├─ PHASE1-C-1.2
├─ PHASE1-A-1.4       │        PHASE1-B-1.3      │   ├─ PHASE1-C-1.3 ⭐ CRITICAL
└─ PHASE1-A-1.5       │        PHASE1-B-1.4      │   ├─ PHASE1-C-1.4
                      │        PHASE1-B-1.5      │   ├─ PHASE1-C-1.5
                      │        PHASE1-B-1.6 ◄────┤   ├─ PHASE1-C-1.6
                      │                          │   ├─ PHASE1-C-1.7
                      └──────────────────────────┴───┴─ PHASE1-C-1.8
                                                 │
                                                 └─ PHASE1-C-1.9 [CODE REVIEW]

Results:
- Sequential critical path: 4-5 days (A → B done, C in parallel)
- Parallel critical path: 2-3 days (A, B, C simultaneous with dependencies)
- Blocker: PHASE1-C-1.9 must complete before Phase 3 can begin
```

---

## Task Breakdown by Agent

### Maryam: Database Schema & Models (PHASE1-A-1)

**What:** Create 6 SQLAlchemy models with relationships and Alembic migrations

**Subtasks:**
- PHASE1-A-1.1 - Create 6 models (Student, Problem, Session, Response, Streak, CostRecord)
- PHASE1-A-1.2 - Design relationships and foreign keys
- PHASE1-A-1.3 - Create Alembic migrations
- PHASE1-A-1.4 - Unit tests (≥80% coverage)
- PHASE1-A-1.5 - Verify with Jodha

**Success Criteria:**
- All models with type hints
- Migrations tested
- 70%+ test coverage
- MyPy strict passes

**File:** `database.md`

---

### Jodha: FastAPI REST API (PHASE1-B-1)

**What:** Build FastAPI app with 12 REST endpoints across 6 route modules

**Subtasks:**
- PHASE1-B-1.1 - FastAPI instance + config
- PHASE1-B-1.2 - Create 6 route modules (health, webhook, practice, student, streak, admin)
- PHASE1-B-1.3 - Middleware setup (CORS, request ID, error handlers)
- PHASE1-B-1.4 - Database integration (session dependency)
- PHASE1-B-1.5 - Unit tests (≥70% coverage)
- PHASE1-B-1.6 - Code review security work from Noor

**Success Criteria:**
- 12 endpoints implemented
- Pydantic validation
- Async/await properly used
- 70%+ test coverage

**File:** `api.md`

**Dependencies:** Needs Maryam's models by Day 2

---

### Noor: Security Hardening (PHASE1-C-1)

**What:** Implement 8 critical security requirements from audit

**Subtasks (Implementation Order):**
- PHASE1-C-1.1 - SEC-002: Telegram webhook verification
- PHASE1-C-1.2 - SEC-001: CORS hardening
- PHASE1-C-1.3 - SEC-003: Student database verification ⭐ **CRITICAL - BLOCKS PHASE 3**
- PHASE1-C-1.4 - SEC-004: Admin auth enforcement
- PHASE1-C-1.5 - SEC-005: Rate limiting
- PHASE1-C-1.6 - SEC-006: Log sanitization
- PHASE1-C-1.7 - SEC-007: Input validation
- PHASE1-C-1.8 - SEC-008: Query validation
- PHASE1-C-1.9 - Security testing & code review

**Success Criteria (GO/NO-GO for Phase 3):**
- CORS restricted (not *)
- All student endpoints verify in DB
- All admin endpoints authenticated
- Telegram webhook verified
- Rate limiting active
- No secrets in logs
- Input/query validation working
- No stack traces in errors
- All tests passing
- Code reviewed by Jodha

**File:** `security.md`

**⚠️ CRITICAL:** Must be 100% complete before Phase 3 begins

---

## How to Use These Files

### For the Agent

1. **Read your task file first**
   - `database.md` (if Maryam)
   - `api.md` (if Jodha)
   - `security.md` (if Noor)

2. **Understand dependencies**
   - Maryam: No dependencies (start immediately)
   - Jodha: Depends on Maryam's models by Day 2
   - Noor: Independent (can start immediately)

3. **Track progress in GitHub issue**
   - Update checklist as you complete subtasks
   - Add comments for blockers or questions

4. **Check references**
   - PHASE1_TASKS.md (comprehensive)
   - Root-level docs (AGENT_ROADMAP.md, SECURITY_ROADMAP_INTEGRATION.md, etc.)

### For the Project Manager

1. **Monitor all three in GitHub**
   - Issue #5: PHASE1-A-1 (Maryam)
   - Issue #6: PHASE1-B-1 (Jodha)
   - Issue #7: PHASE1-C-1 (Noor) ⚠️ CRITICAL

2. **Track critical path**
   - PHASE1-C-1.9 (security code review) is the blocker for Phase 3
   - All three must be complete before moving to Phase 3

3. **Monitor dependencies**
   - Day 2: Jodha needs Maryam's models
   - Day 3+: Noor needs complete API for testing
   - End of week: Jodha needs to review Noor's security work

---

## Labelling System: PHASE1-X-X

**Format:** `PHASE1-{TRACK}-{TASK}.{SUBTASK}`

**Examples:**
- `PHASE1-A-1` = Database (Track A), Main Task 1
- `PHASE1-A-1.1` = Database, Task 1, Subtask 1 (create models)
- `PHASE1-B-1.6` = API, Task 1, Subtask 6 (code review)
- `PHASE1-C-1.3` = Security, Task 1, Subtask 3 (student verification)

**Why this system:**
- Clear ownership (A=Maryam, B=Jodha, C=Noor)
- Traceable to GitHub issues
- Easy to cross-reference in documentation
- Supports parallel execution tracking

**See also:** `../TASK_MAPPING.md` for relationship to legacy TASK-XXX system

---

## Timeline & Milestones

### Week 1: Phase 1 Execution

| Day | Maryam (Track A) | Jodha (Track B) | Noor (Track C) | Blocker |
|-----|-----------------|-----------------|----------------|---------|
| 1 | PHASE1-A-1.1, A-1.2, A-1.3 | A-1.1 done, waiting | C-1.1, C-1.2 | Jodha waits for models |
| 2 | A-1.4, A-1.5 | B-1.1, B-1.2 (models ready) | C-1.3, C-1.4, C-1.5 | Noor waits for API |
| 3 | A-1 complete | B-1.3, B-1.4, B-1.5 | C-1.6, C-1.7, C-1.8 | - |
| 4 | Standby | B-1.6 (code review) | C-1.9 (testing) | Jodha reviews Noor |
| 5 | Standby | Standby | C-1.9 complete | **PHASE 3 GO/NO-GO** |

### Phase 3 Gate (Before Week 2)

- [ ] PHASE1-A-1 complete and tested ✓
- [ ] PHASE1-B-1 complete and tested ✓
- [ ] PHASE1-C-1 **100% complete** and code-reviewed ✓
- [ ] Security test plan passes ✓
- [ ] No open security issues ✓

**Decision:** GO → Phase 3 (Practice endpoints) or NO-GO → Debug

---

## Integration Points

### A → B Handoff
**When:** End of Day 2 (PHASE1-A-1.1 complete)
**What:** Maryam provides 6 SQLAlchemy models to Jodha
**How:** Push to git, notify Jodha, unblock PHASE1-B-1.2

### B → C Handoff
**When:** End of Day 3 (PHASE1-B-1.4 complete)
**What:** Jodha provides complete API to Noor
**How:** Push to git, API testable, unblock PHASE1-C-1.6 (logging)

### C → B Handoff
**When:** End of Day 5 (PHASE1-C-1.9 complete)
**What:** Noor provides security implementations, Jodha reviews
**How:** Git PR, Jodha code review, sign-off for Phase 3

---

## Critical Success Factors

1. **Parallel Execution**
   - Start all three agents simultaneously
   - Minimize blocking (clear handoff points)

2. **Security Is Non-Negotiable**
   - PHASE1-C-1 BLOCKS Phase 3
   - 100% completion required (not 90%)
   - All 8 requirements must be implemented

3. **Code Quality**
   - Type hints on all code (mypy strict)
   - 70%+ test coverage minimum
   - Pre-commit validation must pass

4. **Communication**
   - Daily standups (async comments OK)
   - Notify blockers immediately
   - Code reviews same-day turnaround

---

## Questions?

**For technical questions:**
- Read your task file (`database.md`, `api.md`, or `security.md`)
- Check PHASE1_TASKS.md for detailed specs
- Check root-level docs (CLAUDE.md, API_ARCHITECTURE.md, etc.)

**For coordination questions:**
- Check PROJECT_PROGRESS.md for timeline
- Check TASK_MAPPING.md for legacy system context
- Ask in GitHub issue comments

---

## Phase 1 Success Definition

✅ **Backend Infrastructure:**
- Database schema with 6 models
- FastAPI app with 12 working endpoints
- All 8 security requirements implemented

✅ **Testing:**
- 70%+ overall code coverage
- All tests passing (unit + integration)
- MyPy strict type checking passes

✅ **Security:**
- CORS hardened
- Student verification prevents IDOR
- Admin auth enforced
- Rate limiting active
- Logs contain no secrets
- Input validation prevents DOS

✅ **Readiness for Phase 3:**
- Database verified to work
- API endpoints testable
- Security code reviewed
- Ready for practice endpoint implementation

---

**Document Status:** ✅ Active (Updated 2026-01-30)
**Next Review:** After Phase 1 completion
**Maintained By:** Project Coordinator
