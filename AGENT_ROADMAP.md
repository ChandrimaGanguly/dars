# Dars AI Tutoring Platform - Autonomous Agent Implementation Roadmap

**Duration:** 8 weeks
**Target:** 50 students in Kolkata via Telegram
**Success:** >50% weekly engagement, <$0.10/student/month, 40% retention week 4

---

## Executive Summary

**Critical Path:** Database → Backend → Content → Daily Practice → Hints → Gamification → Localization → Operations → Launch

**Recommended Parallelization:**
- 2-3 agents Week 1: Backend, Telegram, Database (critical path)
- 1-2 agents Week 1-2: Content curation (long-pole, can run parallel)
- 2 agents Weeks 2-3: Practice sessions, evaluation
- 1 agent Weeks 3-4: Adaptive difficulty, hints
- 1 agent Week 5: Engagement, gamification
- 1 agent Week 5-6: Localization, operations
- 1 agent Week 6-7: Admin dashboard, deployment

---

# PHASE 1: Backend & Integration Foundation
**Week 1 (5 days of agent work)**

**Demo:** "Admin can see Telegram bot responds to `/start`, database is connected, health endpoint returns 200"

**Requirements:**
- REQ-017: Database Schema (PostgreSQL + SQLAlchemy)
- REQ-018: Backend API (FastAPI with endpoints)
- REQ-019: Authentication & Security (includes webhook verification, CORS, rate limiting)
- REQ-014: Telegram Bot Integration (with signature verification)
- REQ-020: Error Handling & Logging (with sensitive data sanitization)
- REQ-031: Health Check Endpoint
- **SEC-001:** CORS Configuration Hardening
- **SEC-002:** Telegram Webhook Signature Verification
- **SEC-003:** Student Database Existence Verification
- **SEC-004:** Admin Authentication Enforcement
- **SEC-005:** Rate Limiting on All Endpoints
- **SEC-006:** Sensitive Data Sanitization in Logs
- **SEC-007:** Input Length Validation
- **SEC-008:** Query Parameter Validation

**Success Criteria:**
- ✅ PostgreSQL database running locally/Railway with schema created
- ✅ FastAPI app starts without errors
- ✅ POST /webhook receives Telegram updates AND verifies webhook signature
- ✅ GET /health returns `{"status": "ok", "db": "ok"}` in <500ms
- ✅ Admin ID auth works (hardcoded list) AND verified on all admin endpoints
- ✅ Student endpoints verify student exists in database before returning data
- ✅ All requests logged with JSON structure AND no sensitive data (tokens, keys, IDs)
- ✅ Errors don't crash app (graceful handling) AND don't expose stack traces
- ✅ CORS restricted to specific origins (not `*`)
- ✅ Rate limiting returns 429 if exceeded (max 100 requests/minute per IP)
- ✅ All string inputs have max_length validation (prevent DOS)
- ✅ Query parameters (page, limit, grade) properly validated with bounds

**Complexity:** M (2-3 days backend + API) + M (2-3 days security hardening) = **4-6 days total**

**Blockers:** None

**Work for Agents:**
1. **Agent A:** Create SQLAlchemy models (students, problems, sessions, responses, streaks, admins)
   - Define schema with proper indexes
   - Create Alembic migrations
   - Seed initial admin user
   - Complexity: M, ~2 days

2. **Agent B:** Build FastAPI app structure
   - Create app.py with FastAPI instance
   - Implement POST /webhook for Telegram
   - Implement GET /health
   - Implement core endpoints (practice, student, admin, streak routes)
   - Complexity: M, ~2 days

3. **Agent C:** Implement security & logging (CRITICAL - must complete before Phase 3)
   - **CORS Hardening (SEC-001):** Restrict allow_origins to specific domains (not `*`)
   - **Telegram Webhook Verification (SEC-002):** Verify X-Telegram-Bot-Api-Secret-Token header
   - **Student Database Verification (SEC-003):** Query DB to verify student exists, return 404 if not
   - **Admin Authentication Enforcement (SEC-004):** Use verify_admin() Depends() on all /admin/* endpoints
   - **Rate Limiting (SEC-005):** Implement slowapi rate limiting (100 req/min per IP, 10 hints/day per student)
   - **Sensitive Data Sanitization (SEC-006):** Mask API keys, tokens, admin IDs in logs
   - **Input Validation (SEC-007, SEC-008):** Add max_length to string fields, validate query param bounds
   - Add authentication middleware
   - Implement error handling (no stack trace exposure)
   - Structured JSON logging (no secrets)
   - Setup environment variables
   - Complexity: M, ~2-3 days

**Critical Subtasks for Agent C (Order matters):**
1. SEC-002 (Telegram verification) - Must work before webhook is live
2. SEC-001 (CORS) - Must be restricted before any external testing
3. SEC-003 (Student verification) - Required before Phase 3 practice endpoints
4. SEC-004 (Admin auth) - Required before admin endpoints are accessible
5. SEC-005 (Rate limiting) - Protects against DOS during testing
6. SEC-006 (Log sanitization) - Prevents accidental secret exposure
7. SEC-007/008 (Input validation) - Prevents DOS and injection attacks

**Deliverables:**
- Working FastAPI app
- PostgreSQL schema with migrations
- Telegram webhook endpoint
- Health check endpoint
- Error handling & logging infrastructure

**Hand-off to Phase 2:** Database is ready, API endpoints exist, Telegram webhook ready to receive messages

**Notes:**
- Use Railway PostgreSQL for simplicity (manages backups)
- Telegram bot already created via BotFather, just need webhook URL
- Store bot token in environment variable, never in code
- **SECURITY CRITICAL:** Phase 1 must include all 8 security requirements (SEC-001 through SEC-008) before Phase 3 (Practice endpoints) begins. These are blocking issues that affect user data security.
- **Testing:** Before Phase 3, test with internal team only. Do NOT onboard external users until security hardening is complete.
- **Code Review:** All security implementations in Agent C's work MUST be reviewed by security expert (Noor) before merge
- **Deployment:** Do NOT deploy to production until all SEC-* requirements pass. Interim deployments (staging) are OK with all security in place.

---

# PHASE 2: Problem Content Curation
**Week 1-2 (10 days of agent work, parallel with Phase 1)**

**Demo:** "Admin can query database and see 280 problems for grades 6-8, each with Bengali and English text, aligned to WBBSE curriculum"

**Requirements:**
- REQ-005: Problem Content Curation (280 problems)
- REQ-022: Curriculum Alignment (WBBSE Grade 7)
- REQ-023: Cultural Appropriateness

**Success Criteria:**
- ✅ 280 unique problems in database
- ✅ All problems have: question_bn, question_en, answer, hints[3], difficulty (1-3), topic, grade
- ✅ Problems cover: Number Systems, Profit & Loss, Fractions, Decimals, Percentages, Geometry, Algebra Intro
- ✅ All Bengali translations reviewed by native speaker
- ✅ All problems contextualized to India (currency ₹, local scenarios)
- ✅ No duplicates or near-duplicates
- ✅ 100% of problems verified for accuracy
- ✅ All content appropriate for 14-16 year olds

**Complexity:** L (1-2 weeks) - **This is the long-pole task**

**Blockers:** Needs human input - must have native Bengali speaker + math expert

**Work for Agents:**
1. **Human + Agent:** Content sourcing & translation
   - Find ~150-200 problems from reputable sources
   - Translate to Bengali (or find Bengali source materials)
   - Add contextual examples (mango vendor, auto-rickshaw, street vendor scenarios)
   - Verify accuracy with answer keys
   - Create CSV template for bulk upload
   - Complexity: L, ~7-10 days

2. **Agent:** Curriculum alignment & QA
   - Map each problem to WBBSE curriculum standard
   - Categorize by difficulty (easy/medium/hard based on WBBSE norms)
   - Quality check: culturally appropriate, mathematically sound
   - Remove duplicates
   - Create problem library stats document
   - Complexity: M, ~3-4 days

**Deliverables:**
- 280 problems in database (via CSV import)
- Curriculum mapping document
- Problem quality assurance report
- Easy problem list (for initial onboarding)
- CSV template for future bulk uploads

**Hand-off to Phase 3:** Content is ready for daily practice flow

**Notes:**
- **MUST HAVE HUMAN REVIEW:** A native Bengali speaker (not AI) needs to review ~10% of translations for quality
- Use existing problem banks: WBBSE official materials, Khan Academy (translated), local tutoring centers
- If sourcing takes longer than expected, agent can generate additional problems algorithmically as fallback (lower quality but still usable)
- Store problems in database, not files

---

# PHASE 3: Core Learning Engine
**Week 2-3 (8 days of agent work)**

**Demo:** "Student sends `/practice`, gets 5 problems, submits answers, sees score and feedback for each"

**Requirements:**
- REQ-008: Problem Selection Algorithm
- REQ-001: Daily Practice Sessions
- REQ-007: Practice Session State Persistence
- REQ-003: Answer Evaluation

**Success Criteria:**
- ✅ `/practice` command returns 5 problems from student's grade
- ✅ Problems are diverse (not all same topic)
- ✅ Problems ordered easy → hard
- ✅ Student can submit answer for each problem
- ✅ Answer evaluated correctly (numeric ±5%, multiple choice exact)
- ✅ Feedback shown: "Correct!" or "Not quite, let me help..."
- ✅ Score shown at end: "3/5 correct"
- ✅ Session state saved to database immediately
- ✅ Student can resume mid-session if disconnect
- ✅ Session expires after 30 minutes or completes

**Complexity:** M (3-5 days)

**Blockers:** Needs Phase 1 (API) and Phase 2 (Content)

**Work for Agents:**
1. **Agent A:** Problem selection algorithm
   - Input: student_id, performance history, recent topics
   - Output: ordered list of 5 problem_ids
   - Logic: 50% topic recency, 30% mastery, 20% difficulty variation
   - For first student: start with easy problems from all topics
   - Execution time: <500ms
   - Complexity: M, ~2-3 days

2. **Agent B:** Daily practice flow
   - `/practice` endpoint: calls selection algorithm, retrieves 5 problems from DB
   - Return Telegram message with problem 1/5
   - Handle student answer via webhook
   - Evaluate answer (numeric/multiple choice logic)
   - Return feedback & next problem
   - Track session state in database
   - `/practice` again to resume if disconnected
   - Complexity: M, ~3-4 days

3. **Agent C:** Session persistence & answer logging
   - Create session record in DB before showing first problem
   - Save each response immediately (before user responds to next problem)
   - Session includes: problem_ids, answers, timestamps, hints_used
   - Auto-complete if no response for 30 minutes
   - Allow resume same-day
   - Complexity: S, ~2 days

**Deliverables:**
- `/practice` command that delivers working practice sessions
- Problem selection algorithm in database queries
- Answer evaluation logic (numeric, MC)
- Session state persistence
- Response logging

**Hand-off to Phase 4:** Students can practice, answers are evaluated, data is logged

**Notes:**
- For first student, selection algorithm is trivial (random from grade)
- As student history grows, algorithm optimizes
- Test with 5-10 manual students before moving to next phase
- Session data is critical for all downstream features (streaks, hints, analytics)

---

# PHASE 4: Learning Optimization
**Week 3-4 (6 days of agent work)**
**Status: ✅ COMPLETE (2026-03-05) — 419 tests passing, 75% coverage**

**Demo:** "Student completes today's practice → sees '🔥 Day 3 streak!' in the completion message → types `/streak` → sees real data with milestone countdown. Next session: student who scored 4/5 yesterday gets harder problems; student who scored 1/5 gets easier ones. Student who answered wrong sees a format hint."

**Requirements:**
- REQ-003: Answer Evaluation (enhancement) ✅
- REQ-004: Adaptive Difficulty ✅
- REQ-006: Daily Learning Path ✅
- REQ-009: Streak Tracking ✅
- REQ-010: Streak Display ✅
- REQ-012: Streak Milestones ✅
- REQ-013: Daily Encouragement ✅

**Success Criteria:**
- ✅ `AdaptiveDifficultyService`: upgrades on ≥4/5 in 2 consecutive sessions, downgrades on ≤1/5
- ✅ `difficulty_level` column on Student with Alembic migration, clamped [1, 3]
- ✅ `ProblemSelector.select_problems()` accepts `difficulty_level` parameter and filters candidates
- ✅ `StreakRepository`: `get_or_create`, `record_practice` (idempotent), `get_for_student`, `get_last_7_days`
- ✅ Session completion increments streak in both `practice.py` and `webhook.py`
- ✅ `/streak` endpoint returns real DB data (replaced mock stub)
- ✅ Streak milestones 7/14/30 detected once, milestone messages appended to session-complete feedback
- ✅ `EncouragementService`: bilingual, streak-aware correct messages, session-start topics summary
- ✅ Answer normalization: Bengali numerals (০-৯), whitespace stripping; format hints for MC and numeric
- ✅ Structured logging: `difficulty_upgraded`, `difficulty_downgraded`, `difficulty_no_change`
- ✅ 9 adaptive difficulty integration tests + 15 streak flow integration tests (own fixtures, no MissingGreenlet)
- ✅ All 7 pre-commit pipeline stages pass; coverage 75%

**Key files added/modified:**
- `src/services/adaptive_difficulty.py` (new) — `AdaptiveDifficultyService`
- `src/services/encouragement.py` (new) — `EncouragementService`
- `src/repositories/streak_repository.py` (new) — `StreakRepository`
- `src/repositories/student_repository.py` (new) — `StudentRepository`
- `src/models/student.py` — `difficulty_level` column
- `alembic/versions/b1c2d3e4f5a6_*.py` — difficulty_level migration
- `src/routes/practice.py` — difficulty wiring, streak recording, session_start_message
- `src/routes/webhook.py` — streak recording on session complete
- `src/routes/streak.py` — real DB call replacing stub
- `src/services/answer_evaluator.py` — Bengali normalization, format hints
- `src/services/problem_selector.py` — difficulty_level param
- `tests/integration/test_adaptive_difficulty_flow.py` (new)
- `tests/integration/test_streak_flow.py` (new)

**Complexity:** M (2-3 days)

**Blockers:** Needs Phase 3 (Session data)

**Work for Agents:**
1. **Agent A:** Adaptive difficulty engine
   - Track consecutive correct/incorrect in session
   - Update difficulty level based on performance
   - Modify problem selection to respect difficulty
   - Difficulty 1 = easy, 2 = medium, 3 = hard
   - Reset to difficulty 1 each new day
   - Complexity: S, ~2 days

2. **Agent B:** Learning path personalization
   - Enhance selection algorithm to balance review (60%) + new (40%)
   - Identify topics not practiced in last 7 days
   - Prioritize: weak topics (low mastery) + untouched topics
   - Show student what they'll learn today
   - Complexity: M, ~2-3 days

3. **Agent C:** Answer evaluation enhancement
   - Add format suggestions: "Units? (e.g., 50 rupees)"
   - Accept "close enough" for decimals (round to 2 places)
   - Normalize student input (remove spaces/commas)
   - Complexity: S, ~1 day

**Deliverables:**
- Adaptive difficulty logic in selection algorithm
- Learning path visualization (what topics today)
- Enhanced answer evaluation

**Hand-off to Phase 5:** Learning is now personalized, not one-size-fits-all

**Notes:**
- A/B test difficulty threshold (2 consecutive vs 3?)
- Monitor: are students getting stuck or bored? Adjust difficulty smoothly
- Logging difficulty decisions helps optimize algorithm

---

# PHASE 5: Claude-Powered Hints & Socratic Method
**Week 4 (6 days of agent work)**

**Demo:** "Student gets wrong answer, requests hint, receives personalized Socratic hint like 'What units should your answer have?', can request up to 3 hints before seeing answer"

**Requirements:**
- REQ-015: Claude API Integration for Hints
- REQ-002: Socratic Hint System
- REQ-016: Prompt Caching

**Success Criteria:**
- ✅ Claude Haiku API integrated and working
- ✅ Hint prompt template generates contextual hints
- ✅ First hint asks guiding question (doesn't give answer)
- ✅ Second hint identifies specific misconception
- ✅ Third hint gives step-by-step guidance (still not the answer)
- ✅ After 3 hints, show correct answer with explanation
- ✅ Hints are cached by (problem_id, hint_number)
- ✅ Cache hit rate tracked (target: 70%+)
- ✅ Estimated 50-70% cost savings from caching
- ✅ API failure gracefully falls back to pre-written hints
- ✅ All API calls logged with tokens used

**Complexity:** M (3-4 days for API + caching)

**Blockers:** Needs Phase 3 (Answer submission) and Anthropic API key

**Work for Agents:**
1. **Agent A:** Claude API integration
   - Setup Anthropic SDK
   - Create hint generation function with prompt template
   - Input: problem, student_answer, hint_number
   - Output: personalized Socratic hint
   - Error handling: fallback to pre-written hints
   - Request logging (timestamp, tokens, cost)
   - Complexity: M, ~2 days

2. **Agent B:** Prompt caching & cost optimization
   - Implement Redis cache (or in-memory dict for Phase 0)
   - Cache key: (problem_id, hint_number)
   - Cache duration: 7+ days
   - Track cache hit/miss rates
   - Log cost per hint (cached vs fresh)
   - Weekly report: "Cache hit rate: 65%, Savings: $0.30/week"
   - Complexity: S, ~2 days

3. **Agent C:** Hint system integration
   - `/hint` command: "I'm stuck, give me a hint"
   - Show hint number (1/3)
   - Track hints_used per student per problem
   - After 3 hints: show answer + explanation
   - Complexity: S, ~1 day

**Deliverables:**
- Claude API integration for hint generation
- Socratic hint prompt template
- Caching infrastructure
- Cost tracking per hint
- `/hint` command in Telegram

**Hand-off to Phase 6:** Hints work, cost savings visible, students get Socratic guidance

**Notes:**
- **MUST HAVE:** Anthropic API key configured
- Pre-written hints are critical fallback (Claude API failures happen)
- Test prompt quality: hints should guide, not give away
- Cache warmup: First 5 students will generate hints, rest get cached
- Cost per hint: ~0.001 cents fresh, 0 cents cached

---

# PHASE 6: Engagement & Habit Formation
**Week 5 (6 days of agent work)**

**Demo:** "After completing practice, student sees '🔥 Day 3 streak!' and next milestone in 4 days, receives celebration message at 7-day milestone, gets daily 6pm reminder if hasn't practiced"

**Requirements:**
- REQ-009: Streak Tracking
- REQ-010: Streak Display & Visualization
- REQ-011: Streak Reminders
- REQ-012: Streak Milestones
- REQ-013: Daily Encouragement

**Success Criteria:**
- ✅ Streak increments by 1 when daily practice completed
- ✅ Streak resets to 0 if student misses a day
- ✅ Longest streak tracked separately
- ✅ `/streak` shows: current, longest, last 7 days, next milestone
- ✅ Example: "🔥 Current: 12 days | ⭐ Longest: 28 | 📅 Next: 14 (2 days away!)"
- ✅ Milestone celebrations: 7 days (🔥🔥🔥), 14 days (👑), 30 days (⭐)
- ✅ Daily 6pm reminder if not practiced: "Your 5-day streak is at risk!"
- ✅ Encouragement message after correct answer varies by streak
- ✅ Never repeat exact message twice in a week per student
- ✅ All messages culturally appropriate for Bengali-speaking students

**Complexity:** S-M (2-3 days)

**Blockers:** Needs Phase 3 (Session completion) and database

**Work for Agents:**
1. **Agent A:** Streak tracking system
   - On session completion: increment streak if same calendar day
   - Daily boundary: 12am UTC
   - Timezone handling: India is UTC+5:30
   - Historical retention: never delete streak data
   - Complexity: S, ~1-2 days

2. **Agent B:** Streak visualization & milestones
   - `/streak` command shows current/longest/calendar/next milestone
   - Emoji celebration on milestone hit (7/14/30 days)
   - Milestone logged in database
   - Handle multiple milestones same day (e.g., reset and restart at 14)
   - Complexity: S, ~1 day

3. **Agent C:** Reminders & encouragement
   - Background task: 6pm IST every day, send reminder if not practiced
   - Reminder message personalizes by streak: "Your 10-day streak is at risk!"
   - Encouragement after each correct: varies by streak + performance
   - Message pool: 20+ messages, never repeat in 7 days per user
   - Complexity: M, ~2 days

**Deliverables:**
- Streak tracking logic
- `/streak` command with visualization
- Daily reminder job (background task)
- Encouragement message library
- Streak milestone celebrations

**Hand-off to Phase 7:** Students have habit-forming streak system, daily engagement driver in place

**Notes:**
- Streak psychology is powerful: "Don't break the chain"
- Test reminder timing: 6pm IST might be adjusted based on student activity data
- A/B test encouragement messages: which ones drive more completion?
- Timezone math: UTC 6pm IST = 12:30pm UTC

---

# PHASE 7: Localization & Operations Monitoring
**Week 5-6 (8 days of agent work)**

**Demo:** "All messages are in Bengali, admin can see cost dashboard showing $0.08 per student so far, health endpoint confirms system is healthy"

**Requirements:**
- REQ-021: Bengali Language Support
- REQ-029: Cost Tracking & Monitoring
- REQ-030: Admin Commands
- REQ-020: Error Handling & Logging (enhancement)

**Success Criteria:**
- ✅ All user-facing strings available in Bengali & English
- ✅ Language selected at `/start` (default: Bengali)
- ✅ Preference stored per student
- ✅ All messages use student's language (problems, hints, encouragement, etc.)
- ✅ Math terminology verified by native speaker
- ✅ Currency shown as ₹ in Bengali, Rs. in English
- ✅ All Claude API calls logged with tokens + cost
- ✅ Daily cost aggregated per student
- ✅ Weekly cost report to admin
- ✅ Alert if cost exceeds $0.15/month extrapolated
- ✅ `/admin stats` returns: total students, active week, avg streak, cost
- ✅ `/admin cost` returns: week-to-date, daily average, per-student
- ✅ All logs structured (JSON), searchable, no sensitive data

**Complexity:** M (3-4 days)

**Blockers:** Needs Phase 1 (API), Phase 3 (Sessions), Phase 5 (Claude)

**Work for Agents:**
1. **Agent A:** Bengali localization
   - Create translation strings file (all UI text)
   - Translate problem statements, hints, feedback, encouragement
   - Get native speaker review of 10% sample
   - Create language selection flow
   - Store preference in student profile
   - Route all messages through translation layer
   - Complexity: M, ~2-3 days

2. **Agent B:** Cost tracking & alerting
   - Log every Claude API call: tokens in/out, cost
   - Aggregate daily by student
   - Weekly report: total, per-student, trend
   - Alert if >$0.15/month extrapolated
   - Dashboard: show cost trajectory
   - Complexity: M, ~2 days

3. **Agent C:** Admin commands & logging enhancement
   - `/admin stats`: students, active, avg streak, sessions
   - `/admin cost`: week-to-date, daily avg, projection
   - `/admin students <grade>`: list with streaks
   - Ensure all admin commands require hardcoded ID
   - Structured JSON logging with context
   - Complexity: S, ~1-2 days

**Deliverables:**
- Bengali translations for all UI
- Cost tracking infrastructure
- Admin commands & reporting
- Enhanced logging system
- Weekly cost report generator

**Hand-off to Phase 8:** System is bilingual, costs are tracked, admin has visibility

**Notes:**
- **MUST HAVE HUMAN:** Native Bengali speaker to review translations (~2-3 hours)
- Translation strings should be centralized (easy to update)
- Cost alert threshold ($0.15/month) might be adjusted based on actual data
- Admin commands are authenticated via hardcoded Telegram ID list

---

# PHASE 8: Admin Visibility & Production Launch
**Week 6-7 (10 days of agent work)**

**Demo:** "Admin opens admin dashboard, sees 50 students onboarded, 83% engaged this week, avg 7-day streak, $1.23 weekly cost ($0.16 per student), can see top performers and at-risk students"

**Requirements:**
- REQ-034: Admin Web Dashboard (Phase 0)
- REQ-032: Deployment & Scaling
- REQ-033: Disaster Recovery & Backups (basic)

**Success Criteria:**
- ✅ Dashboard accessible at https://dars.railway.app/admin
- ✅ Hardcoded admin authentication works
- ✅ Real-time metrics: students, active week, avg streak, sessions
- ✅ Cost summary: week-to-date, daily avg, per-student, trend
- ✅ Student list: searchable, sortable by streak/accuracy
- ✅ Per-student: streak, problems attempted, accuracy %, last practice
- ✅ Problem library stats: count by topic/difficulty/language
- ✅ Recent activity log: last 20 actions (sessions, errors)
- ✅ Simple charts: daily active users, topics distribution
- ✅ Auto-refresh every 30 seconds
- ✅ Mobile responsive (Bootstrap CSS)
- ✅ Deployment to Railway successful
- ✅ All environment variables configured (no hardcoded secrets)
- ✅ PostgreSQL auto-backups via Railway
- ✅ Health checks passing, <2s response time
- ✅ SSL/HTTPS configured automatically

**Complexity:** M (3-4 days each for dashboard + deployment)

**Blockers:** All previous phases complete

**Work for Agents:**
1. **Agent A:** Admin dashboard
   - Backend: GET /admin/stats, /admin/cost, /admin/students, /admin/problems
   - Frontend: Simple HTML + vanilla JS + Bootstrap CSS
   - Charts: Chart.js for daily active users, accuracy distribution
   - Auto-refresh: fetch every 30 seconds
   - Responsive design: works on desktop/tablet/phone
   - No React/build tools (keep deployment simple)
   - Complexity: M, ~3 days

2. **Agent B:** Deployment & infrastructure
   - Setup Railway project + PostgreSQL add-on
   - Configure environment variables (secrets management)
   - Deploy FastAPI app to Railway
   - Setup Telegram webhook URL
   - Verify health endpoints
   - Test end-to-end: Telegram → Webhook → Database
   - Complexity: M, ~2-3 days

3. **Agent C:** Backup & monitoring
   - Enable automatic Railway backups (daily)
   - Manual backup export procedure documented
   - Health monitoring: set up Pingdom or similar
   - Error tracking: logs stream to stdout (Railway captures)
   - Runbook for common issues (DB down, Claude timeout, etc.)
   - Complexity: S, ~2 days

**Deliverables:**
- Working admin dashboard
- Production deployment on Railway
- Backup procedures
- Monitoring setup
- Runbook for operations

**Hand-off to Phase 8+:** System is production-ready, monitoring is active, admin has full visibility

**Onboarding 50 Students (Week 7-8):**
- Create student onboarding guide (WhatsApp/email to champions)
- Monitor first 100 sessions for errors
- Gather feedback: what's working? what's frustrating?
- Iterate on critical issues (bugs, unclear instructions)
- Prepare launch demo

**Notes:**
- **CRITICAL:** Test end-to-end with 5-10 real Telegram users before launch
- Webhook URL should be live before any onboarding
- Railway PostgreSQL is managed, backups are automatic
- Monitor logs for errors first week: fix bugs immediately
- Celebrate milestones: "First student hit 7-day streak!"

---

# REQUIREMENTS DEPENDENCY GRAPH

```
Phase 1 (Week 1):
├─ REQ-017 (Database) ────────────────────────────────────────→ REQUIRED for all phases
├─ REQ-018 (API)     ────────────────────────────────────────→ REQUIRED for all phases
├─ REQ-014 (Telegram) ───────────────────────────────────────→ REQUIRED for practice
├─ REQ-019 (Security) ────────────────────────────────────────→ REQUIRED for production
├─ REQ-020 (Errors)  ────────────────────────────────────────→ REQUIRED for reliability
└─ REQ-031 (Health)  ────────────────────────────────────────→ REQUIRED for monitoring

Phase 2 (Week 1-2, parallel):
└─ REQ-005 (Content) ────────────────────────────────────────→ REQUIRED for practice
    ├─ REQ-022 (Curriculum)
    └─ REQ-023 (Cultural)

Phase 3 (Week 2-3):
├─ REQ-008 (Selection) ← REQ-005, REQ-017, REQ-018
├─ REQ-001 (Practice)  ← REQ-008, REQ-005
├─ REQ-007 (Persist)   ← REQ-001, REQ-018
└─ REQ-003 (Evaluate)  ← REQ-001, REQ-018

Phase 4 (Week 3-4):
├─ REQ-004 (Difficulty) ← REQ-003, REQ-001
└─ REQ-006 (Path)      ← REQ-001, REQ-004

Phase 5 (Week 4):
├─ REQ-015 (Claude)     ← REQ-018
├─ REQ-002 (Hints)      ← REQ-015, REQ-003
└─ REQ-016 (Cache)      ← REQ-015

Phase 6 (Week 5):
├─ REQ-009 (Streak)     ← REQ-001, REQ-017
├─ REQ-010 (Display)    ← REQ-009
├─ REQ-011 (Reminders)  ← REQ-009, REQ-018
├─ REQ-012 (Milestones) ← REQ-009
└─ REQ-013 (Encourage)  ← REQ-001, REQ-009

Phase 7 (Week 5-6):
├─ REQ-021 (Bengali)     ← All UI requirements
├─ REQ-029 (Cost)        ← REQ-015, REQ-017, REQ-018
└─ REQ-030 (Commands)    ← REQ-018, REQ-029

Phase 8 (Week 6-7):
├─ REQ-034 (Dashboard)   ← REQ-018, REQ-029, REQ-030
├─ REQ-032 (Deployment)  ← REQ-019, REQ-031
└─ REQ-033 (Backups)     ← REQ-017
```

---

# REQUIREMENTS TO CUT FROM PHASE 0

**Deferred to Phase 1 (not needed for MVP validation):**

| REQ | Feature | Why Cut | When to Add |
|-----|---------|---------|-------------|
| REQ-024 | Teacher Dashboard | Requires teacher setup, school partnerships not ready yet | Phase 1, after pilot learnings |
| REQ-025 | Class Management | Same as above | Phase 1 |
| REQ-026 | Teacher Communication | Same as above | Phase 1 |
| REQ-027 | Community Champions | Champions identified but dashboard not needed for MVP | Phase 1 |
| REQ-028 | Referral System | Nice to have, low effort but not critical for first 50 students | Phase 1 |
| REQ-035 | Teacher Dashboard (full) | Too complex, manual tracking sufficient | Phase 1 |
| REQ-036 | Content Management UI | Manual CSV upload sufficient for Phase 0 | Phase 1 |
| REQ-037 | Champion Dashboard | Can manage via WhatsApp group | Phase 1 |
| REQ-038 | Analytics Dashboard | Too early, not enough data | Phase 1 |
| REQ-040 | Web UI Auth | Hardcode admin ID for Phase 0 | Phase 1 |
| REQ-033 | Disaster Recovery (full) | Railway auto-backups sufficient | Phase 1+ |
| REQ-039 | Responsive Design | Not critical, focus on desktop first | Phase 1 |
| REQ-032 (partial) | Auto-scaling | Manual scaling sufficient for 50 students | Phase 1 |

**Not cut, but lightweight implementation:**

| REQ | Feature | Phase 0 Version |
|-----|---------|-----------------|
| REQ-006 | Learning Path | Simple: show topics for today |
| REQ-030 | Admin Commands | Just `/admin stats` and `/admin cost` |
| REQ-032 | Deployment | Deploy to Railway (easy) |

---

# REQUIREMENTS NEEDING HUMAN DECISION

**Before Phase 2 starts (Content Curation):**

1. **REQ-005 Content Curation**
   - **Question:** Where do we source 280 problems? (Textbooks, Khan Academy, create custom?)
   - **Decision needed:** Content sourcing strategy + native Bengali speaker to review
   - **Timeline:** Decide by end of Week 1
   - **Impact:** If sourced late, delays Phase 2

2. **REQ-021 Bengali Translations**
   - **Question:** Do we hire translator or use bilingual team member?
   - **Decision needed:** Translation approach + budget
   - **Timeline:** Decide by end of Week 1
   - **Impact:** Phase 7 quality depends on translation quality

**Before Phase 3 starts:**

3. **REQ-008 Problem Selection Algorithm**
   - **Question:** Weights (50% recency / 30% mastery / 20% difficulty) correct?
   - **Decision needed:** Verify algorithm weights with education expert
   - **Timeline:** Decide by Week 2
   - **Impact:** Wrong weights = poor learning outcomes

**Before Phase 4 starts:**

4. **REQ-004 Adaptive Difficulty Thresholds**
   - **Question:** Is "2 consecutive correct → harder" the right threshold?
   - **Decision needed:** Verify with learning science expert
   - **Timeline:** Decide by Week 3
   - **Impact:** Too strict = frustration, too loose = boredom

**Before Phase 5 starts:**

5. **REQ-015 Claude Hint Prompt Quality**
   - **Question:** Is Socratic prompt effective? Need to test with real students
   - **Decision needed:** Beta test with 5-10 students, gather feedback
   - **Timeline:** Week 4 (after hint system built)
   - **Impact:** Bad hints = students quit

**Before Phase 8 starts:**

6. **REQ-032 Deployment Target**
   - **Question:** Use Railway or Render? Both work, but cost/reliability varies
   - **Decision needed:** Choose platform + configure
   - **Timeline:** Week 6
   - **Impact:** affects cost, uptime, operational complexity

---

# UNDERSPECIFIED REQUIREMENTS

**These need clarification before agents can build:**

| REQ | Issue | Clarification Needed |
|-----|-------|---------------------|
| REQ-008 | Algorithm weights | What are optimal weights for problem selection? Subject-matter expert review needed |
| REQ-004 | Difficulty thresholds | "2 consecutive correct" is arbitrary. What's the right threshold? |
| REQ-013 | Encouragement messages | How many messages? What's the randomization strategy? |
| REQ-022 | Curriculum alignment | Which WBBSE chapters for each topic? Need curriculum mapping document |
| REQ-023 | Cultural appropriateness | What specific cultural norms to follow? Need guidelines |
| REQ-029 | Cost alert threshold | Is $0.15/month the right threshold? Or should it be $0.10/month? |
| REQ-011 | Reminder timing | Is 6pm IST correct? Should it vary by student activity? |
| REQ-006 | Learning path balance | Is 60/40 (review/new) ratio correct? Or should it be 70/30? |

**Recommendation:** Have education expert (teacher or curriculum specialist) review these before implementation.

---

# TIMELINE & AGENT PARALLELIZATION

```
Week 1-2:  Phase 1 (Backend)     [Agent A, B, C] + Phase 2 (Content)  [Agent D, Human]
Week 2-3:  Phase 3 (Learning)    [Agent A, B, C]
Week 3-4:  Phase 4 (Difficulty)  [Agent A, B] + Phase 5 (Hints) [Agent C]
Week 5:    Phase 6 (Engagement)  [Agent A, B] + Phase 7 (Ops) [Agent C]
Week 5-6:  Phase 7 (Localization) [Agent A, B] + Phase 8 (Dashboard) [Agent C, D]
Week 6-7:  Phase 8 (Launch)      [All agents] + Phase 8+ (Pilot) [Human + Agents]
Week 7-8:  Pilot & Iteration     [Human coordination + agents on-call]
```

**Recommended team:**
- 2-3 backend agents (FastAPI, database, API)
- 1 frontend agent (dashboards, UI)
- 1 content/human coordination agent
- 1 Telegram integration specialist
- Human oversight: product manager + education expert

---

# GO/NO-GO CRITERIA FOR PHASE 1

Before Phase 2 starts, Phase 1 must be 100% complete and tested:

- ✅ FastAPI app runs without errors
- ✅ PostgreSQL schema created and migrated
- ✅ Telegram webhook receives updates
- ✅ POST /webhook doesn't crash app
- ✅ GET /health returns 200
- ✅ Admin ID authentication works
- ✅ Error handling prevents crashes
- ✅ Logging works (JSON format visible in logs)
- ✅ End-to-end test: send /start via Telegram, see bot respond

**If any criteria fail:** Fix before moving to Phase 2

---

# SECURITY AUDIT MAPPING TO ROADMAP

**Security Assessment Date:** 2026-01-30
**Audit Conducted By:** Claude Security Auditor
**Total Vulnerabilities Found:** 15 (3 CRITICAL, 5 HIGH, 4 MEDIUM, 3 LOW)

## Vulnerability Resolution Roadmap

### PHASE 1 (WEEK 1) - CRITICAL SECURITY FIXES
**Must be completed before Phase 3 begins. Code review required before merge.**

| ID | Vulnerability | Severity | Status | Phase Integration | Owner |
|-----|--------------|----------|--------|------------------|-------|
| SEC-001 | CORS configuration allows all origins | CRITICAL | TODO | Phase 1, Agent C | Noor |
| SEC-002 | Telegram webhook lacks signature verification | CRITICAL | TODO | Phase 1, Agent C | Noor |
| SEC-003 | Student auth has no database verification (IDOR) | CRITICAL | TODO | Phase 1, Agent C | Noor |
| SEC-004 | Admin endpoints not enforcing authentication | HIGH | TODO | Phase 1, Agent C | Noor |
| SEC-005 | Missing rate limiting (DOS vulnerability) | HIGH | TODO | Phase 1, Agent C | Noor |
| SEC-006 | Sensitive data in logs (API keys exposure) | HIGH | TODO | Phase 1, Agent C | Noor |
| SEC-007 | No input length validation | MEDIUM | TODO | Phase 1, Agent C | Noor |
| SEC-008 | Insufficient query parameter validation | MEDIUM | TODO | Phase 1, Agent C | Noor |

**Agent C Deliverables (Security Hardening):**
```python
# SEC-001: CORS - Restrict to Railway domain
CORSMiddleware(
    allow_origins=["https://dars.railway.app", "http://localhost:3000"],  # Not "*"
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-Student-ID", "X-Admin-ID"],
)

# SEC-002: Telegram webhook - Verify signature
@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    update: TelegramUpdate
):
    # Verify X-Telegram-Bot-Api-Secret-Token header
    secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if not secret_token or secret_token != TELEGRAM_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid webhook token")
    # ... process update

# SEC-003: Student verification - Query database
async def verify_student(x_student_id: int = Header(...)) -> int:
    # NEW: Verify student exists in database
    student = await db.execute(
        select(Student).where(Student.telegram_id == x_student_id)
    )
    if not student.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Student not found")
    return x_student_id

# SEC-004: Admin auth - Use Depends() on all /admin/* routes
@router.get("/admin/stats")
async def get_admin_stats(
    admin_id: int = Depends(verify_admin),  # NEW: enforce auth
    db: AsyncSession = Depends(get_session),
) -> AdminStats:
    ...

# SEC-005: Rate limiting - Use slowapi
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.post("/practice/{problem_id}/hint")
@limiter.limit("10/day")  # Max 10 hints per day per IP
async def request_hint(...):
    ...

# SEC-006: Log sanitization - Mask sensitive data
def sanitize_log_data(data: dict) -> dict:
    # Mask API keys, tokens, admin IDs
    sensitive_keys = ["api_key", "token", "secret", "admin_id", "x-admin-id"]
    for key in sensitive_keys:
        if key in data:
            data[key] = "***MASKED***"
    return data

logger.info("Request", extra=sanitize_log_data(request_dict))

# SEC-007: Input validation - Add max_length
class AnswerRequest(BaseModel):
    student_answer: str = Field(..., max_length=500)  # NEW: prevent DOS

# SEC-008: Query parameter validation - Add bounds
@router.get("/admin/students")
async def get_admin_students(
    page: int = Query(1, ge=1, le=1000),  # NEW: upper bound
    limit: int = Query(20, ge=1, le=100),  # Already has bound
    grade: int | None = Query(None, ge=6, le=8),  # Already has bounds
):
    ...
```

### PHASE 3 (WEEK 2-3) - VERIFICATION REQUIREMENT
**SEC-003 (Student database verification) must be completed in Phase 1 BEFORE Practice endpoints go live in Phase 3.**

**Success Criteria for Phase 3:**
- ✅ All student endpoints verify student exists in database
- ✅ Attempting to access non-existent student returns 404, not data
- ✅ Attempting to access other student's data fails (access control)

### PHASE 7 (WEEK 5-6) - LOGGING ENHANCEMENT
**SEC-006 (Sensitive data sanitization) is enhanced in Phase 7 logging work.**

| ID | Enhancement | Phase 7 Task |
|-----|-------------|-------------|
| SEC-006 | Comprehensive log sanitization | Add centralized log filtering, test with real API keys |
| SEC-009 | Missing security headers | Add CSP, HSTS, X-Content-Type-Options headers |
| SEC-010 | Error response filtering | Never expose stack traces in production |

### PHASE 8 (WEEK 6-7) - SECURITY HEADERS & FINAL HARDENING
**Before production deployment, add security response headers.**

| ID | Vulnerability | Severity | Phase 8 Task | Owner |
|-----|--------------|----------|-------------|-------|
| SEC-009 | Missing security headers | MEDIUM | Add middleware for CSP, HSTS, X-Content headers | Jodha |
| SEC-010 | Stack trace exposure | MEDIUM | Implement environment-based error handling | Jodha |
| SEC-011 | Database connection risks | LOW | Verify echo=False in production config | Jodha |

**Phase 8 Deliverable (Security Headers):**
```python
# Add security headers middleware (BEFORE CORSMiddleware)
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

### POST-PHASE 8 (PHASE 1+ WORK) - BACKLOG ITEMS
**Lower priority items that don't block MVP but should be addressed in Phase 1+:**

| ID | Vulnerability | Severity | Recommended Phase | Notes |
|-----|--------------|----------|------------------|-------|
| SEC-012 | CSRF protection | MEDIUM | Phase 1+ | Not critical for Telegram-only MVP, add before web UI |
| SEC-013 | IDOR access control | LOW | Phase 1+ | Depends on SEC-003 fix, then add per-student access checks |
| SEC-014 | Database echo logging | LOW | Phase 1+ | Verify echo=False in all environments |
| SEC-015 | Exception handling | LOW | Phase 1+ | Replace broad catches with specific exceptions |

## Security Code Review Checklist (For Agent C)

**Before merging Phase 1 security work, verify:**

- [ ] CORS `allow_origins` does NOT contain `"*"` (must be specific domains)
- [ ] All student endpoints call `verify_student()` and check database
- [ ] All admin endpoints use `Depends(verify_admin)` (not just header acceptance)
- [ ] Telegram webhook verifies `X-Telegram-Bot-Api-Secret-Token` header
- [ ] Rate limiting middleware is installed and limits `/hint` to 10/day
- [ ] No API keys, tokens, or admin IDs logged in JSON logs
- [ ] String inputs have `max_length` constraints (prevent DOS)
- [ ] Query parameters have reasonable bounds (page ≤ 1000, etc.)
- [ ] Error responses never contain stack traces (test with invalid input)
- [ ] All tests pass with security changes (unit + integration)
- [ ] Documentation updated with security assumptions

## Security Testing Plan (Phase 1)

**After security hardening is complete, run these tests:**

```bash
# Test CORS restrictions
curl -H "Origin: https://evil.com" http://localhost:8000/health
# Expected: No Access-Control-Allow-Origin header

# Test student verification
curl http://localhost:8000/practice -H "X-Student-ID: 99999"
# Expected: 404 Student not found

# Test admin auth enforcement
curl http://localhost:8000/admin/stats -H "X-Admin-ID: invalid"
# Expected: 403 Forbidden

# Test rate limiting
for i in {1..15}; do
    curl http://localhost:8000/practice/1/hint -H "X-Student-ID: 1"
    sleep 0.1
done
# Expected: 15th request returns 429 Too Many Requests

# Test log sanitization
# Check logs for any API keys, tokens, admin IDs
grep -i "api_key\|token\|admin_id" logs/
# Expected: No matches (all should be ***MASKED***)
```

## Risk Assessment if Security Work is Skipped

**DO NOT skip Phase 1 security work. Impact of delaying SEC-001 through SEC-008:**

| Risk | Impact | Likelihood | Consequence |
|------|--------|-----------|-------------|
| CORS bypass | Attackers make authenticated requests from malicious sites | HIGH | Data breach, reputation damage |
| Spoofed webhook | Fake Telegram updates processed as real | MEDIUM | Unauthorized state changes, bogus practice sessions |
| IDOR attacks | Attackers access/modify other student data | HIGH | Student data breach, regulatory violation (GDPR) |
| DOS via rate limiting | Service crashes from request flood | MEDIUM | Platform unavailability, lost user trust |
| Log secrets exposure | API keys/admin IDs visible in logs | MEDIUM | Credential compromise, unauthorized access |
| **Overall Risk** | **Would require complete security rebuild post-launch** | **HIGH** | **BLOCKER: Do not launch without these fixes** |

---

# GO/NO-GO FOR PHASE 0 COMPLETION

**Before pilot onboarding (Week 7-8), all 8 phases must meet success criteria:**

**Security (BLOCKING - must all pass):**
- ✅ CORS restricted to specific origins (not `*`)
- ✅ Telegram webhook verifies signature
- ✅ Student endpoints verify student exists in database
- ✅ Admin endpoints enforce authentication with verify_admin()
- ✅ Rate limiting returns 429 when exceeded
- ✅ Logs contain no sensitive data (API keys, tokens, admin IDs masked)
- ✅ String inputs have max_length validation
- ✅ Query parameters have reasonable bounds
- ✅ No stack traces in error responses
- ✅ Security code review completed and approved

Learning:
- ✅ Students can complete 5-problem sessions
- ✅ Answers are evaluated correctly
- ✅ Difficulty adapts based on performance
- ✅ Socratic hints work (Claude API responding)

Engagement:
- ✅ Streaks track correctly
- ✅ Milestones celebrate at 7/14/30 days
- ✅ Reminders send at 6pm IST
- ✅ Encouragement messages vary by streak

Localization:
- ✅ All messages in Bengali
- ✅ Math terminology verified

Operations:
- ✅ Cost tracking shows <$0.10/student/month
- ✅ Admin dashboard displays all metrics
- ✅ Health check passes
- ✅ Deployment to Railway successful
- ✅ Security headers present (CSP, HSTS, X-Content-Type-Options)

**Pilot Success Criteria (Week 7-8):**
- ✅ 50 students onboarded
- ✅ >50% weekly engagement (25+ students practicing per week)
- ✅ Average streak reaches 7+ days by week 4
- ✅ No critical bugs (can have minor issues)
- ✅ Cost <$0.15/student/month
- ✅ >40% retention to week 4

---

## Summary

This roadmap delivers a working AI tutoring MVP in 8 weeks with:
- **Core learning engine:** Daily practice, answer evaluation, adaptive difficulty, Socratic hints
- **Engagement drivers:** Streaks, milestones, reminders, encouragement
- **Operations:** Cost tracking, admin dashboard, monitoring
- **Localization:** Bengali language support, curriculum alignment
- **Quality gates:** Each phase has success criteria, dependencies respected

The critical path is: Database → API → Content → Practice → Hints → Engagement → Operations → Launch.

Parallel work on content curation accelerates the timeline without blocking backend development.

No phase is half-built; each phase delivers working software that can be demoed and tested with real users.
