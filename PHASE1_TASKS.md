# Phase 1 Tasks: Backend & Integration Foundation

**Duration:** Week 1 (5 days of agent work)
**Complexity:** M (2-3 days backend + API) + M (2-3 days security hardening) = **4-6 days total**
**Status:** Ready for implementation

**Demo Target:** "Admin can see Telegram bot responds to `/start`, database is connected, health endpoint returns 200, all security checks pass"

---

## Task Summary

| Task ID | Task Name | Owner | Duration | Blocking | Status |
|---------|-----------|-------|----------|----------|--------|
| PHASE1-A-1 | Database Schema & Models | Maryam | 2 days | Phase 3+ | 📋 Pending |
| PHASE1-B-1 | FastAPI App Structure | Jodha | 2 days | Phase 3+ | 📋 Pending |
| PHASE1-C-1 | Security Hardening (SEC-001-008) | Noor | 2-3 days | **Phase 3** | 📋 **BLOCKING** |

---

## Agent A: Database Schema & Models (Maryam)

**Task ID:** PHASE1-A-1
**Owner:** Maryam (Database & ORM Expert)
**Duration:** ~2 days
**Blocker:** None
**Blocked by:** None

### Deliverables

- [ ] **PHASE1-A-1.1** - Create 6 models (Student, Problem, Session, Response, Streak, CostRecord)
- [ ] **PHASE1-A-1.2** - Design relationships (1-to-Many, Foreign Keys)
- [ ] **PHASE1-A-1.3** - Create Alembic migrations
- [ ] **PHASE1-A-1.4** - Unit tests for models (≥80% coverage)
- [ ] **PHASE1-A-1.5** - Verify with Jodha (imports work for API)

### Detailed Work

#### 1. SQLAlchemy Models (src/models/) [PHASE1-A-1.1]

- [ ] **Base class** (`base.py`)
  - `Base` declarative base with naming conventions
  - `TimestampMixin` for created_at/updated_at
  - `to_dict()` conversion method

- [ ] **Student model** (`student.py`)
  - PK: `student_id` (auto-increment)
  - Unique: `telegram_id` (indexed)
  - Fields: `name`, `grade` (6-8), `language` (bn/en)
  - Relationships: sessions, streak, cost_records
  - Constraints: Grade enum, language enum

- [ ] **Problem model** (`problem.py`)
  - PK: `problem_id`
  - Fields: `question_en`, `question_bn`, `answer`, `difficulty` (1-3)
  - Classification: `grade`, `topic`, `subtopic`
  - Hints: JSON array of 3 hints
  - Methods: `get_question(language)`, `get_hints()`

- [ ] **Session model** (`session.py`)
  - PK: `session_id`
  - FK: `student_id` (cascade delete)
  - Status: enum (IN_PROGRESS, COMPLETED, ABANDONED)
  - Fields: `problem_ids` (JSON), `date`, `expires_at`, `completed_at`
  - Analytics: `total_time_seconds`, `problems_correct`
  - Methods: `is_expired()`, `get_accuracy()`

- [ ] **Response model** (`response.py`)
  - PK: `response_id`
  - FKs: `session_id`, `problem_id`
  - Fields: `student_answer`, `is_correct`, `time_spent_seconds`
  - Hints: `hints_used` (0-3), `hints_viewed` (JSON)
  - Confidence: `confidence_level` enum
  - Evaluation: `evaluated_at` timestamp

- [ ] **Streak model** (`streak.py`)
  - PK: `student_id` (one-to-one)
  - Fields: `current_streak`, `longest_streak`, `last_practice_date`
  - Milestones: `milestones_achieved` (JSON)
  - Methods: `add_milestone()`, `get_next_milestone()`

- [ ] **CostRecord model** (`cost_record.py`)
  - PK: `cost_id`
  - FKs: `student_id`, `session_id` (nullable, SET NULL)
  - Fields: `operation`, `api_provider`, `input_tokens`, `output_tokens`, `cost_usd`
  - Timestamp: `recorded_at` (UTC)

#### 2. Alembic Migrations [PHASE1-A-1.3]

- [ ] Create migration file
  - Auto-detect schema from models
  - Command: `alembic revision --autogenerate -m "Initial schema with all models"`

- [ ] Verify migration
  - Syntax correct
  - Constraints in place
  - Indexes created
  - Foreign keys correct

- [ ] Test migration
  - Apply: `alembic upgrade head`
  - Rollback: `alembic downgrade -1`
  - Both succeed

#### 3. Indexes (Performance)

- [ ] `idx_students_telegram_id` on `students.telegram_id`
- [ ] `idx_sessions_student_id_date` on `sessions(student_id, date)`
- [ ] `idx_responses_session_id` on `responses.session_id`
- [ ] `idx_cost_records_student_id` on `cost_records.student_id`

#### 4. Database Configuration

- [ ] **Production** (Railway PostgreSQL)
  - Connection pooling: 5 base + 10 overflow
  - Pool pre-ping enabled
  - Echo disabled

- [ ] **Testing** (SQLite in-memory)
  - NullPool (avoid connection issues)
  - All tables created fresh

- [ ] **Migrations**
  - Auto-run on app startup (development)
  - Manual for production

#### 5. Testing [PHASE1-A-1.4]

- [ ] Unit tests for all models
  - Test creation, relationships, methods
  - Test constraints (grade 6-8, enums)
  - Test cascading deletes

- [ ] Fixture: `sample_student()`, `sample_problem()`, `sample_session()`

- [ ] Coverage: ≥80% for models

### Success Criteria

- ✅ All 7 models created with correct fields
- ✅ Relationships work (Student → Sessions → Responses, etc.)
- ✅ Alembic migration runs successfully
- ✅ All constraints in place (grade, difficulty, language)
- ✅ Indexes created for performance
- ✅ Unit tests pass (80%+ coverage)
- ✅ Type hints on all code
- ✅ No sensitive data exposed

### Code Review Checklist

- [ ] All models have type hints
- [ ] All fields have documentation
- [ ] Relationships are bidirectional where needed
- [ ] No N+1 query patterns
- [ ] Cascade rules correct
- [ ] Timestamps always UTC
- [ ] Tests cover happy path + edge cases

---

## Agent B: FastAPI App Structure (Jodha)

**Task ID:** PHASE1-B-1
**Owner:** Jodha (FastAPI Backend Expert)
**Duration:** ~2 days
**Blocker:** None
**Blocked by:** Agent A (needs models for imports)

### Deliverables

- [ ] **PHASE1-B-1.1** - Create FastAPI instance + config
- [ ] **PHASE1-B-1.2** - Create 6 route modules (health, webhook, practice, student, streak, admin)
- [ ] **PHASE1-B-1.3** - Implement middleware (CORS, request ID, error handlers)
- [ ] **PHASE1-B-1.4** - Database integration (session dependency)
- [ ] **PHASE1-B-1.5** - Unit tests (≥70% coverage)
- [ ] **PHASE1-B-1.6** - Code review security work from Noor

### Detailed Work

#### 1. Application Setup (src/main.py) [PHASE1-B-1.1]

- [ ] **FastAPI instance**
  ```python
  app = FastAPI(
      title="Dars AI Tutoring Platform",
      version="0.1.0",
      description="AI-powered tutoring platform for Indian students"
  )
  ```

- [ ] **Configuration**
  - Load settings from environment
  - Database connection string
  - API keys (Telegram, Claude)
  - Admin IDs

- [ ] **Lifespan events**
  - Startup: Initialize database connection pool
  - Shutdown: Close connections gracefully

#### 2. Route Modules (src/routes/) [PHASE1-B-1.2]

- [ ] **health.py** - Health check endpoint
  - `GET /health` - Database + Claude status

- [ ] **webhook.py** - Telegram integration
  - `POST /webhook` - Receive Telegram updates

- [ ] **practice.py** - Practice endpoints
  - `GET /practice` - Get 5 daily problems
  - `POST /practice/{problem_id}/answer` - Submit answer
  - `POST /practice/{problem_id}/hint` - Request hint

- [ ] **student.py** - Student profile
  - `GET /student/profile` - Get profile
  - `PATCH /student/profile` - Update profile

- [ ] **streak.py** - Streak tracking
  - `GET /streak` - Get streak info

- [ ] **admin.py** - Admin endpoints
  - `GET /admin/stats` - System stats
  - `GET /admin/students` - Student list
  - `GET /admin/cost` - Cost summary

- [ ] **Root endpoint**
  - `GET /` - API info
  - `GET /docs` - OpenAPI docs (auto-generated)

#### 3. Middleware Setup [PHASE1-B-1.3]

- [ ] **CORS Middleware** (src/main.py)
  - Will be hardened by Noor in SEC-001
  - Placeholder: `allow_origins=["*"]` (marked TODO)

- [ ] **Request ID Middleware** (src/logging/config.py)
  - Add UUID to each request
  - Include in response headers
  - Add to logs

- [ ] **Error Handlers** (src/errors/handlers.py)
  - DarsAPIException handler
  - HTTPException handler
  - Validation error handler
  - Generic exception handler

#### 4. Database Integration [PHASE1-B-1.4]

- [ ] **Session dependency** (src/database.py)
  - `get_session()` - AsyncGenerator for FastAPI Depends()
  - Auto-commit on success
  - Auto-rollback on exception

- [ ] **Database initialization**
  - Create tables on startup (dev only)
  - Run migrations (production)

#### 5. Authentication Dependencies (Placeholder - enhanced by Noor)

- [ ] **Telegram webhook auth** (src/auth/telegram.py)
  - Extract Bearer token
  - Will be enhanced with signature verification

- [ ] **Admin auth** (src/auth/admin.py)
  - Extract X-Admin-ID header
  - Will be enhanced with database verification

- [ ] **Student auth** (src/auth/student.py)
  - Extract X-Student-ID header
  - Will be enhanced with database verification

#### 6. Testing [PHASE1-B-1.5]

- [ ] Unit tests for all endpoints
  - Test 200 responses for health/root
  - Test 404 for missing routes
  - Test authentication (missing headers)
  - Test error handling

- [ ] Fixtures for FastAPI TestClient

- [ ] Coverage: ≥70% for routes

### Success Criteria

- ✅ FastAPI app starts without errors
- ✅ `GET /health` returns 200
- ✅ `POST /webhook` accepts updates (will be verified by Noor)
- ✅ `GET /` returns API info
- ✅ All endpoints have stubs with proper signatures
- ✅ Error handling doesn't crash app
- ✅ Middleware configured
- ✅ Database connection works
- ✅ All unit tests pass (70%+ coverage)
- ✅ OpenAPI docs auto-generated

### Code Review Checklist

- [ ] All route handlers have type hints
- [ ] All responses use Pydantic schemas
- [ ] No print() statements (use logging)
- [ ] Error handling catches specific exceptions
- [ ] Docstrings on all public functions
- [ ] Tests cover happy path + error cases
- [ ] No hardcoded values in code

---

## Agent C: Security Hardening (Noor)

**Task ID:** PHASE1-C-1
**Owner:** Noor (Security & Logging Expert)
**Duration:** 2-3 days
**Blocker:** None
**Blocks:** Phase 3 (Practice endpoints can't go live without this)
**CRITICAL:** Must complete BEFORE Phase 3 begins. Code review required from Jodha.

### Deliverables

- [ ] **PHASE1-C-1.1** - SEC-002: Telegram webhook signature verification
- [ ] **PHASE1-C-1.2** - SEC-001: CORS hardening
- [ ] **PHASE1-C-1.3** - SEC-003: Student database verification (CRITICAL - blocks phase 3)
- [ ] **PHASE1-C-1.4** - SEC-004: Admin authentication enforcement
- [ ] **PHASE1-C-1.5** - SEC-005: Rate limiting (slowapi)
- [ ] **PHASE1-C-1.6** - SEC-006: Sensitive data sanitization in logs
- [ ] **PHASE1-C-1.7** - SEC-007: Input length validation
- [ ] **PHASE1-C-1.8** - SEC-008: Query parameter validation
- [ ] **PHASE1-C-1.9** - Security testing and code review

### Detailed Work - Implementation Order

#### SEC-002: Telegram Webhook Signature Verification [PHASE1-C-1.1]

**Why First:** Webhook must be secure before it's live

- [ ] **Implement header verification** (src/routes/webhook.py)
  ```python
  @router.post("/webhook")
  async def telegram_webhook(request: Request):
      secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
      if not secret_token or secret_token != settings.telegram_secret_token:
          raise HTTPException(status_code=401, detail="Invalid webhook token")
      # ... process update
  ```

- [ ] **Get Telegram secret token** from BotFather
  - Store in `TELEGRAM_SECRET_TOKEN` environment variable
  - Never hardcode

- [ ] **Testing**
  - Test without header → 401
  - Test with wrong token → 401
  - Test with correct token → 200

#### SEC-001: CORS Configuration Hardening [PHASE1-C-1.2]

**Why Second:** Restrict before external testing

- [ ] **Update CORS middleware** (src/main.py)
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["https://dars.railway.app", "http://localhost:3000"],
      allow_credentials=True,
      allow_methods=["GET", "POST", "PATCH"],
      allow_headers=["Content-Type", "Authorization", "X-Student-ID", "X-Admin-ID"],
  )
  ```

- [ ] **Document rationale**
  - Why these origins
  - How to update for different deployment

- [ ] **Testing**
  - Test from allowed origin → CORS headers present
  - Test from forbidden origin → No CORS headers

#### SEC-003: Student Database Existence Verification [PHASE1-C-1.3]

**Why Third:** Required for practice endpoints (Phase 3)

- [ ] **Enhance verify_student()** (src/auth/student.py)
  ```python
  async def verify_student(
      x_student_id: int = Header(...),
      db: AsyncSession = Depends(get_session),
  ) -> int:
      # Existing: validate format
      if x_student_id <= 0:
          raise HTTPException(status_code=400, detail="Invalid student ID")

      # NEW: Query database
      student = await db.execute(
          select(Student).where(Student.telegram_id == x_student_id)
      )
      if not student.scalar_one_or_none():
          raise HTTPException(status_code=404, detail="Student not found")

      return x_student_id
  ```

- [ ] **Apply to all student endpoints**
  - `GET /practice` - `Depends(verify_student)`
  - `POST /practice/{problem_id}/answer` - `Depends(verify_student)`
  - `POST /practice/{problem_id}/hint` - `Depends(verify_student)`
  - `GET /streak` - `Depends(verify_student)`
  - `GET /student/profile` - `Depends(verify_student)`
  - `PATCH /student/profile` - `Depends(verify_student)`

- [ ] **Testing**
  - Valid student ID → Allowed
  - Invalid student ID → 404
  - Missing header → 401
  - Non-integer → 400

#### SEC-004: Admin Authentication Enforcement [PHASE1-C-1.4]

**Why Fourth:** Protect admin endpoints

- [ ] **Enhance verify_admin()** (src/auth/admin.py)
  ```python
  async def verify_admin(x_admin_id: str = Header(...)) -> int:
      # Existing: parse and validate
      try:
          admin_id = int(x_admin_id)
      except ValueError:
          raise HTTPException(status_code=400, detail="Invalid admin ID format")

      # Existing: check hardcoded list
      settings = get_settings()
      if admin_id not in settings.get_admin_ids():
          raise HTTPException(status_code=403, detail="Not authorized")

      return admin_id
  ```

- [ ] **Apply to ALL admin endpoints**
  - `GET /admin/stats` - `Depends(verify_admin)`
  - `GET /admin/students` - `Depends(verify_admin)`
  - `GET /admin/cost` - `Depends(verify_admin)`

- [ ] **Remove placeholder auth checks**
  - Admin endpoints should NOT just accept the header
  - Must call verify_admin() to enforce

- [ ] **Testing**
  - Valid admin ID → Allowed
  - Invalid admin ID → 403
  - Missing header → 401
  - Non-authorized ID → 403

#### SEC-005: Rate Limiting [PHASE1-C-1.5]

**Why Fifth:** Prevent DOS attacks

- [ ] **Install slowapi library**
  ```bash
  pip install slowapi
  ```

- [ ] **Configure rate limiter** (src/main.py)
  ```python
  from slowapi import Limiter
  from slowapi.util import get_remote_address

  limiter = Limiter(key_func=get_remote_address)
  app.state.limiter = limiter
  app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
  ```

- [ ] **Apply global limit**
  - All endpoints: 100 requests/minute per IP
  - `@limiter.limit("100/minute")`

- [ ] **Apply per-endpoint limits**
  - `/practice/{problem_id}/hint` - 10/day per student (most expensive)
  - `@limiter.limit("10/day")`

- [ ] **Error handling**
  - 429 Too Many Requests when limit exceeded
  - Include Retry-After header

- [ ] **Testing**
  - Send 101 requests in 1 minute → 101st returns 429
  - Send 11 hint requests in 1 day → 11th returns 429
  - Different IPs have separate limits

#### SEC-006: Sensitive Data Sanitization in Logs [PHASE1-C-1.6]

**Why Sixth:** Prevent credential leakage

- [ ] **Create sanitization function** (src/logging/config.py)
  ```python
  def sanitize_log_data(data: dict) -> dict:
      """Mask sensitive fields in log data."""
      sensitive_keys = {
          "api_key", "apikey", "token", "secret", "password",
          "admin_id", "x-admin-id", "authorization",
      }
      result = data.copy()
      for key in sensitive_keys:
          if key in result:
              result[key] = "***MASKED***"
      return result
  ```

- [ ] **Apply to all logging**
  - Request logging: sanitize headers, query params
  - Error logging: sanitize exception details
  - Database logging: sanitize query parameters

- [ ] **Test with real values**
  - Log request with API key → Appears as ***MASKED***
  - Log error with token → Appears as ***MASKED***
  - Grep logs → No plain secrets found

- [ ] **Testing**
  - Log with api_key=secret123 → Appears as ***MASKED***
  - Log with admin_id=456 → Appears as ***MASKED***
  - Verify no false positives (allow legitimate field names)

#### SEC-007: Input Length Validation [PHASE1-C-1.7]

**Why Seventh:** Prevent DOS via huge payloads

- [ ] **Add max_length to string fields** (src/schemas/)
  ```python
  class AnswerRequest(BaseModel):
      session_id: int
      student_answer: str = Field(..., max_length=500)  # NEW
      time_spent_seconds: int | None = Field(None, ge=0)
  ```

- [ ] **Applied to all string inputs**
  - `student_answer` (max 500)
  - `feedback` (max 1000)
  - All other text fields (reasonable limits)

- [ ] **Testing**
  - Submit string under limit → Accepted
  - Submit string over limit → 422 Validation Error
  - Test all string fields

#### SEC-008: Query Parameter Validation [PHASE1-C-1.8]

**Why Eighth:** Prevent injection and optimization bypass

- [ ] **Add bounds to query parameters** (src/routes/admin.py)
  ```python
  @router.get("/admin/students")
  async def get_admin_students(
      page: int = Query(1, ge=1, le=1000),  # NEW: upper bound
      limit: int = Query(20, ge=1, le=100),  # Already has bounds
      grade: int | None = Query(None, ge=6, le=8),  # Already has bounds
  ):
      ...
  ```

- [ ] **Applied to all query parameters**
  - Page number: 1 ≤ page ≤ 1000
  - Limit: 1 ≤ limit ≤ 100
  - Grade: 6 ≤ grade ≤ 8 (if present)
  - Validation: `regex` pattern for string params

- [ ] **Testing**
  - Valid values → Accepted
  - Values outside bounds → 422 Validation Error
  - Test edge cases (0, -1, 1001, etc.)

### Security Test Plan

**Run these tests after implementation:**

```bash
# Test CORS (SEC-001)
curl -H "Origin: https://evil.com" http://localhost:8000/health
# Should NOT have Access-Control-Allow-Origin header

# Test student verification (SEC-003)
curl http://localhost:8000/practice -H "X-Student-ID: 99999"
# Should return 404 (student not found)

# Test admin auth (SEC-004)
curl http://localhost:8000/admin/stats -H "X-Admin-ID: invalid"
# Should return 403 (not authorized)

# Test rate limiting (SEC-005)
for i in {1..15}; do
    curl http://localhost:8000/practice/1/hint -H "X-Student-ID: 1"
    sleep 0.1
done
# 15th request should return 429

# Test log sanitization (SEC-006)
grep -i "api_key\|token\|admin_id" logs/
# Should find NO plain values (all ***MASKED***)

# Test input validation (SEC-007)
curl -X POST http://localhost:8000/practice/1/answer \
  -H "X-Student-ID: 1" \
  -H "Content-Type: application/json" \
  -d "{\"student_answer\": \"$(python -c 'print("a"*1000)')\"}"
# Should return 422 (validation error)

# Test query validation (SEC-008)
curl http://localhost:8000/admin/students?page=999999
# Should accept but cap at 1000
```

### Testing & Code Review [PHASE1-C-1.9]

- [ ] Run complete security test plan (see curl commands above)
- [ ] Verify all 8 security requirements implemented
- [ ] Code review with Jodha (FastAPI expert)
- [ ] Verify no performance regressions
- [ ] Document any deviations from SECURITY_ROADMAP_INTEGRATION.md

### Code Review Checklist (Jodha will verify)

- [ ] No `allow_origins=["*"]` (must be specific domains)
- [ ] All student endpoints call database verification
- [ ] All admin endpoints use `Depends(verify_admin)`
- [ ] Telegram webhook verifies `X-Telegram-Bot-Api-Secret-Token`
- [ ] Rate limiting middleware installed and tested
- [ ] No API keys/tokens/IDs in JSON logs (all masked)
- [ ] All string inputs have `max_length` (prevent DOS)
- [ ] Query parameters have reasonable bounds
- [ ] Error responses never expose stack traces
- [ ] All unit + integration tests pass
- [ ] Type hints on all security functions
- [ ] Documentation updated with security patterns

### Success Criteria

- ✅ SEC-001: CORS restricted to specific origins
- ✅ SEC-002: Telegram webhook verifies signature
- ✅ SEC-003: Student database verification working
- ✅ SEC-004: Admin auth enforced on all routes
- ✅ SEC-005: Rate limiting active and tested
- ✅ SEC-006: Sensitive data masked in logs
- ✅ SEC-007: Input length validation on all strings
- ✅ SEC-008: Query parameter validation with bounds
- ✅ No hardcoded secrets
- ✅ All tests passing (70%+ coverage)
- ✅ Security test plan passes
- ✅ Code review from Jodha completed

---

## Phase 1 Success Criteria (All Agents)

### Learning Objectives

- ✅ SQLAlchemy models with proper relationships
- ✅ FastAPI endpoints with proper error handling
- ✅ Telegram integration with signature verification
- ✅ All 8 security requirements implemented

### Code Quality

- ✅ All code has type hints (mypy strict)
- ✅ All tests pass (unit + integration)
- ✅ Coverage ≥70% overall
- ✅ No hardcoded secrets
- ✅ No stack traces in error responses
- ✅ Black formatting + Ruff linting

### Security

- ✅ All 8 SEC-* requirements complete
- ✅ Code review completed
- ✅ Security test plan passes
- ✅ No sensitive data in logs

### DevOps

- ✅ Database migrations work
- ✅ App starts without errors
- ✅ Health endpoint responds
- ✅ Webhook endpoint receives updates
- ✅ Pre-commit hooks pass

---

## Hand-off to Phase 2

**Database is ready, API endpoints exist, Telegram webhook ready to receive messages**

- ✅ Agent A delivered: Database with migrations and seed data
- ✅ Agent B delivered: FastAPI app with all route stubs
- ✅ Agent C delivered: All security requirements implemented

**Phase 2 can begin:** Content curation (parallel with Phase 1)
**Phase 3 can begin:** All 8 security requirements MUST be complete first

---

## Timeline

| Day | Agent A (Maryam) | Agent B (Jodha) | Agent C (Noor) |
|-----|------------------|-----------------|----------------|
| 1 | Design schema | Setup FastAPI | Plan security work |
| 2 | Create models + migrations | Create routes | Implement SEC-001, SEC-002 |
| 3 | Testing + finalize | Testing + finalize | Implement SEC-003 through SEC-005 |
| 4 | - | - | Implement SEC-006 through SEC-008 |
| 5 | - | - | Test + code review |

---

## Notes

- **Agents work in PARALLEL** (not sequential)
- Agent A's models are needed by Agent B (imports) → Agent A starts first
- Agent C can start anytime, but code review must complete before Phase 3
- All work must pass validation pipeline before committing
- Security work (Agent C) is BLOCKING for Phase 3 → DO NOT skip
- All agents follow AGENT_CHECKLIST.md workflow

---

## References

- `AGENT_ROADMAP.md` - Phase 1 full description
- `SECURITY_ROADMAP_INTEGRATION.md` - Security requirements details
- `AGENT_CHECKLIST.md` - Development workflow
- `openspec/agents/maryam.md` - Maryam's guidelines
- `openspec/agents/jodha.md` - Jodha's guidelines
- `openspec/agents/noor.md` - Noor's security guidelines
- `CLAUDE.md` - Project conventions and standards
