# Phase 3 Task Naming & Mapping

This document maps PHASE3-X-X agent tasks to legacy TASK-XXX numbers from `openspec/changes/dars/tasks.md`, shows parallel track ownership, and identifies which tasks can execute concurrently.

---

## Overview

**Two Naming Systems (Consistent with Phase 1 approach):**

1. **Legacy System (TASK-XXX):** Used in `openspec/changes/dars/tasks.md` — overall project roadmap
2. **Agent System (PHASE3-X-X):** Agent-centric breakdown for parallel Phase 3 execution

**Three Parallel Tracks:**
- **Track A (Maryam):** Database — migration, seed script, repositories (DAOs)
- **Track B (Jodha):** API/Services — selection algorithm, evaluator, wire endpoints, Telegram wiring
- **Track C (Noor):** Security/Observability — session ownership, logging, cost tracking

---

## Phase 3 Mapping: TASK-XXX → PHASE3-X-X

### Track A: Database (Maryam)

| PHASE3 Label | Legacy TASK | Description | Can Start Day |
|---|---|---|---|
| PHASE3-A-1.1 | TASK-002 (migrations) | Add answer_type, tolerance, MC options columns to problems | Day 1 |
| PHASE3-A-1.2 | TASK-002 (models) | Update src/models/problem.py with new fields | Day 1 |
| PHASE3-A-1.3 | TASK-005 (seeding) | Create scripts/seed_problems.py YAML loader | Day 1 |
| PHASE3-A-1.4 | TASK-005 (seeding) | Idempotent seed: (grade, topic, question_en) uniqueness | Day 1 |
| PHASE3-A-1.5 | TASK-005 (seeding) | Idempotency + CLI: --dry-run, --grade flags | Day 1 |
| PHASE3-A-1.6 | TASK-005 (testing) | Unit tests for YAML loader (≥80% coverage) | Day 1 |
| PHASE3-A-1.7 | TASK-002 (verify) | Verify seed: SELECT COUNT(*) = 280 | Day 2 |
| PHASE3-A-2.1 | TASK-003 (data layer) | src/repositories/problem_repository.py | Day 3 |
| PHASE3-A-2.2 | TASK-003 (data layer) | src/repositories/session_repository.py | Day 3 |
| PHASE3-A-2.3 | TASK-003 (data layer) | src/repositories/response_repository.py | Day 3 |
| PHASE3-A-2.4 | TASK-003 (data layer) | src/repositories/__init__.py exports all three | Day 3 |
| PHASE3-A-2.5 | TASK-003 (testing) | Unit + integration tests ≥80% coverage | Day 3-4 |

**Duration:** ~3.5 days total (A-1: 2 days, A-2: 1.5 days)
**Blocks:** PHASE3-B-2 (evaluator needs answer_type), PHASE3-B-3 (endpoints need repos)

---

### Track B: API & Services (Jodha)

| PHASE3 Label | Legacy TASK | Description | Can Start Day |
|---|---|---|---|
| PHASE3-B-1.1 | TASK-008 | src/services/problem_selector.py — ProblemSelector class | Day 1 |
| PHASE3-B-1.2 | TASK-008 | 50/30/20 scoring: recency, mastery, difficulty variation | Day 1 |
| PHASE3-B-1.3 | TASK-008 | Determinism: tie-breaking by problem_id ASC | Day 1 |
| PHASE3-B-1.4 | TASK-008 | Edge cases: new student, sparse grade, all mastered | Day 2 |
| PHASE3-B-1.5 | TASK-008 | Unit tests with mocked repos ≥80% coverage | Day 2-3 |
| PHASE3-B-1.6 | TASK-008 | Performance: <500ms validated | Day 3 |
| PHASE3-B-2.1 | TASK-003 | src/services/answer_evaluator.py — AnswerEvaluator class | Day 4 |
| PHASE3-B-2.2 | TASK-003 | Numeric ±5% tolerance evaluation | Day 4 |
| PHASE3-B-2.3 | TASK-003 | Multiple choice exact index match | Day 4 |
| PHASE3-B-2.4 | TASK-003 | Input normalisation: ₹, commas, trailing units | Day 4 |
| PHASE3-B-2.5 | TASK-003 | Confidence level from hints_used | Day 4 |
| PHASE3-B-2.6 | TASK-003 | Bilingual feedback (EN + BN) | Day 4-5 |
| PHASE3-B-2.7 | TASK-003 | Unit tests ≥80% coverage | Day 4-5 |
| PHASE3-B-3.1 | TASK-001, TASK-007 | GET /practice — real selection + session creation | Day 5 |
| PHASE3-B-3.2 | TASK-001, TASK-003 | POST /practice/{id}/answer — real evaluation + persist | Day 5-6 |
| PHASE3-B-3.3 | TASK-001, TASK-015 | POST /practice/{id}/hint — pre-written hint from DB | Day 5-6 |
| PHASE3-B-3.4 | TASK-007 | Session resume: reconnect continues from last problem | Day 6 |
| PHASE3-B-3.5 | TASK-007 | Session expiry: stale auto-abandoned on next /practice | Day 6 |
| PHASE3-B-3.6 | TASK-001 | "Already completed today" response | Day 6 |
| PHASE3-B-3.7 | TASK-021 | Feedback language follows student.language (BN/EN) | Day 6 |
| PHASE3-B-3.8 | TASK-001 | Integration tests ≥70% coverage on practice.py | Day 6-7 |
| PHASE3-B-4.1 | TASK-014 | Wire /practice Telegram command → GET /practice | Day 7 |
| PHASE3-B-4.2 | TASK-014 | In-memory session state: `_active_sessions: dict[int, dict]` | Day 7 |
| PHASE3-B-4.3 | TASK-014 | Free-text answer handler → POST /practice/{id}/answer | Day 7 |
| PHASE3-B-4.4 | TASK-014 | /hint command handler → POST /practice/{id}/hint | Day 7 |
| PHASE3-B-4.5 | TASK-014 | Bilingual Telegram responses + score summary on completion | Day 7 |
| PHASE3-B-4.6 | TASK-014 | Smoke test: live Telegram bot sends /practice and answers | Day 8 |

**Duration:** ~7.5 days total (B-1: 2.5d, B-2: 1.5d, B-3: 2d, B-4: 1.5d)
**Blocked by:** B-2 needs A-1 (answer_type); B-3 needs A-2 (repos) + B-1 + B-2; B-4 needs B-3 complete

---

### Track C: Security & Observability (Noor)

| PHASE3 Label | Legacy TASK | Description | Can Start Day |
|---|---|---|---|
| PHASE3-C-1.1 | TASK-019 (auth) | src/auth/session.py — verify_session_owner() dependency | Day 5 |
| PHASE3-C-1.2 | TASK-019 (auth) | verify_problem_in_session() guard | Day 5 |
| PHASE3-C-1.3 | TASK-019 (auth) | Wire both answer + hint endpoints with ownership Depends | Day 5-6 |
| PHASE3-C-1.4 | TASK-019 (auth) | Expired session → HTTP 410 Gone | Day 5 |
| PHASE3-C-1.5 | TASK-019 (security) | IDOR attempt → WARNING log with hashed student IDs | Day 5 |
| PHASE3-C-1.6 | TASK-019 (testing) | Security tests: IDOR, expired, completed, wrong problem | Day 5-6 |
| PHASE3-C-2.1 | TASK-020 (logging) | 5 structured log events across all practice endpoints | Day 6 |
| PHASE3-C-2.2 | TASK-020 (logging) | student_answer never logged | Day 6 |
| PHASE3-C-2.3 | TASK-020 (logging) | telegram_id logged as SHA-256 hash only | Day 6 |
| PHASE3-C-2.4 | TASK-020 (testing) | Unit tests verify log format and PII absence | Day 6 |
| PHASE3-C-3.1 | TASK-029 (cost) | src/services/cost_tracker.py — CostTracker stub | Day 6-7 |
| PHASE3-C-3.2 | TASK-029 (cost) | request_hint endpoint calls record_hint_cost() | Day 6-7 |
| PHASE3-C-3.3 | TASK-029 (cost) | Every hint → CostRecord with cost_usd=0.00 | Day 6-7 |
| PHASE3-C-3.4 | TASK-029 (cost) | check_budget_alert() warns at >$0.10/student/month | Day 7 |
| PHASE3-C-3.5 | TASK-029 (testing) | Unit tests ≥80% coverage | Day 7 |

**Duration:** ~3.5 days active work (Noor prepares scaffolding Days 1-3 while waiting for B-3)
**Blocked by:** C-1 and C-2 need PHASE3-B-3 complete; C-3 wires into B-3.3 (hint endpoint)

---

## Parallel Execution Map with Integration Checkpoints

```
             DAY 1      DAY 2      DAY 3      DAY 4      DAY 5      DAY 6      DAY 7      DAY 8
MARYAM  ┌─ A-1.1 ─┬─ A-1.2 ─┬─ A-2.1 ─┬─ A-2.2 ─┐
        │  A-1.3  │  A-1.4  │  A-2.3  │  A-2.5  │
        │  A-1.5  │  A-1.6  │  A-2.4  │         │
        └─────────┴─────────┴─────────┴─────────┘
                      ↑                     ↑
                     CP1                   CP3

JODHA   ┌─ B-1.1 ─┬─ B-1.2 ─┬─ B-1.3 ──────────┬─ B-2.1 ─┬─ B-3.1 ─┬─ B-3.2 ─┬─ B-4.1 ─┐
        │         │         │   B-1.4  B-1.5     │  B-2.2  │  B-3.3  │  B-3.4  │  B-4.2  │
        │         │         │   B-1.6            │  B-2.3  │  B-3.8  │  B-3.5  │  B-4.3  │
        │         │         │                    │  B-2.4  │         │  B-3.6  │  B-4.4  │
        └─────────┴─────────┴────────────────────┴─────────┴─────────┴─────────┴─────────┘
                                ↑                               ↑           ↑         ↑
                               CP2                             CP4         CP4       CP5
                                                (waits for A-1, A-2)

NOOR    ┌─ Design Review ──────────────────────────────────┬─ C-1.1 ─┬─ C-2.1 ─┐
        │  Test scaffolding                               │  C-1.2  │  C-3.1  │
        │  Review B-1 algorithm                           │  C-1.3  │  C-3.2  │
        │  Prepare security test fixtures                 │  C-1.6  │  C-2.4  │
        └─────────────────────────────────────────────────┴─────────┴─────────┘
                                                            (waits for B-3)
                                                                          ↑
                                                                         CP5

JAHANARA┌─ Grade 8 content (parallel, independent) ────────────────────────────────────────┐
        │  mensuration, geometry, data_handling, rational_numbers (10 problems each, BN+EN) │
        └───────────────────────────────────────────────────────────────────────────────────┘
```

---

## Integration Checkpoints

Each checkpoint is a formal go/no-go gate. Work on dependent tasks must not start until the checkpoint passes.

### CP1 — End of Day 2: Seed Verified ✅

**Owner:** Maryam
**Gate condition:** `SELECT COUNT(*) FROM problems` returns 280
**Tests that must pass:**
- `python scripts/seed_problems.py --dry-run` exits 0 with no errors
- `python scripts/seed_problems.py` loads all YAML files idempotently
- Re-running seed produces no duplicates (idempotency test)
- `answer_type` column exists and is populated on all 280 rows

**Unblocks:** PHASE3-B-2 (Jodha can start AnswerEvaluator)

---

### CP2 — End of Day 3: ProblemSelector Validated ✅

**Owner:** Jodha
**Gate condition:** ProblemSelector unit test suite passes at ≥80% coverage
**Tests that must pass:**
- `pytest tests/unit/test_problem_selector.py -v` — all pass
- Determinism test: same inputs → same 5 problems returned
- Edge case: new student with no history → 5 problems selected without error
- Edge case: sparse grade (< 5 problems in DB for a grade) → graceful fallback
- Performance: `select_problems()` completes in <500ms with mocked repos

**Unblocks:** Noor can begin reviewing B-1 scoring logic for security/fairness concerns

---

### CP3 — End of Day 4: Repositories Integrated ✅

**Owner:** Maryam
**Gate condition:** Repository layer integration tests pass against test DB
**Tests that must pass:**
- `pytest tests/integration/test_repositories.py -v` — all pass
- `from src.repositories import ProblemRepository, SessionRepository, ResponseRepository` — no import errors
- `ProblemRepository.get_by_grade(grade=7)` returns correct subset
- `SessionRepository.create()` and `SessionRepository.get_active()` round-trip correctly
- `ResponseRepository.record()` persists answer with correct student_id/session_id/problem_id

**Also required at CP3:**
- B-2 (AnswerEvaluator) unit tests pass (Jodha): numeric tolerance, MC exact match, bilingual feedback
- `pytest tests/unit/test_answer_evaluator.py -v` — all pass

**Unblocks:** PHASE3-B-3 (Jodha can wire real endpoints); PHASE3-C-1 (Noor can build ownership checks)

---

### CP4 — End of Day 6: Full Practice Flow via REST ✅

**Owner:** Jodha (sign-off from Maryam + Noor)
**Gate condition:** All 3 practice endpoints return real data end-to-end
**Tests that must pass:**
- `pytest tests/integration/test_practice_flow.py -v` — all pass (≥70% coverage)
- `GET /practice` → returns 5 real problems from DB, creates session record
- `POST /practice/{id}/answer` → evaluates, persists response, returns bilingual feedback
- `POST /practice/{id}/hint` → returns pre-written hint from DB (not Claude stub)
- Session resume: calling `GET /practice` mid-session reconnects to existing session
- Session expiry: stale session auto-abandoned on next `GET /practice`
- "Already completed today" guard returns correct response

**Security check (Noor):**
- `verify_session_owner` wired to answer + hint endpoints
- IDOR test: student B cannot answer on student A's session → 403 Forbidden
- Expired session → 410 Gone

**Unblocks:** PHASE3-B-4 (Telegram wiring); PHASE3-C-2 (logging); PHASE3-C-3 (cost stubs)

---

### CP5 — End of Day 7-8: Phase 3 Complete ✅

**Owner:** All three agents (joint sign-off)
**Gate condition:** Telegram bot demo works + all security/observability in place
**Tests that must pass:**
- `pytest tests/ -v --cov=src --cov-fail-under=70` — full suite passes
- Telegram smoke test: real bot receives `/practice`, sends answer, gets bilingual feedback
- IDOR blocked at Telegram layer (session state tied to telegram_id)
- No PII in logs: grep for telegram_id raw value returns empty
- `student_answer` never appears in any log line
- CostTracker records hint cost (cost_usd=0.00) for every hint served
- Budget alert test: mock student with >$0.10/month triggers WARNING log

**Go/No-Go Decision:** Phase 3 demo can proceed only after CP5 passes. If CP5 fails, triage by track and re-run failed checkpoints.

---

## What Can Run In Parallel (Day 1)

| Task | Owner | Why no dependency |
|---|---|---|
| PHASE3-A-1 (migration + seed) | Maryam | Pure DB work, no service code needed |
| PHASE3-B-1 (problem selector) | Jodha | Only needs Problem model (already exists); can mock repos |
| Noor design review | Noor | Reviews B-1 algorithm, writes test fixtures, no code to block on |
| Jahanara Grade 8 content | Jahanara | Independent YAML authoring, no code dependency |

**First hard dependency:** PHASE3-B-2 (evaluator) cannot start until CP1 delivers
the `answer_type` column on the Problem model. Expected: end of Day 2.

**Second hard dependency:** PHASE3-B-3 (wire endpoints) cannot start until CP3 passes
(A-2 repos + B-2 evaluator both complete). Expected: start of Day 5.

**Track C unblocked:** C-1, C-2, C-3 start immediately after CP4. Expected: Day 6-7.

**PHASE3-B-4 unblocked:** Telegram wiring starts after CP4 (REST endpoints working). Expected: Day 7.

---

## Handoff Points Between Agents

| From | To | Handoff | Checkpoint |
|---|---|---|---|
| Maryam (A-1) | Jodha (B-2) | `answer_type` on Problem model, migration applied, 280 rows seeded | **CP1** (End Day 2) |
| Jodha (B-1) | Noor | ProblemSelector tests pass, algorithm reviewable | **CP2** (End Day 3) |
| Maryam (A-2) | Jodha (B-3) | `from src.repositories import SessionRepository` works; integration tests pass | **CP3** (End Day 4) |
| Jodha (B-3) + Noor (C-1) | All | Practice endpoints wired + session ownership enforced | **CP4** (End Day 6) |
| Jodha (B-4) + Noor (C-2/C-3) | Demo | Telegram bot working + logging + cost stubs all live | **CP5** (End Day 7-8) |

---

## Legacy TASK-XXX Cross-Reference

| Legacy TASK | Description | Phase 3 Coverage |
|---|---|---|
| TASK-001 | Daily Practice Sessions | PHASE3-B-3.1, B-3.2, B-3.6 |
| TASK-002 | Database Schema | PHASE3-A-1.1, A-1.2 |
| TASK-003 | Answer Evaluation | PHASE3-B-2 (full), PHASE3-A-2.3 |
| TASK-005 | Content/Seed | PHASE3-A-1.3, A-1.4, A-1.5 |
| TASK-007 | Session State Persistence | PHASE3-B-3.4, B-3.5, PHASE3-A-2.2 |
| TASK-008 | Problem Selection Algorithm | PHASE3-B-1 (full) |
| TASK-014 | Telegram Bot Commands | PHASE3-B-4 (full — /practice wiring) |
| TASK-015 | Claude Hint Generation | ⚠️ DEFERRED to Phase 4 — stub only in C-3 |
| TASK-019 | Authentication & Security | PHASE3-C-1 (full) |
| TASK-020 | Logging & Observability | PHASE3-C-2 (full) |
| TASK-021 | Bengali Localisation | PHASE3-B-3.7 (feedback language) |
| TASK-029 | Cost Tracking | PHASE3-C-3 (stub, full in Phase 5) |

---

## Additional Skills Assessment

### Agents Available for Phase 3

| Agent | Role | Phase 3 Contribution |
|---|---|---|
| **Maryam** | Database & ORM | Track A — migration, seed, repositories |
| **Jodha** | FastAPI Backend | Track B — services, algorithm, wire endpoints, Telegram wiring |
| **Noor** | Security & Logging | Track C — IDOR, observability, cost stubs |
| **Jahanara** | Content | Grade 8 YAML expansion (parallel, independent) |

### Skill Gaps: Resolved

---

#### Gap 1: Algorithm / Learning Science Review ✅ RESOLVED

**Decision:** Algorithm weights (50% recency / 30% mastery / 20% difficulty) **confirmed for MVP**.
No human education expert review required before Phase 3. Weights can be tuned post-pilot using
real student performance data from the 8-week run.

**Rationale:** The weights are reasonable pedagogical heuristics (topic recency prevents drill fatigue,
mastery reinforcement is standard spaced repetition, difficulty variation maintains engagement). The
50-student pilot will generate the data needed to validate or adjust them empirically.

---

#### Gap 2: Integration Testing ✅ RESOLVED

**Decision:** Integration checkpoints (CP1–CP5) are distributed throughout Phase 3 (not just at the end).
Jodha owns `tests/integration/test_practice_flow.py`. Maryam owns `tests/integration/test_repositories.py`.
Noor owns security tests in `tests/unit/test_session_auth.py`.

Each checkpoint is a blocking go/no-go gate. This eliminates the "integration failure only caught at demo" risk.

---

#### Gap 3: Grade 8 Content ✅ IN PROGRESS (Jahanara)

**Decision:** Jahanara running in parallel with Phase 3 tracks to expand Grade 8 content.
Target: add mensuration, geometry, data_handling, rational_numbers (10 problems each, all bilingual).
No wait for human review — `bn_reviewed: false` flag maintains audit trail.

**Status:** ✅ ALL FOUR FILES COMPLETE
- `grade_8/mensuration.yaml` — 10 problems (cubes, cuboids, cylinders)
- `grade_8/geometry.yaml` — 10 problems (Pythagoras theorem)
- `grade_8/data_handling.yaml` — 10 problems (probability, answer_type: text)
- `grade_8/rational_numbers.yaml` — 10 problems (fractions, operations)

Total problem count: **320 problems** (280 minimum met + 40 Grade 8 bonus content)

---

#### Gap 4: Telegram Bot Command Wiring ✅ RESOLVED — PHASE3-B-4 Added

**Decision:** PHASE3-B-4 added to Jodha's track. Starts Day 7 after CP4.
Uses in-memory session state (`_active_sessions: dict[int, dict]`) for 50-student pilot.
Wires `/practice` command, free-text answer handling, `/hint` command.
Bilingual Telegram responses + score summary on session completion.

---

### Summary: Skills Needed to Complete Phase 3

| Need | Agent/Person | Priority | Status |
|---|---|---|---|
| Maryam — Track A | Available | Critical | Ready |
| Jodha — Track B | Available | Critical | Ready |
| Noor — Track C | Available | Critical | Ready |
| Algorithm weights decision | ✅ Confirmed for MVP | High | Done |
| Jahanara — Grade 8 content | Running in parallel | High | In Progress |
| Telegram /practice wiring | Jodha (PHASE3-B-4) | Medium | Scoped |
| Integration checkpoints | CP1–CP5 distributed across Phase 3 | Medium | Done |
