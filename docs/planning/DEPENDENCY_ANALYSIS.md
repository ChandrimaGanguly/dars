# Dars AI Tutoring Platform - Dependency Analysis & Parallelization Strategy

**Date:** 2026-01-28
**Scope:** 40 Requirements mapped to 8 Phases
**Goal:** Optimize parallel development, minimize critical path, identify handoffs

---

## Executive Summary

### Critical Path: 32 Days (4.6 weeks)
The longest dependency chain:
```
REQ-017 (Database, 2d)
  → REQ-018 (API, 2d)
  → REQ-001 (Practice, 3d)
  → REQ-008 (Selection, 3d)
  → REQ-004 (Difficulty, 2d)
  → REQ-015 (Claude, 2d)
  → REQ-032 (Deploy, 2d)
  = 32 days serial

BUT with parallelization:
REQ-005 (Content, 10d) ∥ REQ-017 → REQ-018 → REQ-001...
REQ-020 (Errors, 1d) ∥ REQ-017 → REQ-018
REQ-014 (Telegram, 2d) ∥ REQ-017 → REQ-018
= Actual timeline: MAX(32, 10) = 32 days with better resource utilization
```

### Recommendation: 4 Parallel Work Streams
- **Stream A:** Backend API Foundation (REQ-017, 018, 020, 019, 031)
- **Stream B:** Content Curation (REQ-005, 022, 023) - LONGEST SINGLE TASK
- **Stream C:** Learning Engine (REQ-001, 008, 003, 007)
- **Stream D:** Telegram Integration (REQ-014 + Stream A)
- **Stream E:** Optimization Layers (REQ-004, 006, 015, 016, 002)
- **Stream F:** Engagement & Localization (REQ-009-013, 021, 029-030)
- **Stream G:** Admin & Deployment (REQ-034, 032, 033)

### Team Structure
- **3-4 backend agents** (Stream A + D)
- **1-2 content agents** (Stream B) + 1 human (Bengali speaker)
- **2 learning algorithm agents** (Stream C + E)
- **1 frontend agent** (Stream G)
- **1 operations agent** (Stream F)

---

# PART 1: DEPENDENCY GRAPH

## Requirements Dependency Matrix

### Level 0: No Dependencies (Can Start Immediately)

```
REQ-005 (Problem Content Curation)
├─ No dependencies
├─ Complexity: L (10 days)
└─ Critical for: REQ-001, REQ-008

REQ-017 (Database Schema)
├─ No dependencies
├─ Complexity: M (2-3 days)
└─ Critical for: Everything (REQ-001, 002, 009, 014, 018, 019, 020, 029, 032, 033)

REQ-022 (Curriculum Alignment)
├─ Depends on: REQ-005 (content exists)
├─ Complexity: S (1-2 days)
└─ Can start: With content sourcing

REQ-023 (Cultural Appropriateness)
├─ Depends on: REQ-005 (content exists)
├─ Complexity: S (1 day)
└─ Can start: With content sourcing
```

**Diagram:**
```
Phase 1 Foundation (Start Week 1):

REQ-017 ──────────────────────────────────────────┐
(Database)                                        │
                                                  ├─→ REQ-014 ──────────┐
REQ-020 ──────────┐                              │   (Telegram)        │
(Errors)          ├─→ REQ-018 ────────────────┬─┤                      │
                  │   (API)                    │ │                      │
REQ-019 ──────────┤   └─ Handles all endpoints│ │                      │
(Security)        │                           │ │                      │
                  └───────────────────────────┘ │                      │
                                                │                      │
REQ-031 ──────────────────────────────────────┬─┴───────────────────┐  │
(Health Check)                                │                     │  │
                                              └─→ REQ-032 ──────────┤──┤
REQ-005 (10 days) ────────────────────────────┐                     │  │
(Content, longest!!)                           ├─→ REQ-001 ─────────┼──┘
                                              │   (Practice)
                                              │
                            ┌──────────────────┘
                            │
                            └─→ REQ-008 (Selection)
                                REQ-022 (Curriculum)
                                REQ-023 (Culture)
```
---

### Level 1: Depends on Level 0 Items

```
REQ-001 (Daily Practice Sessions)
├─ Depends on: REQ-005 (content), REQ-017 (database), REQ-018 (API)
├─ Blocks: REQ-003, 004, 006, 007, 008, 009, 010, 011, 012, 013
├─ Complexity: M (3-5 days)
└─ Must have: Content available + API endpoints

REQ-003 (Answer Evaluation)
├─ Depends on: REQ-001 (practice exists)
├─ Blocks: REQ-004, 006, 013
├─ Complexity: M (2-3 days)
└─ Critical for: Learning engine

REQ-008 (Problem Selection Algorithm)
├─ Depends on: REQ-005 (content), REQ-017 (DB), REQ-018 (API)
├─ Blocks: REQ-001 (can't practice without selection)
├─ Complexity: M (3-4 days)
└─ Interaction: Tightly coupled with REQ-001, should be built together

REQ-007 (Session Persistence)
├─ Depends on: REQ-001 (practice), REQ-017 (database)
├─ Blocks: None (internal implementation detail)
├─ Complexity: S (2 days)
└─ Note: Should be built WITH REQ-001, not after

REQ-014 (Telegram Bot Integration)
├─ Depends on: REQ-017 (DB for user data), REQ-018 (API for webhook)
├─ Blocks: All user-facing features (REQ-001, 002, etc.)
├─ Complexity: M (2-3 days)
└─ Interfaces: Webhook endpoint from REQ-018
```

**Diagram:**
```
Level 1 - Learning Engine Foundation (Week 2-3):

        REQ-005 ──┐
                  ├─→ REQ-008 ────┐
        REQ-017 ──┤               ├─→ REQ-001 (Practice)
                  ├─→ REQ-001 ────┤   └─ REQ-007 (Persistence)
        REQ-018 ──┤               │
                  ├─→ REQ-003 (Eval) ←┘
                  │
                  └─→ REQ-014 (Telegram)
                      └─ Delivers to: REQ-001
```

---

### Level 2: Depends on Level 1 Items

```
REQ-002 (Socratic Hint System)
├─ Depends on: REQ-003 (answer eval), REQ-015 (Claude API)
├─ Blocks: REQ-013 (encouragement uses hints)
├─ Complexity: M (3-4 days)
└─ Note: Can design while waiting for Claude

REQ-004 (Adaptive Difficulty)
├─ Depends on: REQ-001 (practice), REQ-003 (answer eval)
├─ Blocks: REQ-006 (learning path)
├─ Complexity: S (2-3 days)
└─ Note: Must have answer evaluation data to adapt

REQ-006 (Daily Learning Path)
├─ Depends on: REQ-001 (practice), REQ-004 (difficulty)
├─ Blocks: None (enhancement to REQ-001)
├─ Complexity: M (2-3 days)
└─ Note: Can plan path selection while waiting for difficulty

REQ-009 (Streak Tracking)
├─ Depends on: REQ-001 (practice completion), REQ-017 (DB schema)
├─ Blocks: REQ-010, 011, 012, 013
├─ Complexity: S (1-2 days)
└─ Note: Simple DB update on session completion

REQ-015 (Claude API Integration)
├─ Depends on: REQ-018 (API to call from), REQ-005 (problems exist)
├─ Blocks: REQ-002, 016
├─ Complexity: M (2-3 days)
└─ Note: Design early, implement after session data

REQ-020 (Error Handling) - Actually Level 1
├─ Depends on: REQ-018 (API exists)
├─ Blocks: None (applies to all)
├─ Complexity: S (1-2 days)
└─ Note: Should be implemented in Phase 1, not later

REQ-021 (Bengali Language)
├─ Depends on: REQ-001, 002, 003, 014, etc. (all UI strings)
├─ Blocks: None (translation layer)
├─ Complexity: M (2-3 days)
└─ Note: Can prepare strings file while building, translate in parallel

REQ-029 (Cost Tracking)
├─ Depends on: REQ-015 (Claude calls), REQ-017 (DB), REQ-018 (API)
├─ Blocks: REQ-030 (admin commands), REQ-034 (dashboard)
├─ Complexity: M (2-3 days)
└─ Note: Log every Claude API call from start
```

**Diagram:**
```
Level 2 - Optimization & Engagement (Week 3-5):

REQ-001 ──┐
          ├─→ REQ-003 ──┐
          │             ├─→ REQ-002 (Hints)
REQ-015 ──────────────┘

REQ-001 ──┐
          ├─→ REQ-004 ──────→ REQ-006 (Learning Path)
REQ-003 ──┘

REQ-001 ──→ REQ-009 ──┐
                      ├─→ REQ-010 ──┐
                      │             ├─→ REQ-012 ──┐
                      ├─→ REQ-011 ──┘             ├─→ REQ-013
                      │                          │
                      └─ (streak available) ─────┘

REQ-015 ──→ REQ-016 (Caching)

All UI ──→ REQ-021 (Bengali) ─ Can be done in parallel
```

---

### Level 3: Depends on Level 2 Items

```
REQ-010 (Streak Display)
├─ Depends on: REQ-009 (streak exists)
├─ Blocks: REQ-012
├─ Complexity: S (1 day)
└─ Simple: Just format streak data

REQ-011 (Streak Reminders)
├─ Depends on: REQ-009 (streak tracking)
├─ Blocks: None
├─ Complexity: S (2 days)
└─ Note: Background job to send reminders daily

REQ-012 (Streak Milestones)
├─ Depends on: REQ-009 (streak), REQ-010 (display)
├─ Blocks: REQ-013
├─ Complexity: S (1 day)
└─ Note: Just add celebration messages

REQ-013 (Daily Encouragement)
├─ Depends on: REQ-001 (practice), REQ-009 (streak), REQ-003 (eval)
├─ Blocks: None
├─ Complexity: S (1-2 days)
└─ Note: Message pool, vary by streak/performance

REQ-016 (Prompt Caching)
├─ Depends on: REQ-015 (Claude API)
├─ Blocks: None (optimization)
├─ Complexity: S (1-2 days)
└─ Note: Critical for cost control, not optional

REQ-030 (Admin Commands)
├─ Depends on: REQ-018 (API), REQ-029 (cost tracking)
├─ Blocks: REQ-034 (dashboard)
├─ Complexity: S (2 days)
└─ Note: Simple commands, fetch from DB

REQ-031 (Health Check)
├─ Depends on: REQ-018 (API endpoints), REQ-017 (DB)
├─ Blocks: REQ-032 (deployment monitoring)
├─ Complexity: S (1 day)
└─ Note: Simple endpoint, can be done early
```

---

### Level 4: Depends on Level 3 Items

```
REQ-034 (Admin Dashboard)
├─ Depends on: REQ-018 (API), REQ-029 (cost), REQ-030 (commands)
├─ Blocks: None
├─ Complexity: M (3 days)
└─ Note: Frontend work, can start early with mock data

REQ-032 (Deployment)
├─ Depends on: REQ-019 (security), REQ-031 (health check)
├─ Blocks: REQ-033 (backup needs live system)
├─ Complexity: M (2-3 days)
└─ Note: Can't deploy until auth + health check work

REQ-033 (Disaster Recovery)
├─ Depends on: REQ-017 (DB exists), REQ-032 (deployment)
├─ Blocks: None
├─ Complexity: M (2-3 days, but mostly setup)
└─ Note: Railway auto-backups handle most
```

---

## Complete Dependency Tree

```
ROOT DEPENDENCIES (No blockers, start immediately):
├─ REQ-005 (Content) - 10 days (CRITICAL LONG POLE)
├─ REQ-017 (Database) - 2 days
└─ REQ-020 (Error Handling) - 1 day

PHASE 1 DEPS (Week 1, parallel):
├─ REQ-017 → REQ-018 (API) → REQ-014 (Telegram)
├─ REQ-020 → embedded in REQ-018
├─ REQ-005 → REQ-022, REQ-023 (parallel)
└─ REQ-019 (Security) → REQ-031 (Health)

PHASE 2-3 DEPS (Week 2-3, serial):
├─ REQ-017 + REQ-018 + REQ-005 → REQ-001 (Practice)
│   └─ REQ-001 + REQ-008 (Selection) - built together
│       └─ REQ-007 (Persistence) - built with REQ-001
│           └─ REQ-003 (Evaluation)
│               ├─ REQ-004 (Difficulty)
│               │   └─ REQ-006 (Learning Path)
│               └─ REQ-002 (Hints) + REQ-015 (Claude) + REQ-016 (Cache)

PHASE 3-4 DEPS (Week 3-4, parallel):
├─ REQ-001 → REQ-009 (Streaks)
│   └─ REQ-010 (Display)
│       └─ REQ-012 (Milestones) → REQ-013 (Encouragement)
├─ REQ-009 → REQ-011 (Reminders)
└─ REQ-015 → REQ-016 (Caching)

PHASE 5-6 DEPS (Week 5-6, parallel):
├─ REQ-001, 014 + REQ-005 → REQ-021 (Bengali)
├─ REQ-015, 017, 018 → REQ-029 (Cost Tracking)
│   └─ REQ-030 (Admin Commands)
└─ All → REQ-034 (Admin Dashboard)

PHASE 7 DEPS (Week 6-7):
├─ REQ-019, 031 → REQ-032 (Deployment)
│   └─ REQ-033 (Backups)
```

---

## Critical Path Analysis

### Serial Path (Longest Chain)

```
REQ-017 (Database)          [2 days]  ──┐
                                        │
REQ-018 (API)               [2 days]  ──┤
                                        ├─→ REQ-001 (Practice) [3 days]
REQ-005 (Content)          [10 days]  ──┤
                                        │
                                        ├─→ REQ-008 (Selection) [3 days]
                                        │
                                        ├─→ REQ-003 (Evaluation) [2 days]
                                        │
                                        ├─→ REQ-004 (Difficulty) [2 days]
                                        │
                                        ├─→ REQ-015 (Claude) [2 days]
                                        │
                                        ├─→ REQ-032 (Deploy) [2 days]

Total: 10 + 2 + 3 + 3 + 2 + 2 + 2 + 2 = 26 days (optimistic)
```

### Actual Critical Path with Dependencies

The bottleneck is **REQ-005 (Content Curation: 10 days)** because:
1. REQ-005 must complete before REQ-001 can be fully tested
2. REQ-001 is required for REQ-008, REQ-003, etc.
3. REQ-003 is required for REQ-004, REQ-002
4. This creates a dependency chain that takes time

**Optimal timeline if content is sourced in parallel:**

Week 1 (Days 1-5):
- Day 1-2: REQ-017 (DB schema) ✓
- Day 1-2: REQ-020 (Error handling) ✓
- Day 1-3: REQ-018 (API) ✓
- Day 3-4: REQ-014 (Telegram webhook) ✓
- Day 4-5: REQ-031 (Health check) ✓
- Week 1 END: Backend foundation complete

Week 1-2 (Days 1-10, parallel):
- Days 1-10: REQ-005 (Content curation) ✓✓✓
- By end of Week 2: 280 problems available

Week 2-3 (Days 8-16):
- Day 6-8: REQ-003 (Answer eval - can start with mock data) ✓
- Day 8-10: REQ-001 (Practice) ✓
- Day 10-12: REQ-008 (Selection) ✓
- Day 13-14: REQ-007 (Persistence - with REQ-001)

Week 3-4 (Days 15-26):
- Day 13-14: REQ-004 (Difficulty) ✓
- Day 14-16: REQ-006 (Learning path)
- Day 15-17: REQ-015 (Claude API)
- Day 17-18: REQ-016 (Caching)

**Critical Path Duration: ~18-20 working days (3.5-4 weeks)**

But with proper parallelization and resource allocation, **real timeline: 4-5 weeks to MVP-ready** (accounting for testing, human decisions, unforeseen issues).

---

# PART 2: PARALLELIZATION GROUPS

## Group 1: Database & API Foundation (Can Start Immediately)
**Timeline:** Week 1 (3-5 days)
**Team:** 3 agents
**Dependencies:** None

### Requirements:
| REQ | Task | Days | Owner | Interface |
|-----|------|------|-------|-----------|
| REQ-017 | Database schema (SQLAlchemy + Alembic) | 2 | Agent A | PostgreSQL connection string |
| REQ-018 | FastAPI backend with endpoints | 2 | Agent B | API routes (POST /webhook, GET /health, etc.) |
| REQ-020 | Error handling & logging | 1 | Agent C | Logging middleware |
| REQ-019 | Security & authentication | 1 | Agent B | Auth middleware |
| REQ-031 | Health check endpoint | 1 | Agent C | GET /health endpoint |

**Handoffs:**
- Agent A → Agent B: Database connection string, models
- Agent B → Agent C: API routes that need logging
- All → Next phase: Working FastAPI app + PostgreSQL

**Success Criteria:**
- ✅ `python -m pytest tests/integration/test_db.py` passes
- ✅ `curl http://localhost:8000/health` returns 200
- ✅ `GET /health` responds in <500ms
- ✅ Logs are structured JSON
- ✅ Admin auth works (hardcoded Telegram ID)

---

## Group 2: Telegram Integration (Depends on Group 1)
**Timeline:** Week 1-2 (2-3 days, overlaps with Group 1)
**Team:** 1 agent (can work in parallel with API)
**Dependencies:** REQ-018 (API)

### Requirements:
| REQ | Task | Days | Owner | Interface |
|-----|------|------|-------|-----------|
| REQ-014 | Telegram bot webhook | 2 | Agent D | POST /webhook, message handlers |

**Handoffs:**
- Agent B (API) → Agent D: POST /webhook endpoint ready
- Agent D → Next phase: Bot responds to /start command

**Success Criteria:**
- ✅ BotFather registration complete
- ✅ Webhook URL set in Telegram
- ✅ `/start` command triggers response
- ✅ No errors in logs

---

## Group 3: Problem Content Curation (Independent, Long Pole)
**Timeline:** Week 1-2 (7-10 days)
**Team:** 1-2 content agents + 1 human (Bengali speaker, for QA)
**Dependencies:** None (can run fully parallel with backend)

### Requirements:
| REQ | Task | Days | Owner | Interface |
|-----|------|------|-------|-----------|
| REQ-005 | Problem curation (280 problems) | 8 | Human + Agent E | CSV import template |
| REQ-022 | Curriculum alignment | 2 | Agent E | Curriculum mapping doc |
| REQ-023 | Cultural appropriateness | 1 | Human review | QA checklist |

**Handoffs:**
- Human → Agent E: Content sources, Bengali translations
- Agent E → Database: CSV of 280 problems
- Agent E → Next phase: Problems available for selection

**Success Criteria:**
- ✅ 280 problems in database
- ✅ Each has: question (bn + en), answer, hints[3], difficulty, topic
- ✅ All Bengali reviewed by native speaker
- ✅ All culturally appropriate (no insensitive content)
- ✅ Curriculum mapping document created
- ✅ Zero duplicates

**Note:** This is the **longest single task** (10 days) but doesn't block Group 1. Start immediately in parallel.

---

## Group 4: Core Learning Engine (Depends on Groups 1, 3)
**Timeline:** Week 2-3 (6-8 days)
**Team:** 2-3 agents
**Dependencies:** REQ-017, REQ-018, REQ-005

### Requirements:
| REQ | Task | Days | Owner | Interface |
|-----|------|------|-------|-----------|
| REQ-008 | Problem selection algorithm | 3 | Agent F | /practice endpoint |
| REQ-001 | Daily practice sessions | 3 | Agent G | Practice flow, message handlers |
| REQ-007 | Session persistence | 2 | Agent G | Database schema updates |
| REQ-003 | Answer evaluation | 2 | Agent F | Evaluation logic |

**Handoffs:**
- Agent E → Agent F: 280 problems available in DB
- Agent F → Agent G: Selection algorithm returns problem_ids
- Agent G → Agent F: Answer submission with response data
- Agent F → Agent G: Evaluation feedback (correct/incorrect)
- All → Database: Session records with responses

**Success Criteria:**
- ✅ `/practice` returns 5 problems
- ✅ Student can submit answers
- ✅ Answers evaluated correctly (numeric ±5%, MC exact)
- ✅ Session persists across disconnections
- ✅ `/practice` again resumes mid-session
- ✅ Session expires after 30 minutes
- ✅ All session data in database

**Implementation Order:**
1. Agent F: Build selection algorithm (test with mock problems)
2. Agent G: Build practice flow & session persistence
3. Integrate together
4. Test with 5-10 real problems from REQ-005

---

## Group 5: Learning Optimization (Depends on Group 4)
**Timeline:** Week 3-4 (5-7 days)
**Team:** 2 agents
**Dependencies:** REQ-001, REQ-003, REQ-008

### Requirements:
| REQ | Task | Days | Owner | Interface |
|-----|------|------|-------|-----------|
| REQ-004 | Adaptive difficulty | 2 | Agent H | Modify REQ-008 selection |
| REQ-006 | Daily learning path | 2 | Agent H | Show topics preview |
| REQ-015 | Claude API integration | 2 | Agent I | Hint generation |
| REQ-016 | Prompt caching | 1 | Agent I | Cache layer |
| REQ-002 | Socratic hint system | 2 | Agent I | Hint commands |

**Handoffs:**
- Agent F (Group 4) → Agent H: Answer data available
- Agent H → Agent F: Selection algorithm now considers difficulty
- Agent I → Database: Cache table schema
- Agent I → Agent H: Hints available on command

**Success Criteria:**
- ✅ Difficulty increases after 2 correct
- ✅ Difficulty decreases after 1 wrong
- ✅ Learning path shows topics for today
- ✅ Claude API generates Socratic hints
- ✅ Hints cached (70%+ hit rate)
- ✅ Cost <$0.001 per hint

---

## Group 6: Engagement Hooks (Depends on Group 4)
**Timeline:** Week 5 (5-6 days)
**Team:** 2 agents
**Dependencies:** REQ-001, REQ-017

### Requirements:
| REQ | Task | Days | Owner | Interface |
|-----|------|------|-------|-----------|
| REQ-009 | Streak tracking | 1 | Agent J | On session complete |
| REQ-010 | Streak display | 1 | Agent J | `/streak` command |
| REQ-011 | Streak reminders | 2 | Agent K | Background job |
| REQ-012 | Streak milestones | 1 | Agent J | Celebration messages |
| REQ-013 | Daily encouragement | 2 | Agent K | Message pool |

**Handoffs:**
- Agent G (Group 4) → Agent J: Session completion events
- Agent J → Database: Streak records
- Agent J → Agent K: Streak data for reminders
- Agent K → Telegram: Messages to students

**Success Criteria:**
- ✅ Streak increments on daily practice
- ✅ `/streak` shows visual format
- ✅ 6pm IST reminder triggers
- ✅ Milestones celebrated at 7, 14, 30 days
- ✅ Encouragement messages vary

---

## Group 7: Localization & Operations (Depends on Groups 1, 4, 5)
**Timeline:** Week 5-6 (6-8 days)
**Team:** 2 agents
**Dependencies:** REQ-018, REQ-015, all UI requirements

### Requirements:
| REQ | Task | Days | Owner | Interface |
|-----|------|------|-------|-----------|
| REQ-021 | Bengali language support | 3 | Agent L | Translation layer |
| REQ-029 | Cost tracking | 2 | Agent M | Logging per API call |
| REQ-030 | Admin commands | 1 | Agent M | `/admin stats`, `/admin cost` |

**Handoffs:**
- All previous agents → Agent L: UI strings to translate
- Agent I (Claude) → Agent M: API call tracking
- Agent M → Database: Cost records
- Agent M → Admin: Reports via commands

**Success Criteria:**
- ✅ All messages in Bengali
- ✅ Language preference stored per student
- ✅ Every Claude call logged with tokens
- ✅ `/admin stats` works
- ✅ `/admin cost` shows week-to-date + projection
- ✅ Alert if >$0.15/month extrapolated

---

## Group 8: Admin Dashboard & Deployment (Depends on Groups 5, 7)
**Timeline:** Week 6-7 (6-8 days)
**Team:** 2 agents
**Dependencies:** REQ-018, REQ-029, REQ-030, REQ-019, REQ-031

### Requirements:
| REQ | Task | Days | Owner | Interface |
|-----|------|------|-------|-----------|
| REQ-034 | Admin web dashboard | 3 | Agent N | HTML + CSS + JS |
| REQ-032 | Deployment to Railway | 2 | Agent O | Railway config |
| REQ-033 | Disaster recovery | 2 | Agent O | Backup procedure |

**Handoffs:**
- Agent M (Cost tracking) → Agent N: Cost data API
- Agent B (API) → Agent N: All API endpoints for dashboard
- Agent A (DB) → Agent O: Connection string for Railway
- Agent O → Agent N: Live URL for dashboard

**Success Criteria:**
- ✅ Admin dashboard accessible at https://dars.railway.app/admin
- ✅ Shows students, engagement, cost metrics
- ✅ Deployed to Railway successfully
- ✅ SSL/HTTPS working
- ✅ Backups automated
- ✅ Health check passes

---

# PART 3: WORK STREAMS

## Stream A: Backend Infrastructure
**Duration:** Weeks 1-7 (continuous)
**Team:** 3-4 agents (A, B, C, D)
**Deliverable:** Working FastAPI backend serving all features

### Phase 1 (Week 1):
- Agent A: PostgreSQL schema, migrations
- Agent B: FastAPI app structure, endpoints
- Agent C: Error handling, logging
- Agent D: Telegram integration (webhook)

**Deliverable:** Working API accepting Telegram webhooks

### Phase 2 (Week 2-3):
- Agents A, B: Add practice endpoints
- Agent C: Enhance error handling for practice flows
- Shared: Integrate with problem selection

**Deliverable:** `/practice` endpoint fully functional

### Phase 3 (Week 3-4):
- Agent B: Add Claude API endpoints
- Agent C: Logging for API calls
- Shared: Integrate with caching

**Deliverable:** Hint generation endpoint working

### Phase 4 (Week 5):
- Agent B: Add streak/engagement endpoints
- Shared: Integrate with notifications

**Deliverable:** All gameplay endpoints functional

### Phase 5 (Week 5-6):
- Agent B: Add admin endpoints
- Agent C: Structured logging for admin
- Shared: Build dashboard data API

**Deliverable:** Admin API fully functional

### Phase 6 (Week 6-7):
- Agent B: Prepare for deployment
- Agent A: Database on Railway
- Shared: Health checks working

**Deliverable:** Production-ready backend

### Handoffs:
- Within stream: A → B → C continuously
- To Stream B (Frontend): API contracts, endpoints
- To Stream C (Content): Database schema ready
- To Stream D (Operations): Cost tracking logs

---

## Stream B: Frontend & Admin UI
**Duration:** Weeks 5-7 (later start, parallel with backend)
**Team:** 1-2 agents (N)
**Deliverable:** Admin dashboard

### Phase 1 (Week 5-6):
- Agent N: Design dashboard HTML structure
- Mock data from API contracts
- Build static pages

**Deliverable:** Dashboard without data

### Phase 2 (Week 6-7):
- Agent N: Integrate with backend API
- Fetch real data
- Add real-time updates (30s refresh)

**Deliverable:** Fully functional dashboard

### Handoffs:
- Stream A → Stream B: API endpoints, data format
- Stream B → Stream A: Dashboard URL for admin access

### Dependencies:
- Must wait for: REQ-029 (cost tracking)
- Must have: REQ-030 (admin commands)
- Must have: REQ-034 API endpoints (chart data)

---

## Stream C: Content & Localization
**Duration:** Weeks 1-6 (long but independent)
**Team:** 1-2 agents (E) + 1 human (Bengali speaker)
**Deliverable:** 280 problems + translations

### Phase 1 (Week 1-2):
- Agent E + Human: Source 280 problems
- Translate to Bengali
- Add contextual examples

**Deliverable:** 280 problems in CSV format

### Phase 2 (Week 2):
- Agent E: Import to database
- Quality check duplicates
- Curriculum mapping

**Deliverable:** Problems available for practice

### Phase 3 (Week 3-4):
- Agent E: Create curriculum mapping doc
- Map to WBBSE standards
- Difficulty classification

**Deliverable:** Curriculum alignment complete

### Phase 4 (Week 5-6):
- Agent L: Extract all UI strings
- Add to translation layer
- Final Bengali review

**Deliverable:** Bengali language support live

### Handoffs:
- Content → Backend (Stream A): CSV import for database
- Content → Learning (Stream D): 280 problems for selection algorithm
- Content → Localization: Strings for translation

### Dependencies:
- Must have: Native Bengali speaker for review (human decision)
- Must have: Content sourcing strategy decided (human decision)

---

## Stream D: Learning Algorithm & Engagement
**Duration:** Weeks 2-5 (core engine)
**Team:** 2-3 agents (F, G, H, I, J, K)
**Deliverable:** Complete learning experience

### Phase 1 (Week 2-3):
- Agent F: Selection algorithm
- Agent G: Practice flow, session management
- Agent I: Answer evaluation

**Deliverable:** Complete learning loop works

### Phase 2 (Week 3-4):
- Agent H: Adaptive difficulty
- Agent I: Claude integration
- Integration test: difficulty adapts correctly

**Deliverable:** Personalized learning works

### Phase 3 (Week 4):
- Agent I: Prompt caching
- Agent I: Socratic hints
- Test: Hints generate and cache

**Deliverable:** AI-powered hints work

### Phase 4 (Week 5):
- Agent J: Streak tracking
- Agent K: Reminders
- Agent J: Encouragement messages

**Deliverable:** Engagement hooks in place

### Handoffs:
- Stream C (Content) → Stream D: 280 problems
- Stream A (Backend) → Stream D: Database, API endpoints
- Within stream: F → G, I → (H, J, K)

### Dependencies:
- REQ-005 (content) must complete before full testing
- REQ-018 (API) must have session endpoints
- REQ-017 (database) must have schema

---

## Stream E: Operations & Monitoring
**Duration:** Weeks 5-7 (later start)
**Team:** 1-2 agents (M, O)
**Deliverable:** Cost tracking, deployment, monitoring

### Phase 1 (Week 5-6):
- Agent M: Cost tracking infrastructure
- Log every API call
- Generate cost reports

**Deliverable:** Cost visibility

### Phase 2 (Week 5-6):
- Agent M: Admin commands
- `/admin stats`, `/admin cost`

**Deliverable:** Admin has operational visibility

### Phase 3 (Week 6-7):
- Agent O: Deployment to Railway
- Agent O: Backups setup
- Agent O: Health monitoring

**Deliverable:** Production deployment

### Handoffs:
- Stream B (Frontend) → Stream E: Dashboard for cost visualization
- Stream A (Backend) → Stream E: Logging infrastructure
- Stream E → Stream B: Cost data for dashboard

### Dependencies:
- Must have: Stream A logging
- Must have: Stream A API endpoints
- Must have: Stream D cost per feature

---

## Integration Points & Handoffs

### Handoff 1: Database Ready (Day 2)
- **From:** Stream A (Agent A)
- **To:** All other streams
- **What:** PostgreSQL connection string, SQLAlchemy models
- **Format:** Python object definitions, migration scripts
- **Verification:** `pytest tests/integration/test_db.py` passes

### Handoff 2: API Routes Ready (Day 3)
- **From:** Stream A (Agent B)
- **To:** Streams B, D, E
- **What:** FastAPI endpoint specifications
- **Format:** OpenAPI docs at `/docs`, endpoint signatures
- **Verification:** `curl http://localhost:8000/docs` shows routes

### Handoff 3: Content Available (Day 10)
- **From:** Stream C (Agent E)
- **To:** Stream D (Agent F)
- **What:** 280 problems in database
- **Format:** Query result, CSV backup
- **Verification:** `SELECT COUNT(*) FROM problems` = 280

### Handoff 4: Selection Algorithm Ready (Day 13)
- **From:** Stream D (Agent F)
- **To:** Stream D (Agent G, H)
- **What:** Problem selection logic
- **Format:** Python function with test cases
- **Verification:** `pytest tests/unit/test_selection.py` passes

### Handoff 5: Practice Flow Ready (Day 15)
- **From:** Stream D (Agent G)
- **To:** Stream D (Agent H, I, J, K)
- **What:** Working practice endpoint, session persistence
- **Format:** `/practice` command handlers
- **Verification:** Manual testing: 5 problems → answers → evaluation

### Handoff 6: Claude Integration Ready (Day 17)
- **From:** Stream D (Agent I)
- **To:** Stream D (Agent I, H)
- **What:** Hint generation working
- **Format:** `/hint` command handler
- **Verification:** Manual testing: hint generation works

### Handoff 7: Engagement Features Ready (Day 22)
- **From:** Stream D (Agents J, K)
- **To:** Stream B
- **What:** Streak data, reminder jobs
- **Format:** Database tables, background job code
- **Verification:** Manual testing: streaks increment, reminders send

### Handoff 8: Cost Tracking Ready (Day 29)
- **From:** Stream E (Agent M)
- **To:** Stream B (Agent N)
- **What:** Cost data API endpoint
- **Format:** GET /admin/cost endpoint
- **Verification:** Dashboard displays costs

### Handoff 9: Everything Ready (Day 42)
- **From:** Streams A, B, D, E
- **To:** Stream E (Agent O)
- **What:** Production-ready system
- **Format:** Complete codebase, all tests passing
- **Verification:** Deploy to Railway, test end-to-end

---

## Hidden Dependencies & Risk Points

### Risk 1: Content Quality (HIGH)
- **Issue:** Poor problem translations → students confused → churn
- **Mitigation:** Native Bengali speaker reviews 10% sample in parallel with sourcing
- **Blocker:** No phase can proceed without verified problem content
- **Timeline impact:** Can delay up to 1 week if content sourcing slow

### Risk 2: Claude API Availability (MEDIUM)
- **Issue:** Claude API flaky or rate-limited → hints fail → bad UX
- **Mitigation:** Fallback to pre-written hints, proper error handling
- **Blocker:** REQ-002, 016 can't proceed without Claude working
- **Timeline impact:** Can delay up to 2 days if API integration fails

### Risk 3: Selection Algorithm Correctness (HIGH)
- **Issue:** Wrong algorithm weights → students get bored/frustrated
- **Mitigation:** A/B test weights with small user group, education expert review
- **Blocker:** Phase 0 success depends on algorithm quality
- **Timeline impact:** May need iteration (1-2 days) after pilot

### Risk 4: Telegram Webhook Stability (MEDIUM)
- **Issue:** Telegram rate limits, webhook failures → messages not received
- **Mitigation:** Queue system, retry logic, monitoring
- **Blocker:** REQ-014 must be rock-solid
- **Timeline impact:** Testing takes 2-3 extra days

### Risk 5: Bengali Localization Quality (HIGH)
- **Issue:** Poor translations feel foreign → cultural disconnect
- **Mitigation:** Native speaker review, test with real students early
- **Blocker:** Phase 0 launch blocked if translations poor
- **Timeline impact:** May need rework (1-2 days) after pilot

### Risk 6: Cost Control Failure (CRITICAL)
- **Issue:** AI costs exceed budget → unsustainable
- **Mitigation:** Prompt caching, cost monitoring, alerts
- **Blocker:** Phase 0 go/no-go decision depends on this
- **Timeline impact:** If cost control fails, must redesign (3-5 days)

---

# PART 4: CRITICAL PATH SUMMARY

## Timeline with Parallelization

```
WEEK 1:
├─ Mon-Wed (3 days):
│  ├─ Stream A: Database (REQ-017)
│  ├─ Stream A: API (REQ-018)
│  ├─ Stream A: Error handling (REQ-020)
│  └─ Stream C: Content sourcing starts (parallel)
│
├─ Thu-Fri (2 days):
│  ├─ Stream A: Security (REQ-019)
│  ├─ Stream A: Health check (REQ-031)
│  ├─ Stream D: Telegram integration (REQ-014)
│  └─ Stream C: Content sourcing continues
│
└─ End of Week 1: Backend foundation ready ✓

WEEK 2:
├─ Stream C: Content sourcing finishes (+ QA) ✓
├─ Stream D: Selection algorithm (REQ-008)
├─ Stream D: Practice flow (REQ-001)
├─ Stream D: Answer evaluation (REQ-003)
└─ End of Week 2: Core learning works ✓

WEEK 3:
├─ Stream D: Adaptive difficulty (REQ-004)
├─ Stream D: Learning path (REQ-006)
├─ Stream D: Claude integration (REQ-015)
└─ End of Week 3: Smart learning works ✓

WEEK 4:
├─ Stream D: Prompt caching (REQ-016)
├─ Stream D: Socratic hints (REQ-002)
└─ End of Week 4: AI hints work ✓

WEEK 5:
├─ Stream D: Streak tracking (REQ-009)
├─ Stream D: Streak display (REQ-010)
├─ Stream D: Milestones (REQ-012)
├─ Stream E: Cost tracking (REQ-029)
├─ Stream C: Bengali (REQ-021) starts
└─ End of Week 5: Engagement hooks work ✓

WEEK 6:
├─ Stream D: Reminders (REQ-011)
├─ Stream D: Encouragement (REQ-013)
├─ Stream E: Admin commands (REQ-030)
├─ Stream C: Bengali (REQ-021) finishes
├─ Stream B: Admin dashboard (REQ-034) starts
└─ End of Week 6: Operations visible ✓

WEEK 7:
├─ Stream B: Admin dashboard (REQ-034) finishes
├─ Stream E: Deployment (REQ-032)
├─ Stream E: Backups (REQ-033)
└─ End of Week 7: Production ready ✓

WEEK 8:
├─ Pilot: 50 students onboarded
├─ Testing: Fix bugs, iterate
└─ End of Week 8: MVP validation ✓
```

## Parallel Team Schedule

```
Week 1-2:
┌─────────────────────────────────────────────────────────┐
│ Stream A (Backend):    ████████████ (continuous)        │
│ Stream C (Content):    ░░░░░░░░░░░░░░░░░░░░░░░░░ (10d) │
│ Stream D (Algorithm):  __________████████ (start day 8) │
└─────────────────────────────────────────────────────────┘

Week 3-4:
┌─────────────────────────────────────────────────────────┐
│ Stream A (Backend):    ████████████ (continue)          │
│ Stream D (Algorithm):  ████████████████ (core logic)    │
│ Stream E (Ops):        __________░░░░ (prep)            │
└─────────────────────────────────────────────────────────┘

Week 5-6:
┌─────────────────────────────────────────────────────────┐
│ Stream A (Backend):    ████████████ (continue)          │
│ Stream B (Frontend):   __________████████ (dashboard)   │
│ Stream C (Content):    ░░░░░░░ (localization)           │
│ Stream D (Engagement): ████████ (hooks)                 │
│ Stream E (Ops):        ████████ (monitoring)            │
└─────────────────────────────────────────────────────────┘

Week 7+:
┌─────────────────────────────────────────────────────────┐
│ Stream A (Backend):    ████ (finalization)              │
│ Stream B (Frontend):   ░░░░ (polish)                    │
│ Stream E (Ops):        ████████ (deployment)            │
│ Pilot Team:            ████████████████ (launch + test) │
└─────────────────────────────────────────────────────────┘
```

---

# CONCLUSION

## Recommended Execution Strategy

1. **Start Week 1:** Streams A + C immediately (3-4 agents)
2. **Start Day 8:** Stream D joins (2-3 agents) as API becomes available
3. **Start Day 15:** Stream E prep (1 agent)
4. **Start Week 5:** Stream B (1 agent) with Stream E

**Total team: 5-6 agents + 1 product manager + human decisions (education expert, Bengali speaker)**

**Critical success factors:**
1. ✅ Content sourced and verified by day 8
2. ✅ Backend API stable by day 5
3. ✅ Selection algorithm weights correct by day 13
4. ✅ Claude API working reliably by day 17
5. ✅ Cost stays <$0.10/student/month

**Worst case if one stream gets blocked:**
- If content late → delays Stream D by 3-5 days (parallel, so acceptable)
- If API unstable → delays all by 2-3 days (serial, critical)
- If Claude API fails → can fallback to pre-written hints (2 day delay)
- If cost too high → must redesign (5 day rework)

**Best case with efficient execution:**
- Week 4.5: Core MVP ready (practice + difficulty + hints working)
- Week 5.5: Engagement features ready
- Week 6.5: Admin dashboard ready
- Week 7: Deployed to production
- Week 7-8: Pilot & iteration
