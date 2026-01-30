# Task Naming & Phase Mapping

This document clarifies the relationship between the legacy TASK-XXX naming system (used in openspec/changes/dars/tasks.md) and the new PHASE1-X-X agent-based naming system.

---

## Overview

**Two Naming Systems (For Clarity During Phase 1):**

1. **Legacy System (TASK-XXX):** Used in openspec/ and original tasks/ files
   - General task tracking across all phases
   - Examples: TASK-001, TASK-005, TASK-038
   - Keeps history and original architecture

2. **New Agent System (PHASE1-X-X):** Used in PHASE1_TASKS.md and GitHub issues
   - Agent-centric breakdown for parallel execution
   - Examples: PHASE1-A-1.1, PHASE1-B-1.2, PHASE1-C-1.3
   - Three parallel tracks: A (Database), B (API), C (Security)

**Why Both Exist:**
- Legacy system is the source of truth for overall project roadmap
- Agent system is optimized for Phase 1 execution with Maryam, Jodha, Noor
- Both will be consolidated after Phase 1

---

## Phase 1 Mapping: TASK-XXX → PHASE1-X-X

### Track A: Database Schema & Models (Maryam)

**PHASE1-A-1: Create database models and migrations**

| PHASE1 Label | Legacy TASK | Description |
|-------|---------|----------------|
| PHASE1-A-1.1 | TASK-001, TASK-002 | Project setup + PostgreSQL database schema |
| PHASE1-A-1.2 | TASK-005 | Create core data models (Student, Problem, Session, Response, Streak, CostRecord) with relationships |
| PHASE1-A-1.3 | TASK-002 (migrations) | Create Alembic migrations |
| PHASE1-A-1.4 | Implicit in TASK-005 | Unit tests for all models (≥80% coverage) |
| PHASE1-A-1.5 | Implicit (coordination) | Verify with Jodha that imports work for API |

**Duration:** ~2 days
**Dependencies:** None
**Blocks:** PHASE1-B-1 (API needs model imports)

---

### Track B: FastAPI REST API Implementation (Jodha)

**PHASE1-B-1: Build FastAPI app with all 12 REST endpoints**

| PHASE1 Label | Legacy TASK | Description |
|-------|---------|-------|
| PHASE1-B-1.1 | TASK-001 | Initialize FastAPI app and configuration |
| PHASE1-B-1.2 | TASK-003, TASK-004 | Create 6 route modules: health, webhook, practice, student, streak, admin |
| PHASE1-B-1.3 | TASK-001 | Middleware setup: CORS (placeholder), request IDs, error handlers |
| PHASE1-B-1.4 | TASK-001 | Database session integration |
| PHASE1-B-1.5 | Implicit in route tasks | Unit tests for all endpoints (≥70% coverage) |
| PHASE1-B-1.6 | Implicit (coordination) | Code review security work from Noor |

**Duration:** ~2 days
**Dependencies:** PHASE1-A-1 (needs models by Day 2)
**Blocks:** PHASE1-C-1.6 (Noor needs complete API for security review)

**Legacy Tasks Covered:**
- TASK-003: Set up FastAPI with Telegram webhook
- TASK-004: Implement message handler routing (simplified for Phase 1 MVP)

---

### Track C: Security Hardening (Noor)

**PHASE1-C-1: Implement all 8 critical security requirements**

| PHASE1 Label | Security ID | WBBSE Vuln ID | Description |
|-------|----------|---------|-----------|
| PHASE1-C-1.1 | SEC-002 | CWE-303 | Telegram webhook signature verification |
| PHASE1-C-1.2 | SEC-001 | CWE-346 | CORS hardening (restrict from * to specific domains) |
| PHASE1-C-1.3 | SEC-003 | CWE-639 | Student database verification (prevents IDOR) |
| PHASE1-C-1.4 | SEC-004 | CWE-287 | Admin authentication enforcement |
| PHASE1-C-1.5 | SEC-005 | CWE-400 | Rate limiting (slowapi) |
| PHASE1-C-1.6 | SEC-006 | CWE-532 | Sensitive data sanitization in logs |
| PHASE1-C-1.7 | SEC-007 | CWE-400 | Input length validation |
| PHASE1-C-1.8 | SEC-008 | CWE-129 | Query parameter validation |
| PHASE1-C-1.9 | Testing | N/A | Security testing and code review |

**Duration:** ~2-3 days
**Dependencies:** PHASE1-B-1 (complete API needed for testing)
**Blocks:** Phase 3 (CRITICAL - must be 100% complete before practice endpoints)

**Note:** Security requirements are NEW to Phase 1 (integrated from 2026-01-30 security audit). Not in legacy TASK system.

---

## How to Use This Document

### For Developers (Maryam, Jodha, Noor):

1. **Track your work with PHASE1-X-X labels**
   - All GitHub issues use PHASE1-X-X
   - PHASE1_TASKS.md uses PHASE1-X-X subtasks
   - This provides clear, granular tracking

2. **Reference legacy TASK-XXX for context**
   - See openspec/changes/dars/tasks.md for broader context
   - Understand how Phase 1 work fits into 8-week roadmap

3. **Report progress in both systems**
   - Update GitHub issues with PHASE1-X-X labels
   - Document any deviations from legacy TASK expectations

### For Project Managers:

1. **Phase 1 Dashboard**
   - Use PHASE1_TASKS.md for execution tracking
   - Use GitHub issues #5, #6, #7 for real-time status
   - Use PROJECT_PROGRESS.md for timeline and critical path

2. **Full Project Roadmap**
   - Use AGENT_ROADMAP.md for Phases 1-8 planning
   - Use legacy TASK-XXX for detailed task reference
   - Keep openspec/changes/dars/tasks.md as source of truth

---

## File Organization

### Root Level (Planning & Roadmap):
- **AGENT_ROADMAP.md** - 8-week roadmap with all phases
- **PROJECT_PROGRESS.md** - Current status, parallel tracks, critical path
- **PHASE1_TASKS.md** - Detailed Phase 1 breakdown with PHASE1-X-X labels
- **SECURITY_ROADMAP_INTEGRATION.md** - Security audit findings & integration

### /tasks Folder (Operational Tracking):
- **tasks/README.md** - Task coordination system (updated for PHASE1-X-X)
- **tasks/backend.md** - Legacy TASK-XXX for reference (Phase 1-8)
- **tasks/content.md** - Content tasks
- **tasks/frontend.md** - Frontend tasks
- **tasks/infrastructure.md** - DevOps & deployment
- **tasks/phase1/** - Phase 1 agent-based breakdown (new)
  - `database.md` - PHASE1-A-1 subtasks (Maryam)
  - `api.md` - PHASE1-B-1 subtasks (Jodha)
  - `security.md` - PHASE1-C-1 subtasks (Noor)

### GitHub Issues:
- **#5** - PHASE1-A-1: Database Schema & Models
- **#6** - PHASE1-B-1: FastAPI REST API Implementation
- **#7** - PHASE1-C-1: Security Hardening (BLOCKS Phase 3)

---

## Transition Plan (After Phase 1)

Once Phase 1 is complete:
1. Mark all PHASE1-X-X issues as complete
2. Merge PHASE1_TASKS.md completion data back to legacy TASK system
3. Keep PHASE1_TASKS.md as historical record (not deleted)
4. Phase 2+ will use hybrid approach if parallel agents continue
5. Eventually consolidate into single system for clarity

---

## Examples

### Developer Workflow:

**Maryam (Database):**
```
GitHub Issue #5: PHASE1-A-1
└── PHASE1-A-1.1 ✓
└── PHASE1-A-1.2 (in progress)
└── PHASE1-A-1.3
└── PHASE1-A-1.4
└── PHASE1-A-1.5

References:
- PHASE1_TASKS.md (Section 1: Agent A)
- tasks/phase1/database.md
- openspec/changes/dars/tasks.md (TASK-001, TASK-002, TASK-005)
```

**Status Updates (Daily):**
```
GitHub Issue #5 comment:
"PHASE1-A-1.2 complete - all 6 models created with relationships
Next: PHASE1-A-1.3 (Alembic migration)
Notify Jodha when PHASE1-A-1.1 done so he can start PHASE1-B-1.2"
```

### Manager Dashboard:

```
Phase 1 Status (Week 1)

Track A (Maryam): PHASE1-A-1
  PHASE1-A-1.1 ✓ (complete)
  PHASE1-A-1.2 ✓ (complete)
  PHASE1-A-1.3 (in progress)
  PHASE1-A-1.4
  PHASE1-A-1.5

Track B (Jodha): PHASE1-B-1 [depends on A.1]
  PHASE1-B-1.1
  PHASE1-B-1.2
  PHASE1-B-1.3
  PHASE1-B-1.4
  PHASE1-B-1.5
  PHASE1-B-1.6 [blocks Phase 3]

Track C (Noor): PHASE1-C-1 [BLOCKS Phase 3]
  PHASE1-C-1.1
  PHASE1-C-1.2
  ...
  PHASE1-C-1.9 [code review required]

Critical Path: PHASE1-C-1.9 (must be 100% complete before Phase 3)
```

---

## Notes

- Legacy TASK system is preserved in openspec/ for archival and Phase 2+ planning
- PHASE1-X-X system is optimized for Phase 1 parallel execution
- Both systems complement each other - they are not in conflict
- After Phase 1, review if hybrid approach should continue for Phase 2
- Security requirements (SEC-001-008) are new and only appear in PHASE1-C-1

---

**Document Status:** ✅ Active
**Last Updated:** 2026-01-30
**Maintained By:** Project Coordinator
