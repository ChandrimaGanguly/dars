# Dars AI Tutoring Platform - Requirements Specification

**Version:** 1.0
**Date:** 2026-01-28
**Status:** Approved for Phase 0 Implementation
**Audience:** Developers, Product Managers, Stakeholders

---

## Executive Summary

This document formalizes the Dars AI tutoring platform requirements extracted from the business proposal. Requirements are organized by functional area with clear acceptance criteria, dependencies, and complexity estimates.

**Phase 0 Focus:** Validate core hypothesis on Telegram with 50 students for 8 weeks
**Success Criteria:** 50% weekly engagement, 40% retention at week 4, <$0.15/student/month

---

## Requirements Overview

| Category | Count | Complexity |
|----------|-------|-----------|
| Core Learning | 8 | Mixed |
| Engagement | 5 | S/M |
| Platform | 10 | Mixed |
| Localization | 3 | S/M |
| Gamification | 4 | S/M |
| Teacher Features | 3 | M/L |
| Community Features | 2 | M |
| Admin/Operations | 5 | M |
| **TOTAL** | **40** | |

---

# CORE LEARNING EXPERIENCE

## REQ-001: Daily Practice Sessions

**The system shall deliver exactly 5 math problems per student per day, personalized to their grade level and performance history.**

**Acceptance Criteria:**
- [ ] System selects 5 problems when `/practice` command is sent
- [ ] Problems are from student's assigned grade (6, 7, or 8)
- [ ] Problems are drawn from curated problem bank (no AI generation)
- [ ] Problems increase in difficulty based on student's previous correct answers
- [ ] Each problem displays with clear question text in Bengali/English
- [ ] Student can skip max 1 problem per session
- [ ] Session ends when 5 problems are answered or skipped
- [ ] Session state persists if student disconnects mid-session

**Edge Cases:**
- Less than 5 problems available for grade → Use all available
- Student hasn't taken any tests yet → Start at easiest difficulty
- Same problem requested twice in a week → Never repeat same problem

**Dependencies:** REQ-011 (Content library), REQ-008 (Problem selection logic)

**Complexity:** M (3-5 days)

---

## REQ-002: Socratic Hint System

**The system shall guide students to answers using the Socratic method without directly providing correct answers.**

**Acceptance Criteria:**
- [ ] When student answers incorrectly, system offers first hint
- [ ] Hints are generated via Claude Haiku API with Socratic method prompt
- [ ] Hints guide student to think about the problem step-by-step
- [ ] Hints NEVER contain the correct answer
- [ ] Student can request additional hints (max 3 per problem)
- [ ] Each hint is more detailed than the previous
- [ ] Hints are cached after first generation (reused for same problem)
- [ ] System suggests answer format if student struggles (e.g., "What are the units?")
- [ ] After 3 hints, system shows correct answer with explanation
- [ ] Hint request is logged to track which students struggle with which topics

**Edge Cases:**
- Student responds with blank/gibberish → Treat as wrong answer, offer hint
- Student's answer is "close enough" (e.g., rounding difference) → Accept as correct
- Same student requests same hint twice → Return cached hint

**Dependencies:** REQ-014 (Claude API integration), REQ-017 (Prompt caching)

**Complexity:** M (3-4 days)

---

## REQ-003: Answer Evaluation

**The system shall evaluate student answers as correct or incorrect with appropriate feedback.**

**Acceptance Criteria:**
- [ ] Numeric answers: Accept if match exactly OR within tolerance (±5% for decimals)
- [ ] Multiple choice: Accept only exact selection
- [ ] Text answers: Use Claude for semantic evaluation (if needed in future)
- [ ] Return "Correct!" with emoji celebration for right answers
- [ ] Return "Not quite, let me help you..." for wrong answers
- [ ] Show step-by-step explanation of correct answer after 3 attempts
- [ ] Track answer history per student per problem
- [ ] Log confidence level based on hints needed
- [ ] Provide personalized encouragement based on progress

**Edge Cases:**
- Student provides answer in wrong format → Ask for clarification once, then guide
- Numeric answer with extra spaces or commas → Normalize and evaluate
- Duplicate submission of same answer → Accept as valid attempt

**Dependencies:** REQ-001 (Practice sessions), REQ-002 (Hints)

**Complexity:** M (2-3 days)

---

## REQ-004: Adaptive Difficulty

**The system shall adjust problem difficulty based on student performance in real-time.**

**Acceptance Criteria:**
- [ ] Starting difficulty: Easy problems (Level 1)
- [ ] After 2 consecutive correct answers → Increase to Medium (Level 2)
- [ ] After 1 wrong answer → Decrease to Easy (Level 1)
- [ ] Hard problems (Level 3) only presented if student consistently correct
- [ ] Difficulty selection happens at problem-selection time (not interactive)
- [ ] Difficulty resets daily (fresh start each day)
- [ ] Historical performance used to inform initial difficulty
- [ ] Topics with low mastery get easier problems

**Edge Cases:**
- First session ever → Start with Level 1
- Student hasn't practiced in 7 days → Reset to Level 1
- Mixed performance (some easy right, some medium wrong) → Stay at current level

**Dependencies:** REQ-001 (Daily practice), REQ-003 (Answer evaluation)

**Complexity:** S (2-3 days)

---

## REQ-005: Problem Content Curation

**The system shall maintain a curated library of math problems aligned to Grade 6-8 curriculum.**

**Acceptance Criteria:**
- [ ] Phase 0: 280 problems total (35 per week × 8 weeks)
- [ ] Each problem includes: question, answer, 2-3 hints, difficulty level
- [ ] All content in Bengali (translated from English source)
- [ ] Problems contextualized to India (currency: ₹, references: local context)
- [ ] Problems mapped to WBBSE (West Bengal Board) curriculum standards
- [ ] Topics covered (Phase 0): Number Systems, Profit & Loss, Fractions, Decimals, Percentages, Geometry, Algebra Intro
- [ ] No duplicate or near-duplicate problems
- [ ] All problems reviewed by native Bengali speaker
- [ ] Answer key accuracy verified (100% of problems)

**Edge Cases:**
- Problem has multiple valid answer formats → Accept all valid formats
- Culturally sensitive topics → Avoid or handle appropriately
- Level mismatch (problem labeled easy but is hard) → Adjust labeling

**Dependencies:** None (initial content creation)

**Complexity:** L (1-2 weeks of content curation)

---

## REQ-006: Daily Learning Path

**The system shall create a personalized daily learning path for each student based on their history.**

**Acceptance Criteria:**
- [ ] Problems selected are from topics NOT heavily practiced in last 7 days
- [ ] Problems are sequenced from easier to harder within a session
- [ ] System balances review (easier topics) with learning (new topics) - 60/40
- [ ] Learning path visible to student at start of session
- [ ] Student can see which topics they'll practice today
- [ ] System recommends practice time (typically morning 6-9am based on regional data)
- [ ] Path adapts if student completes session early
- [ ] Path adapts if student fails multiple problems in sequence

**Edge Cases:**
- All topics mastered → Mix in challenge problems and review
- No topics practiced yet → Linear progression through curriculum
- Student practices at different time than recommended → Still deliver full session

**Dependencies:** REQ-001 (Daily practice), REQ-004 (Adaptive difficulty)

**Complexity:** M (2-3 days)

---

## REQ-007: Practice Session State Persistence

**The system shall maintain practice session state across disconnections without losing progress.**

**Acceptance Criteria:**
- [ ] Session data stored in PostgreSQL immediately (before user response)
- [ ] If user disconnects mid-session, session can be resumed
- [ ] Resume shows last unsolved problem, not from beginning
- [ ] Max session duration: 30 minutes (then auto-completes)
- [ ] Session marked complete when all 5 problems answered OR session expires
- [ ] Session data includes: timestamp, problems, answers, hints_used, time_per_problem
- [ ] Completed sessions cannot be re-opened
- [ ] Incomplete sessions auto-complete after 24 hours if not resumed

**Edge Cases:**
- Network drops multiple times → Each reconnect resumes from last state
- User intentionally stops mid-session → Session pauses, can resume anytime today
- User closes Telegram app → Session persists in DB, resumable next time

**Dependencies:** REQ-001 (Daily practice), Database schema

**Complexity:** S (2 days)

---

## REQ-008: Problem Selection Algorithm

**The system shall implement an intelligent algorithm to select daily problems matching student level and learning goals.**

**Acceptance Criteria:**
- [ ] Input: student_id, performance_history, topics_recent, difficulty_preference
- [ ] Output: ordered list of 5 problem_ids
- [ ] Selection logic: Weighted selection by (1) topic recency, (2) mastery level, (3) difficulty
- [ ] Weights: 50% topic recency, 30% mastery, 20% difficulty variation
- [ ] Algorithm runs at practice start time (not pre-computed)
- [ ] Execution time: <500ms for problem selection
- [ ] Deterministic (same inputs = same outputs, for testing)
- [ ] Handles edge cases: insufficient problems, new student, all topics mastered
- [ ] Logged for analysis (which problems selected, why, student feedback)

**Edge Cases:**
- Only 3 problems available for requested topic → Use those 3, fill remaining from review
- Student mastered all topics → Introduce challenge problems (harder versions)
- Topic has only 2 problems total → Include both in today's mix

**Dependencies:** REQ-001 (Daily practice), REQ-005 (Content library), REQ-004 (Difficulty)

**Complexity:** M (3-4 days)

---

# ENGAGEMENT & GAMIFICATION

## REQ-009: Streak Tracking

**The system shall track student daily practice streaks to build consistent learning habits.**

**Acceptance Criteria:**
- [ ] Streak increments by 1 when student completes daily practice
- [ ] Streak resets to 0 if student misses a day
- [ ] Longest streak tracked separately from current streak
- [ ] Streak status displayed in `/practice` and `/streak` commands
- [ ] Streak data: current_streak, longest_streak, last_practice_date
- [ ] Streak calculation runs at practice completion time
- [ ] Daily boundary: 12 AM UTC (can be customized per region later)
- [ ] Leap day handling: Treated as normal day
- [ ] Historical streak data retained (for analytics)

**Edge Cases:**
- Student practices at 11:55 PM and 12:05 AM → Counts as same streak day
- Student travels across time zones → Uses server time (UTC)
- Clock resets (during DST) → Handles gracefully
- Timezone difference causes practice to count as previous day → Streak continues if within 24 hours

**Dependencies:** REQ-001 (Practice sessions)

**Complexity:** S (1-2 days)

---

## REQ-010: Streak Display & Visualization

**The system shall display streaks with visual feedback and motivation.**

**Acceptance Criteria:**
- [ ] `/streak` command shows current streak with fire emoji (🔥)
- [ ] Shows longest streak achieved
- [ ] Shows "days until 7-day milestone", "14-day milestone", "30-day milestone"
- [ ] Last 7 days calendar view (filled/empty circles)
- [ ] Example output:
  ```
  🔥 Current Streak: 12 days
  ⭐ Longest Streak: 28 days

  📅 Last 7 Days:
  Mon ●  Tue ●  Wed ●  Thu ●  Fri ●  Sat ○  Sun ●

  🎯 Next Milestone: 14 days (2 days away!)
  ```
- [ ] Emoji celebration when hitting milestones (7, 14, 30 days)
- [ ] Motivational message if streak at risk (not practiced today)

**Edge Cases:**
- Streak is 0 → Show "Start your first streak! Complete today's practice."
- At exactly milestone day → Show celebration + congratulations message
- User checks `/streak` multiple times a day → Same data (no duplicate counting)

**Dependencies:** REQ-009 (Streak tracking)

**Complexity:** S (1 day)

---

## REQ-011: Streak Reminders

**The system shall send daily reminders to students who haven't practiced to keep streaks alive.**

**Acceptance Criteria:**
- [ ] Reminder sent once per day (at 6 PM IST by default)
- [ ] Only sent if student hasn't completed practice today
- [ ] Reminder message includes current streak and days-to-milestone
- [ ] Reminder personalizes based on streak length (more urgent at higher streaks)
- [ ] Student can opt-out of reminders (disable in preferences, Phase 1)
- [ ] Reminder text: "Your X-day streak is at risk! Complete today's practice to keep it alive. 🔥"
- [ ] Max one reminder per student per day
- [ ] Reminder sent via Telegram WhatsApp (or SMS fallback, Phase 1)
- [ ] Opt-out/preference tracked in database

**Edge Cases:**
- Student has 0-day streak → Send motivational message, not "at risk" message
- Reminder send fails (network down) → Retry next hour
- Student disabled reminders → Never send (until re-enabled)

**Dependencies:** REQ-009 (Streak tracking), REQ-010 (Streak display)

**Complexity:** S (2 days)

---

## REQ-012: Streak Milestones

**The system shall celebrate milestone achievements (7, 14, 30 days) with special recognition.**

**Acceptance Criteria:**
- [ ] 7-day milestone: 🔥🔥🔥 "You're on fire! 7-day streak!"
- [ ] 14-day milestone: 👑 "You're unstoppable! 14-day streak!"
- [ ] 30-day milestone: ⭐ "Legend! 30-day streak! You're changing your learning journey!"
- [ ] Milestone achievement logged in database
- [ ] Milestone unlocks badge (visual in UI, Phase 1)
- [ ] Achievement shared with teacher dashboard (Phase 1)
- [ ] Total milestone count tracked per student
- [ ] Milestones never expire (historical record maintained)

**Edge Cases:**
- Student hits multiple milestones on same day (reset streak then immediately restart) → Show all
- Milestone message sent once (not duplicate if user checks `/streak` multiple times)
- User achievement replayed from backup (disaster recovery) → Don't resend message

**Dependencies:** REQ-009 (Streak tracking), REQ-010 (Streak display)

**Complexity:** S (1 day)

---

## REQ-013: Daily Encouragement

**The system shall provide personalized, varied encouragement messages to maintain motivation.**

**Acceptance Criteria:**
- [ ] Encouragement sent after each correct answer
- [ ] Messages vary by streak length (different for 1 day vs 30 days)
- [ ] Messages vary by performance (50% correct vs 100% correct)
- [ ] Messages are culturally appropriate and motivating
- [ ] Never repeat exact same message twice in a week for same student
- [ ] Messages in Bengali and English (matches student language preference)
- [ ] Examples:
  ```
  Correct! 🎉
  For 1st correct: "Great start! You're learning!"
  For streak 7+: "You're on fire! Keep it up! 🔥"
  For all correct: "Perfect session! You're a math star! ⭐"
  For 50% correct: "You're improving! Keep practicing tomorrow."
  ```
- [ ] Encouragement logged (for analysis of what works)

**Edge Cases:**
- First-time user → Use generic encouragement
- Student hasn't practiced in week → "Welcome back! Let's rebuild that streak!"
- Perfect streak for month → Exceptional message

**Dependencies:** REQ-001 (Practice sessions), REQ-003 (Answer evaluation), REQ-009 (Streaks)

**Complexity:** S (1-2 days)

---

# PLATFORM & TECHNICAL

## REQ-014: Telegram Bot Integration

**The system shall communicate with students exclusively through Telegram bot for Phase 0.**

**Acceptance Criteria:**
- [ ] Bot name: "Dars" (@DarsAITutor or similar)
- [ ] Bot accessible at all times (99.5% uptime target)
- [ ] All student interactions via Telegram direct message (no groups)
- [ ] Bot registered via BotFather with webhook endpoint
- [ ] Webhook receives all incoming messages and callbacks
- [ ] Bot commands available: `/start`, `/practice`, `/streak`, `/help`, `/language`
- [ ] Inline buttons for navigation (not text commands)
- [ ] Maximum response time: 2 seconds per message
- [ ] Fallback: SMS via Twilio if Telegram fails (Phase 1)

**Edge Cases:**
- Telegram API rate limiting → Queue messages and retry
- Network outage → Queue messages locally, send on reconnect
- User blocks bot → Graceful handling (no error spam)
- User tries group chat → Polite message: "I only work in direct messages"

**Dependencies:** Telegram Bot API, FastAPI backend

**Complexity:** M (2-3 days)

---

## REQ-015: Claude API Integration for Hints

**The system shall use Claude Haiku API to generate contextual Socratic hints.**

**Acceptance Criteria:**
- [ ] Claude Haiku selected for cost efficiency (~10x cheaper than Sonnet)
- [ ] Hint generation via prompt template with problem context
- [ ] Prompt includes: problem statement, student's answer, hint number
- [ ] API call latency: <3 seconds
- [ ] Retry logic: 3 attempts with exponential backoff
- [ ] Rate limiting: Max 10 AI calls per student per day
- [ ] Error handling: Graceful fallback to pre-written hints if API fails
- [ ] Request/response logging for debugging
- [ ] Cost tracking: Log API token usage per request

**Prompt Template:**
```
Problem: {problem_question}
Student's Answer: {student_answer}
Correct Answer: {correct_answer}
Hint Number: {hint_number}

Guide this student to the correct answer using the Socratic method.
- Hint 1: Start with a guiding question
- Hint 2: Point out the specific concept they're missing
- Hint 3: Give step-by-step guidance but NOT the answer

Generate Hint {hint_number} ONLY, no preamble.
```

**Edge Cases:**
- API returns error → Use fallback hint
- Student's answer is unintelligible → Generate generic hint
- Problem is ambiguous → Handle gracefully

**Dependencies:** REQ-002 (Socratic hints)

**Complexity:** M (2-3 days)

---

## REQ-016: Prompt Caching

**The system shall cache generated hints to reduce API costs and latency.**

**Acceptance Criteria:**
- [ ] Same-problem hints cached after first generation
- [ ] Cache key: (problem_id, hint_number)
- [ ] Cache duration: 7 days minimum
- [ ] Cache hit rate target: 70%+ (most problems have repeat solvers)
- [ ] Manual cache invalidation if hint quality poor
- [ ] In-memory cache (Redis or dict) for Phase 0
- [ ] Estimated cost savings: 50-70% reduction in AI costs

**Cache Statistics:**
- [ ] Track cache hits/misses
- [ ] Report hit rate weekly
- [ ] Identify problems with poor hints (low hit rate = need better prompt)

**Edge Cases:**
- Same problem appears in two formats → Normalize key matching
- Hint regenerated due to quality issue → Update cache
- Cache server restarts → Regenerate on-demand

**Dependencies:** REQ-015 (Claude API integration)

**Complexity:** S (1-2 days)

---

## REQ-017: Database Schema

**The system shall maintain a PostgreSQL database with normalized schema for all entities.**

**Acceptance Criteria:**
- [ ] Tables: students, problems, sessions, responses, streaks, admins
- [ ] students: telegram_id, name, grade, language, created_at, updated_at
- [ ] problems: id, grade, topic, question_bn, question_en, answer, hints[], difficulty
- [ ] sessions: id, student_id, date, problems_attempted, problems_correct, completed_at
- [ ] responses: id, session_id, problem_id, student_answer, is_correct, hints_used, timestamp
- [ ] streaks: student_id, current_streak, longest_streak, last_practice_date, milestones[]
- [ ] All tables have indexes on frequently-queried columns (student_id, date, grade)
- [ ] Foreign key constraints enforced
- [ ] Migrations managed via Alembic
- [ ] Initial migration creates empty schema
- [ ] Data integrity: no orphaned records

**Performance Requirements:**
- [ ] Query student profile: <100ms
- [ ] Query daily problems: <200ms
- [ ] Write session: <500ms
- [ ] Streak calculation: <100ms

**Edge Cases:**
- Concurrent write from same student → Handled by transactions
- Data migration from CSV → Idempotent scripts
- Schema changes → Zero-downtime migrations

**Dependencies:** None (foundational)

**Complexity:** M (2-3 days)

---

## REQ-018: Backend API

**The system shall provide a FastAPI backend with REST endpoints for Telegram webhook and admin functions.**

**Acceptance Criteria:**
- [ ] POST /webhook - Receive Telegram updates
- [ ] GET /health - Health check (db + claude connection)
- [ ] POST /admin/stats - Get engagement metrics
- [ ] POST /admin/students - List active students
- [ ] POST /admin/cost - Show AI cost summary
- [ ] All endpoints require authentication (webhook uses token, admin uses admin ID)
- [ ] Response time: <500ms for all endpoints
- [ ] Error handling: Return proper HTTP status codes + JSON errors
- [ ] Logging: All requests logged with timestamp + status
- [ ] CORS: Configured appropriately

**Webhook Format:**
```json
{
  "update_id": 123,
  "message": {
    "message_id": 1,
    "chat": {"id": 987654321, "type": "private"},
    "text": "/start"
  }
}
```

**Edge Cases:**
- Invalid JSON in webhook → Return 400 Bad Request
- Duplicate webhook message → Idempotent handling
- Missing required fields → Clear error message

**Dependencies:** REQ-014 (Telegram integration), REQ-017 (Database)

**Complexity:** M (3-4 days)

---

## REQ-019: Authentication & Security

**The system shall protect sensitive endpoints and prevent unauthorized access.**

**Acceptance Criteria:**
- [ ] Telegram webhook authenticated via token (TELEGRAM_BOT_TOKEN)
- [ ] Admin endpoints require admin Telegram ID (hardcoded for Phase 0, later OAuth)
- [ ] No hardcoded secrets in code (use environment variables)
- [ ] .env file excluded from git (.gitignore)
- [ ] HTTPS enforced (Railway/Render provides SSL)
- [ ] Rate limiting: Max 100 requests per minute per IP
- [ ] Input validation: All user inputs sanitized
- [ ] SQL injection prevention: Use parameterized queries (SQLAlchemy)
- [ ] XSS prevention: Not applicable (no HTML rendering)
- [ ] CSRF protection: Not applicable (stateless API)

**Secrets Managed:**
- [ ] TELEGRAM_BOT_TOKEN - via environment
- [ ] ANTHROPIC_API_KEY - via environment
- [ ] DATABASE_URL - via environment
- [ ] Example file: .env.example (no secrets, just placeholders)

**Edge Cases:**
- Token stolen → Regenerate via BotFather immediately
- API key leaked → Rotate immediately, check usage
- Database password leaked → Change immediately, audit logs

**Dependencies:** REQ-014 (Telegram), REQ-018 (Backend API)

**Complexity:** S (1-2 days)

---

## REQ-020: Error Handling & Logging

**The system shall handle errors gracefully and log all issues for debugging.**

**Acceptance Criteria:**
- [ ] Structured logging: JSON format with timestamp, level, message, context
- [ ] Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- [ ] Logs sent to stdout (Railway/Render captures them)
- [ ] All API errors logged with request context
- [ ] All database errors logged
- [ ] All API calls to Claude logged (prompt tokens, completion tokens)
- [ ] User-facing error messages: Generic ("Something went wrong") with error code
- [ ] Admin error messages: Detailed (full traceback)
- [ ] Log retention: 7 days minimum (Railway/Render default)
- [ ] No sensitive data in logs (no passwords, API keys, etc.)

**Error Scenarios:**
- Database down → Log ERROR, tell user "Something went wrong", show error code
- Claude API timeout → Log ERROR, use fallback hint, tell user "Connection slow, trying again"
- Invalid user input → Log WARNING, tell user "I didn't understand"
- Rate limit hit → Log INFO, tell user "Please wait a moment before continuing"

**Edge Cases:**
- Logging system itself fails → Fail gracefully (print to stderr as last resort)
- Logs fill up disk → Rotate logs (handled by deployment platform)

**Dependencies:** All modules

**Complexity:** S (1-2 days)

---

# LOCALIZATION

## REQ-021: Bengali Language Support

**The system shall support Bengali as the primary language for Phase 0, with English as fallback.**

**Acceptance Criteria:**
- [ ] All user-facing strings available in Bengali (bn) and English (en)
- [ ] Language selected at `/start` (default: Bengali)
- [ ] Preference stored per student in database
- [ ] All subsequent messages use student's language preference
- [ ] Math terminology verified by native Bengali speaker
- [ ] Currency shown as ₹ (Indian Rupee) in Bengali mode
- [ ] Date/time formatted appropriately for region (e.g., 12-hour, no leading zeros)
- [ ] Problem context uses local examples (mango seller, auto-rickshaw, etc.)
- [ ] Streak messages, hints, all encouragement in student's language
- [ ] RTL support not needed (Bengali is LTR)

**String Categories:**
- [ ] Welcome messages
- [ ] Problem statements
- [ ] Hints and explanations
- [ ] Feedback (correct/incorrect)
- [ ] Encouragement
- [ ] Commands and menus
- [ ] Error messages
- [ ] Admin messages

**Example - English:**
```
Good morning! Ready for today's math challenge?
A shopkeeper buys 15 mangoes for Rs. 300...
```

**Example - Bengali:**
```
শুভ সকাল! আজকের গণিত চ্যালেঞ্জের জন্য প্রস্তুত?
একজন দোকানদার 15টি আম ₹300 এর জন্য ক্রয় করেন...
```

**Edge Cases:**
- Missing translation → Use English as fallback
- Student changes language mid-session → Switch all future messages
- Mixed-script input from user → Handle gracefully

**Dependencies:** REQ-014 (Telegram integration)

**Complexity:** S (2 days)

---

## REQ-022: Curriculum Alignment

**The system shall align problem content to West Bengal Board of Secondary Education (WBBSE) Grade 7 curriculum.**

**Acceptance Criteria:**
- [ ] Topics covered: Number Systems, Profit & Loss, Fractions, Decimals, Percentages, Geometry, Algebra Intro
- [ ] Problem difficulty matches grade level standards
- [ ] Topics sequenced in order of WBBSE syllabus
- [ ] All problems verified against official WBBSE curriculum document
- [ ] Curriculum mapping document created (REQ-005 acceptance)
- [ ] Problems not in curriculum excluded
- [ ] Curriculum updates reflected in content within 1 month

**Curriculum Mapping:**
| Week | Topic | Problems | WBBSE Chapter |
|------|-------|----------|---------------|
| 1-2 | Number Systems | 70 | Chap 1-2 |
| 3-4 | Profit & Loss | 70 | Chap 5 |
| etc. | ... | ... | ... |

**Edge Cases:**
- Curriculum changes → Update content
- Local variation (different state) → Add regional variant (Phase 1)

**Dependencies:** REQ-005 (Content curation)

**Complexity:** S (1-2 days)

---

## REQ-023: Cultural Appropriateness

**The system shall ensure all content is culturally sensitive and appropriate for Indian students.**

**Acceptance Criteria:**
- [ ] Problem contexts: Use familiar scenarios (auto-rickshaw, street vendor, school fees, etc.)
- [ ] Avoid: Religious references, gender stereotypes, controversial topics
- [ ] Names in problems: Mix of Indian names (Rajesh, Priya, Amit, etc.)
- [ ] Currency: Indian Rupee (₹) only
- [ ] Time: 12-hour format with AM/PM
- [ ] All content reviewed by someone familiar with Indian culture
- [ ] Student feedback mechanism to flag inappropriate content (Phase 1)

**Problem Review Checklist:**
- [ ] Context relevant to students' lives?
- [ ] No religious/political content?
- [ ] Inclusive of all genders?
- [ ] Appropriate difficulty for age group?
- [ ] Mathematically accurate?

**Edge Cases:**
- Holidays/festivals affect availability → Plan around them
- Regional language variation → Bengali (West Bengal focus initially)

**Dependencies:** REQ-021 (Language support), REQ-005 (Content curation)

**Complexity:** S (1 day)

---

# TEACHER FEATURES (Phase 1+)

## REQ-024: Teacher Dashboard

**The system shall provide teachers with a dashboard to monitor student progress (Phase 1).**

**Acceptance Criteria:**
- [ ] Teacher login via email/password (Phase 1)
- [ ] Dashboard shows all students in class
- [ ] Metrics per student: Last practice date, current streak, % correct this week
- [ ] Aggregate metrics: Class average performance, most struggled topics
- [ ] Flag: Students not practicing (red), high performers (green)
- [ ] Export: CSV of student data
- [ ] Teacher can add notes per student
- [ ] Teacher can set homework (Phase 1)
- [ ] Privacy: Teachers only see their own class(es)

**Phase 0 Note:** Manual tracking via spreadsheet; no web interface required

**Dependencies:** REQ-001 (Practice sessions), REQ-009 (Streaks)

**Complexity:** L (1-2 weeks for full implementation)

---

## REQ-025: Class Management

**The system shall allow teachers to create and manage class lists (Phase 1).**

**Acceptance Criteria:**
- [ ] Teacher creates class with name and grade level
- [ ] Teacher adds students to class (by name or ID)
- [ ] Teacher removes students from class
- [ ] Multiple classes per teacher supported
- [ ] Class roster changeable throughout year
- [ ] Archive old classes (Phase 1)
- [ ] Share class link for student self-enrollment (Phase 1)

**Phase 0:** Manual addition via shared spreadsheet

**Dependencies:** REQ-024 (Teacher dashboard)

**Complexity:** M (1-2 weeks)

---

## REQ-026: Teacher Communication

**The system shall send teachers weekly summaries of class progress (Phase 1).**

**Acceptance Criteria:**
- [ ] Weekly email/SMS summary every Monday morning
- [ ] Summary includes: Students practiced, avg performance, top/bottom performers
- [ ] Alert: Students at risk (no practice for 3+ days)
- [ ] Teacher can request immediate report
- [ ] Customizable frequency (weekly, daily, manual only)
- [ ] Include action items: "These 3 students need intervention"

**Phase 0:** Manual email by project coordinator

**Dependencies:** REQ-024 (Teacher dashboard)

**Complexity:** M (1 week)

---

# COMMUNITY FEATURES

## REQ-027: Community Champions

**The system shall identify and empower community leaders to promote Dars locally (Phase 0-1).**

**Acceptance Criteria:**
- [ ] Champion profile: Name, area, students recruited
- [ ] Champions can see their local students' progress (aggregate only)
- [ ] Recognition: Public leaderboard of top champions
- [ ] Impact metrics: "You've helped 50 students!"
- [ ] Champion can message all their students at once (Phase 1)
- [ ] Compensation: Recognition + incentives (TBD per region)
- [ ] Phase 0: Identify 2-3 champions in Kolkata

**Phase 0 Implementation:**
- [ ] Manual identification and onboarding
- [ ] Simple WhatsApp group for champions
- [ ] Weekly check-in calls

**Dependencies:** REQ-001 (Practice sessions)

**Complexity:** M (1 week)

---

## REQ-028: Referral System

**The system shall track and reward students who refer friends (Phase 1).**

**Acceptance Criteria:**
- [ ] Student generates shareable referral code
- [ ] New student enters code on signup
- [ ] Referrer gets bonus XP or badge
- [ ] Referral tracked in database
- [ ] Leaderboard: Top referrers (Phase 1)

**Phase 0:** Not required

**Dependencies:** None (future feature)

**Complexity:** S (1-2 days)

---

# OPERATIONS & ADMIN

## REQ-029: Cost Tracking & Monitoring

**The system shall track all operational costs with alerts if approaching budget.**

**Acceptance Criteria:**
- [ ] Log every Claude API call with tokens used and cost
- [ ] Daily cost aggregation per student
- [ ] Weekly cost report to admin
- [ ] Target: <$0.10/student/month
- [ ] Alert: If weekly average > $0.15/month extrapolated
- [ ] Dashboard shows: Total costs, cost per student, cost per session
- [ ] Breakdown: AI costs vs infrastructure costs
- [ ] Identify expensive operations (e.g., repeated hint generation)

**Cost Formula:**
```
Claude Haiku: $0.80 per 1M input tokens, $0.40 per 1M output tokens
WhatsApp: $0.005 per conversation
SMS: $0.01 per message (future)
Infrastructure: ~$5/month fixed (Railway), ~$0.10 per student per month storage
```

**Alerts:**
- [ ] Weekly report with trend
- [ ] Alert if total >$0.15/month extrapolated
- [ ] Alert if single API call returns >1000 tokens (possible infinite loop)

**Edge Cases:**
- API call fails (retry) → Don't double-count cost
- API returns partial response → Still count tokens used
- Cached hint used (no API call) → $0 cost

**Dependencies:** REQ-015 (Claude integration), REQ-017 (Database)

**Complexity:** M (2-3 days)

---

## REQ-030: Admin Commands

**The system shall provide admin with utility commands to manage the platform.**

**Acceptance Criteria:**
- [ ] `/admin stats` - Total students, active this week, avg streak
- [ ] `/admin students <grade>` - List all students in grade
- [ ] `/admin cost` - Week-to-date cost, daily average, projections
- [ ] `/admin send_announcement <message>` - Send to all students (Phase 1)
- [ ] Admin identification: Hardcoded Telegram IDs (Phase 0), OAuth (Phase 1)
- [ ] All admin commands logged
- [ ] Error if non-admin tries admin command

**Response Format:**
```
📊 STATS
─────────
Total Students: 50
Active This Week: 42 (84%)
Avg Streak: 7.2 days
Avg Problems/Session: 4.8

💰 COSTS
─────────
Week-to-Date: $1.23
Daily Average: $0.18
Projected (Month): $7.80
Per Student: $0.16 [⚠️ Over budget!]
```

**Edge Cases:**
- No students yet → Show "No data"
- Command syntax error → Clear error message

**Dependencies:** REQ-018 (Backend API), REQ-029 (Cost tracking)

**Complexity:** S (2 days)

---

## REQ-031: Health Check Endpoint

**The system shall provide a health check endpoint for monitoring uptime.**

**Acceptance Criteria:**
- [ ] GET /health returns 200 if system healthy
- [ ] Checks: Database connection, Claude API reachability
- [ ] Response time: <500ms
- [ ] Return JSON: `{"status": "ok", "db": "ok", "claude": "ok"}`
- [ ] Can be used for automated monitoring (Pingdom, etc.)
- [ ] Fails fast if dependent service down

**Response Examples:**
```json
// Healthy
{"status": "ok", "db": "ok", "claude": "ok", "timestamp": "2026-01-28T10:00:00Z"}

// Unhealthy
{"status": "error", "db": "timeout", "claude": "ok", "timestamp": "2026-01-28T10:00:00Z"}
```

**Edge Cases:**
- Database down → /health returns 500 Service Unavailable
- Claude API slow but responsive → /health returns 200 (API will retry)
- Network timeout → Return 500 after 2 second wait

**Dependencies:** REQ-017 (Database), REQ-015 (Claude API)

**Complexity:** S (1 day)

---

## REQ-032: Deployment & Scaling

**The system shall be deployable to production with automatic scaling.**

**Acceptance Criteria:**
- [ ] Deployable to Railway or Render (simple platforms)
- [ ] Environment variables configured via dashboard (no secrets in repo)
- [ ] Database: PostgreSQL managed service (Railway Postgres or similar)
- [ ] Auto-scaling: 0-10 instances based on load
- [ ] SSL: Automatic via platform
- [ ] Monitoring: Platform-native logging (accessible via dashboard)
- [ ] CI/CD: GitHub Actions workflow for validation + deploy
- [ ] Rollback: One-click previous version
- [ ] Estimated cost: $5-10/month fixed + $0.10/student/month variable

**Deployment Checklist:**
- [ ] Code pushed to GitHub
- [ ] GitHub Actions validates (7-stage pipeline)
- [ ] If pass → Deploy to staging
- [ ] Manual QA
- [ ] Deploy to production

**Phase 0 Plan:**
- [ ] Deploy to Railway with PostgreSQL add-on
- [ ] Webhook URL: https://dars.railway.app/webhook
- [ ] Admin URL: https://dars.railway.app/admin
- [ ] Estimated cost: $5/month + $0.03/student/month

**Dependencies:** REQ-019 (Security), REQ-031 (Health check)

**Complexity:** M (2-3 days)

---

## REQ-033: Disaster Recovery & Backups

**The system shall implement backup and recovery procedures (Phase 0-1).**

**Acceptance Criteria:**
- [ ] Daily database backups (automatic via Railway)
- [ ] Backup retention: 14 days minimum
- [ ] Recovery time objective (RTO): 1 hour
- [ ] Recovery point objective (RPO): 1 day
- [ ] Tested recovery: Monthly test of restore procedure
- [ ] Documented runbook for manual recovery
- [ ] Backup stored separately from production (different region, different account)
- [ ] Sensitive data: Encrypted at rest

**Phase 0:**
- [ ] Automatic backups via Railway (included in service)
- [ ] Weekly manual backup export to secure location
- [ ] Tested restore monthly

**Phase 1:**
- [ ] Automated backup verification
- [ ] Alerts if backup fails

**Edge Cases:**
- Production database corrupted → Restore from previous day's backup
- Ransomware attack → Disconnect all instances, restore from backup
- Accidental data deletion → Restore specific table from backup

**Dependencies:** REQ-017 (Database), REQ-032 (Deployment)

**Complexity:** M (1 week)

---

# WEB UI & DASHBOARDS

## REQ-034: Admin Web Dashboard (Phase 0)

**The system shall provide a simple web-based admin dashboard for monitoring platform health and managing operations.**

**Acceptance Criteria:**
- [ ] Accessible at `https://dars.railway.app/admin` (requires login with admin ID)
- [ ] Real-time statistics: Total students, active this week, avg streak, total sessions
- [ ] Cost summary: Week-to-date, daily average, per-student cost, trend chart
- [ ] Student list: Searchable by name, grade, telegram_id
- [ ] Per-student view: Streak, problems attempted, accuracy %, last practice date
- [ ] Problem library: Count by topic, difficulty, language
- [ ] Recent activity log: Last 20 actions (practice sessions, errors)
- [ ] Simple charts: Line graph (daily students), bar graph (topics)
- [ ] Mobile responsive (works on tablets in field)
- [ ] No fancy frameworks: Use simple HTML + CSS + vanilla JS (keep it light)

**Phase 0 Implementation:**
- [ ] Built with FastAPI templates (Jinja2 + static files)
- [ ] Simple Bootstrap CSS for styling
- [ ] Data fetched from REST API endpoints
- [ ] Auto-refresh every 30 seconds

**Tech Stack:**
- [ ] Backend: FastAPI Jinja2 templates
- [ ] Frontend: HTML5, CSS3, vanilla JavaScript
- [ ] Charts: Chart.js library (lightweight)
- [ ] No React/Vue/build tools (keep deployment simple)

**Screenshots (Phase 0):**
```
┌─────────────────────────────────────────┐
│         DARS ADMIN DASHBOARD            │
├─────────────────────────────────────────┤
│ Stats  |  Cost  |  Students  |  Problems│
├─────────────────────────────────────────┤
│                                         │
│  Total Students: 42                     │
│  Active This Week: 35 (83%)             │
│  Avg Streak: 7.2 days                   │
│                                         │
│  This Week Cost: $1.23                  │
│  Per Student: $0.16 [⚠️ OVER BUDGET]    │
│                                         │
│  [Recent Activity Log]                  │
│  Today 10:30: Student 123 completed     │
│  Today 10:15: Student 456 completed     │
│  ...                                    │
└─────────────────────────────────────────┘
```

**Edge Cases:**
- No data yet → Show "No data available"
- API timeout → Show last cached data, retry in background
- Auth failure → Redirect to login with clear message
- Permission denied (non-admin) → Clear error message

**Dependencies:** REQ-018 (Backend API), REQ-029 (Cost tracking), REQ-030 (Admin commands)

**Complexity:** M (2-3 days)

---

## REQ-035: Teacher Dashboard (Phase 1)

**The system shall provide teachers with a comprehensive web dashboard to monitor class progress and manage student learning.**

**Acceptance Criteria:**
- [ ] Accessible at `https://dars.railway.app/teacher` (requires teacher account)
- [ ] Teacher login: Email + password (OAuth Phase 2)
- [ ] My Classes: List of classes teacher manages
- [ ] Class View:
  - [ ] Student roster: Name, enrollment date, status (active/inactive)
  - [ ] Class metrics: Avg streak, avg accuracy, total sessions, weekly engagement
  - [ ] Student performance table: Name, current streak, this week's accuracy %, last practice date
  - [ ] Color coding: Green (engaged), yellow (at risk), red (not practicing)
- [ ] Student Detail View:
  - [ ] Streak history (last 30 days calendar)
  - [ ] Performance graph (accuracy trend)
  - [ ] Topics mastered vs struggling
  - [ ] Recent practice sessions (what problems, accuracy, time spent)
  - [ ] Teacher notes field (free-form notes about student)
- [ ] Reports:
  - [ ] Class summary report (download as PDF)
  - [ ] Individual student report (download as PDF)
  - [ ] Export class data as CSV
- [ ] Alerts:
  - [ ] Students not practicing for 3+ days
  - [ ] Students struggling with specific topics
  - [ ] High performers (for recognition)
- [ ] Communication:
  - [ ] Send announcement to whole class via Telegram
  - [ ] Send individual message to student
  - [ ] Email parent (Phase 2)
- [ ] Class Management:
  - [ ] Add student (by phone number or share invite link)
  - [ ] Remove student
  - [ ] Set custom practice schedule (e.g., no weekend practice)
- [ ] Responsive: Works on desktop, tablet, mobile

**Tech Stack:**
- [ ] Frontend: React or Vue.js (modern UI framework)
- [ ] Backend: FastAPI REST API
- [ ] Charts: Chart.js or Plotly (for graphs)
- [ ] Authentication: JWT tokens
- [ ] Database: PostgreSQL (existing)

**Dashboard Layout:**
```
┌──────────────────────────────────────────────┐
│  DARS TEACHER DASHBOARD                     │
├──────────────────────────────────────────────┤
│ Logout | My Classes | Reports | Help        │
├──────────────────────────────────────────────┤
│                                              │
│  CLASS: Grade 7-A (25 Students)              │
│                                              │
│  📊 Class Metrics                            │
│  ├─ Avg Streak: 6.5 days                     │
│  ├─ Avg Accuracy: 72%                        │
│  ├─ Active This Week: 21/25 (84%)            │
│  └─ Total Sessions: 342                      │
│                                              │
│  ⚠️ At Risk (Not practiced in 3+ days)       │
│  ├─ Rajesh (5 days)                          │
│  ├─ Priya (4 days)                           │
│  └─ Amit (3 days)                            │
│                                              │
│  📈 Student Performance Table                │
│  ├─ Name | Streak | This Week | Last       │
│  ├─ Ananya | 12 | 88% | Today ✓             │
│  ├─ Arjun | 3 | 65% | Yesterday             │
│  ├─ [View more...]                           │
│                                              │
│  [Download Report] [Send Announcement]      │
└──────────────────────────────────────────────┘
```

**Phase 1 Implementation:**
- [ ] User management: Teacher signup/login
- [ ] Multi-class support: Teachers can manage multiple classes
- [ ] Advanced reporting: Statistical analysis

**Edge Cases:**
- No students in class → Show "No students yet"
- Student transferred to different class → Archive old enrollment
- Teacher wants to see previous year's class → Archive feature
- Large class (>100 students) → Pagination and filtering

**Dependencies:** REQ-024 (Teacher features), REQ-018 (Backend API)

**Complexity:** L (1-2 weeks)

---

## REQ-036: Content Management Interface (Phase 1)

**The system shall provide an interface for admins to add, edit, and manage math problems without writing code.**

**Acceptance Criteria:**
- [ ] Accessible at `https://dars.railway.app/content` (requires admin/editor role)
- [ ] Problem List:
  - [ ] Filterable by grade, topic, difficulty, language
  - [ ] Sortable by creation date, edit date, usage count
  - [ ] Search by question text or answer
  - [ ] Bulk actions: Delete, change difficulty, change topic
- [ ] Create Problem Form:
  - [ ] Grade level (6, 7, 8)
  - [ ] Topic (dropdown from predefined list)
  - [ ] Subtopic (optional, free-form)
  - [ ] Question (Bengali + English)
  - [ ] Answer (numeric or text)
  - [ ] Hint 1, Hint 2, Hint 3 (Bengali + English)
  - [ ] Difficulty (1=Easy, 2=Medium, 3=Hard)
  - [ ] Variables (optional, for randomized problems)
  - [ ] Tags (for filtering)
  - [ ] Preview (shows formatted problem + hints)
  - [ ] Save as Draft or Publish
- [ ] Edit Problem:
  - [ ] Full form editing
  - [ ] Version history (who changed what, when)
  - [ ] Rollback to previous version
  - [ ] Track usage (how many students solved this)
- [ ] Bulk Upload:
  - [ ] CSV template download
  - [ ] CSV upload (parse and validate)
  - [ ] Preview changes before commit
  - [ ] Error reporting (line-by-line feedback)
- [ ] Problem Library Stats:
  - [ ] Total problems: 280 (Phase 0 target)
  - [ ] By grade: 7th grade - 95 problems, etc.
  - [ ] By topic: Profit & Loss - 40 problems, etc.
  - [ ] Coverage: Which topics have >20 problems (good), which need more (red flag)
- [ ] Quality Control:
  - [ ] Mark problem for review (flag quality issues)
  - [ ] Editor notes (for content team)
  - [ ] Publish/draft status per language

**Tech Stack:**
- [ ] Frontend: React or Vue.js
- [ ] Form validation: JavaScript library (Vuelidate, React-hook-form)
- [ ] Text editor: Simple textarea, no WYSIWYG needed
- [ ] File upload: Drop zone UI

**Problem Editor Screenshot:**
```
┌───────────────────────────────────────────────┐
│  ADD/EDIT PROBLEM                             │
├───────────────────────────────────────────────┤
│                                               │
│  Grade: [7 ▼]  Topic: [Profit & Loss ▼]      │
│  Difficulty: [Medium ▼]                       │
│                                               │
│  Question (Bengali):                          │
│  [একজন দোকানদার 15টি আম ₹300 এর জন্য...]  │
│                                               │
│  Question (English):                          │
│  [A shopkeeper buys 15 mangoes for Rs. 300...] │
│                                               │
│  Correct Answer:                              │
│  [75 rupees]                                  │
│                                               │
│  Hint 1 (Bengali):                            │
│  [প্রথম, প্রতিটি আমের খরচ কী?]             │
│                                               │
│  Hint 1 (English):                            │
│  [First, what is the cost of each mango?]   │
│                                               │
│  [+ Add Hint 2] [+ Add Hint 3]               │
│                                               │
│  ✓ Preview Problem                            │
│  [Save as Draft] [Publish]                    │
│                                               │
└───────────────────────────────────────────────┘
```

**Phase 1 Implementation:**
- [ ] Start with manual entry
- [ ] Bulk CSV import for Phase 0 problems
- [ ] Later: AI-assisted hint generation, problem difficulty suggestions

**Edge Cases:**
- Problem has multiple correct answers → Accept comma-separated list
- Hint length too long → Warn user, suggest truncation
- Import CSV has errors → Show row-by-row error report
- Problem not used by any students yet → Allow safe deletion

**Dependencies:** REQ-005 (Content library), REQ-018 (Backend API)

**Complexity:** M (1 week)

---

## REQ-037: Community Champion Dashboard (Phase 1)

**The system shall provide champions with a view of their students' collective progress.**

**Acceptance Criteria:**
- [ ] Accessible at `https://dars.railway.app/champion` (requires champion account)
- [ ] Champion login: Phone number + OTP (simple, no email required)
- [ ] Overview:
  - [ ] Total students recruited: "You've helped 47 students!"
  - [ ] Active this week: 39 students (83%)
  - [ ] Avg streak: 6.8 days
  - [ ] Avg accuracy: 71%
- [ ] My Students (List):
  - [ ] Name, phone, enrollment date, current streak, last practice date
  - [ ] Filter: Active/inactive, streak range, accuracy range
  - [ ] Color coding: Green (engaged), yellow (at risk), red (not practicing)
- [ ] Leaderboard:
  - [ ] Top champions by students recruited
  - [ ] Top champions by student engagement
  - [ ] Your rank nationally
- [ ] Engagement Tracking:
  - [ ] Weekly summary: X% of my students practiced this week
  - [ ] Trend graph: Student engagement over time
- [ ] Communication:
  - [ ] Send reminder to at-risk students (via Telegram, template message)
  - [ ] Celebrate milestones: "Congratulate Rajesh on 14-day streak!"
- [ ] Incentive Tracking:
  - [ ] Points earned (if incentive program exists)
  - [ ] Recognition badge
  - [ ] Referral bonus tracking

**Tech Stack:**
- [ ] Mobile-first responsive design (champions use phones)
- [ ] Simple, lightweight UI
- [ ] WhatsApp-integrated message templates (Phase 1)

**Screenshot:**
```
┌────────────────────────────────┐
│  MY IMPACT (Champion View)     │
├────────────────────────────────┤
│                                │
│  🌟 Students Helped: 47        │
│     Active This Week: 39 (83%) │
│     Avg Streak: 6.8 days       │
│                                │
│  🏆 National Rank: #12         │
│                                │
│  📊 This Week Summary          │
│     83% of my students          │
│     practiced this week         │
│                                │
│  ⚠️ At Risk (3+ days no...):  │
│     • Rajesh                   │
│     • Priya                    │
│     [Send Reminder]            │
│                                │
│  ✨ Celebrate!                 │
│     Arjun hit 14-day streak!   │
│     [Send Congrats Message]    │
│                                │
└────────────────────────────────┘
```

**Phase 1 Implementation:**
- [ ] WhatsApp integration for messaging students
- [ ] Incentive program (points, badges, rewards)

**Edge Cases:**
- Champion hasn't recruited students yet → Show onboarding guide
- Student churned → Remove from list, show "graduated"
- Champion requests refund/dispute → Manual process

**Dependencies:** REQ-027 (Community champions), REQ-018 (Backend API)

**Complexity:** M (1 week)

---

## REQ-038: Analytics Dashboard (Phase 1)

**The system shall provide data analytics for product managers and researchers to understand learning patterns.**

**Acceptance Criteria:**
- [ ] Accessible at `https://dars.railway.app/analytics` (requires analyst/manager role)
- [ ] Metrics Overview:
  - [ ] Total students: 50 (Phase 0), 500+ (Phase 1)
  - [ ] Weekly active rate: X%
  - [ ] Average streaks: distribution chart
  - [ ] Accuracy by topic: Which topics hardest? easiest?
  - [ ] Retention curve: Week 1 → Week 8 survival rates
- [ ] Learning Analytics:
  - [ ] Time-to-mastery: How many sessions needed to reach 80% accuracy?
  - [ ] Problem difficulty: Which problems are most/least difficult?
  - [ ] Hint usage: Average hints needed per topic
  - [ ] Drop-off analysis: Where do students quit? (problem X has 40% dropout)
- [ ] Engagement Trends:
  - [ ] New students per day
  - [ ] Daily active users (DAU) trend
  - [ ] Churn rate by cohort (Week 1 cohort, Week 2 cohort)
  - [ ] Reactivation: % of inactive students who come back
- [ ] Demographic Analysis:
  - [ ] Students by grade
  - [ ] Language preference distribution
  - [ ] Geographic distribution (if captured)
  - [ ] Gender breakdown (if captured)
- [ ] Exports:
  - [ ] Download all data as CSV
  - [ ] Export selected charts as images
  - [ ] Scheduled email reports (Phase 1)
- [ ] Heatmaps:
  - [ ] Student activity by hour (when do students practice?)
  - [ ] Performance heatmap (which problems × which students struggle?)

**Tech Stack:**
- [ ] Charting: Plotly or D3.js (advanced analytics)
- [ ] Data aggregation: PostgreSQL queries + caching
- [ ] Frontend: React + visualization library

**Use Cases:**
- Product manager checks DAU to plan scaling
- Researcher analyzes mastery patterns to improve curriculum
- Marketing team tracks cohort retention to refine acquisition strategy

**Phase 1 Implementation:**
- [ ] Start with basic metrics
- [ ] Expand to advanced analytics

**Edge Cases:**
- Insufficient data (Phase 0) → Show "Data will appear after Week 2"
- Anomalies (student with 1000 sessions/day) → Flag for investigation

**Dependencies:** REQ-017 (Database), REQ-018 (Backend API)

**Complexity:** M (1-2 weeks)

---

## REQ-039: Responsive Design

**The system shall ensure all web UIs are responsive and accessible on desktop, tablet, and mobile devices.**

**Acceptance Criteria:**
- [ ] Desktop (1920×1080): Full layout, all features visible
- [ ] Tablet (768×1024): Optimized layout, navigation adapts
- [ ] Mobile (375×667): Mobile-first layout, touch-friendly buttons
- [ ] All pages tested on:
  - [ ] Chrome (latest 2 versions)
  - [ ] Safari (latest 2 versions)
  - [ ] Firefox (latest 2 versions)
  - [ ] Edge (latest 2 versions)
- [ ] Accessibility:
  - [ ] Keyboard navigation (all interactive elements reachable via tab)
  - [ ] Screen reader compatible (semantic HTML)
  - [ ] Color contrast: WCAG AA minimum (4.5:1 for text)
  - [ ] Font size: Minimum 14px
  - [ ] Touch targets: Minimum 44×44px
- [ ] Performance:
  - [ ] Page load: <3 seconds on 4G
  - [ ] Time to interactive: <5 seconds
  - [ ] No layout shifts (Cumulative Layout Shift <0.1)
- [ ] CSS Framework: Bootstrap 5 (lightweight, responsive)

**Testing:**
- [ ] Manual testing on real devices
- [ ] Automated testing: Lighthouse, WAVE
- [ ] Cross-browser testing: BrowserStack

**Edge Cases:**
- Very slow network (2G) → Progressive enhancement, show loading states
- Very old browser (IE11) → Graceful degradation, show unsupported message
- Touch device (iPad) → Hover states converted to click handlers

**Dependencies:** All UI requirements (REQ-034 to REQ-038)

**Complexity:** S (1-2 days per dashboard, included in other estimates)

---

## REQ-040: Web UI Authentication & Authorization

**The system shall secure all web dashboards with authentication and role-based access control.**

**Acceptance Criteria:**
- [ ] Admin Dashboard:
  - [ ] Hardcoded admin Telegram IDs (Phase 0)
  - [ ] Login via Telegram (one-click) - Phase 1
  - [ ] Session tokens: Expire after 24 hours
- [ ] Teacher Dashboard:
  - [ ] Email + password signup (Phase 1)
  - [ ] Verify email before access
  - [ ] Password reset via email
  - [ ] 2FA optional (Phase 2)
- [ ] Champion Dashboard:
  - [ ] Phone number + OTP signup (Phase 1)
  - [ ] Session expires after 30 days
  - [ ] No password needed (OTP on each login)
- [ ] Analytics Dashboard:
  - [ ] Email + password (same as teacher, subset can access)
  - [ ] Role: analyst, manager, researcher
- [ ] Authorization:
  - [ ] Teachers only see their own classes
  - [ ] Champions only see their own students
  - [ ] Admins see everything
  - [ ] Analysts cannot edit data, only view
  - [ ] Prevent direct URL access to other user's data
- [ ] Security:
  - [ ] HTTPS enforced
  - [ ] CSRF tokens on all forms
  - [ ] Rate limiting: 5 failed logins → lockout for 15 minutes
  - [ ] Secure cookies: HttpOnly, Secure, SameSite
  - [ ] No sensitive data in URL (use POST)

**Tech Stack:**
- [ ] Frontend: Store JWT token in secure HttpOnly cookie
- [ ] Backend: JWT validation on every request
- [ ] OTP: Twilio or AWS SNS (Phase 1)
- [ ] Email: SendGrid or similar (Phase 1)

**Edge Cases:**
- Token expired mid-session → Redirect to login with helpful message
- User tries to access another user's data → 403 Forbidden
- Admin account compromised → Manual password reset process
- Teacher account deleted → Soft delete (preserve historical data)

**Dependencies:** REQ-019 (Security), All UI dashboards

**Complexity:** M (2-3 days)

---

# REQUIREMENTS TRACEABILITY

## Dependencies Matrix

```
REQ-001 (Daily Practice)
├── REQ-005 (Content Library)
├── REQ-008 (Problem Selection)
├── REQ-004 (Adaptive Difficulty)
└── REQ-007 (Session Persistence)

REQ-002 (Socratic Hints)
├── REQ-015 (Claude API)
├── REQ-016 (Prompt Caching)
└── REQ-003 (Answer Evaluation)

REQ-009 (Streak Tracking)
├── REQ-010 (Streak Display)
├── REQ-011 (Reminders)
└── REQ-012 (Milestones)

REQ-021 (Bengali Language)
├── REQ-001 (Daily Practice)
├── REQ-002 (Hints)
└── REQ-005 (Content)

REQ-022 (Curriculum Alignment)
└── REQ-005 (Content Library)

REQ-029 (Cost Tracking)
└── REQ-015 (Claude API)

REQ-032 (Deployment)
├── REQ-019 (Security)
└── REQ-031 (Health Check)
```

---

## Complexity Summary

| Complexity | Count | Total Days |
|-----------|-------|-----------|
| **S** (1-2 days) | 15 | 15-30 |
| **M** (2-4 days) | 16 | 32-64 |
| **L** (1-2 weeks) | 3 | 5-10 |
| **XL** (Needs breakdown) | 0 | 0 |
| **TOTAL PHASE 0** | 33 | **52-104 days** |

**Note:** Phase 0 focuses on top 25 requirements. Phase 1 adds teacher/community features.

---

## Implementation Roadmap

### Phase 0: MVP Validation (8 weeks, 50 students)

| Week | Focus | Requirements | Key Milestones |
|------|-------|--------------|-----------------|
| 1-2 | Foundation | REQ-014, 017, 018, 019 | Backend + DB online, Telegram bot created |
| 2-3 | Core Learning | REQ-001, 008, 005, 003 | Daily practice works, problems curated |
| 3-4 | Hints | REQ-002, 015, 016 | Socratic hints live, caching working |
| 4-5 | Gamification | REQ-009, 010, 011, 012 | Streaks working, reminders sent |
| 5-6 | Localization | REQ-021, 022, 023 | Bengali live, curriculum aligned |
| 6-7 | Operations | REQ-029, 030, 031, 032 | Cost tracking live, deployed |
| 7-8 | Polish & Pilot | Testing, documentation, 50 students onboard | Ready for evaluation |

**Go/No-Go for Phase 1:**
- ✓ >50% weekly engagement
- ✓ >40% retention at week 4
- ✓ Cost <$0.15/student/month
- ✓ Positive teacher feedback
- ✓ At least one "aha moment" story

### Phase 1: Scale & Learn (3 months, 500 students)

- Implement REQ-024, 025, 026 (Teacher dashboard)
- Implement REQ-027 (Community champions)
- Add to WhatsApp Business API (migration from Telegram)
- Add Science subject
- Implement analytics

### Phase 2: Grow (6 months, 5,000 students)

- Additional subjects (English, regional languages)
- Native mobile app (if Telegram becomes bottleneck)
- Study groups (Phase 2+)
- Parent updates (Phase 2+)

---

## Success Metrics by Requirement

| REQ | Metric | Target |
|-----|--------|--------|
| REQ-001 | Daily sessions completed | >50% of students |
| REQ-002 | Hints used per wrong answer | 1-2 avg |
| REQ-003 | Answer accuracy | 60% first try |
| REQ-009 | Average streak length | 7+ days |
| REQ-013 | Student satisfaction | 4+/5 stars |
| REQ-014 | Bot response time | <2s |
| REQ-015 | Claude API success rate | 99%+ |
| REQ-021 | Language preference Bengali | 80%+ |
| REQ-029 | Cost per student | <$0.10/month |
| REQ-031 | Health check uptime | 99.5%+ |

---

## Open Questions & Assumptions

### Assumptions

1. **Student Device:** Budget Android phone (Redmi 9A ~$100), 2G/3G connectivity
2. **Practice Frequency:** 1 session per day, ~20 minutes per session
3. **Content Language:** Bengali primary, English fallback
4. **Feedback Latency:** Acceptable delay of up to 5 seconds
5. **Student Age:** 14-16 (Grade 7 students)
6. **Learning Goal:** Math fundamentals (Grades 6-8 curriculum)

### Open Questions (Resolved in Next Phase)

1. **Student Acquisition:** How exactly do we recruit 50 students? (Personal network, NGO partner, school partnership)
2. **Parent Communication:** Should we support parent notifications? (Deferred to Phase 1)
3. **Offline Capability:** Required for Phase 0? (Deferred to Phase 1+)
4. **AI Model Evolution:** Will we use newer models? (Upgrade process in Phase 1)
5. **Internationalization:** When do we expand to Hindi/Urdu? (Phase 1)

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-28 | Product Team | Initial draft from proposal |
| | | | - 33 core requirements |
| | | | - 7-stage validation pipeline |
| | | | - Phase 0/1/2 roadmap |

**Approval:** ✓ Product Manager, ✓ Tech Lead, ✓ Project Manager

---

**Next Steps:**

1. ✓ Requirements approved by stakeholders
2. → Developers begin TASK-001 implementation
3. → Weekly requirement review meetings
4. → Document updates as requirements change
5. → Traceability tracking in GitHub Issues (REQ-XXX tags)
