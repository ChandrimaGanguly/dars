# PHASE1-C-1: Security Hardening

**Owner:** Noor (Security & Logging Expert)
**Duration:** ~2-3 days (independent, can run parallel)
**Status:** Ready to start
**GitHub Issue:** #7
**⚠️ CRITICAL:** BLOCKS Phase 3 - must be 100% complete before practice endpoints go live

---

## Task Summary

| Subtask | Security ID | Description | Status | Assignee |
|---------|-------------|-------------|--------|----------|
| PHASE1-C-1.1 | SEC-002 | Telegram webhook signature verification | 📋 Ready | Noor |
| PHASE1-C-1.2 | SEC-001 | CORS hardening | 📋 Ready | Noor |
| PHASE1-C-1.3 | SEC-003 | Student database verification (CRITICAL) | 📋 Ready | Noor |
| PHASE1-C-1.4 | SEC-004 | Admin authentication enforcement | 📋 Ready | Noor |
| PHASE1-C-1.5 | SEC-005 | Rate limiting | 📋 Ready | Noor |
| PHASE1-C-1.6 | SEC-006 | Log sanitization | 📋 Blocked | Noor |
| PHASE1-C-1.7 | SEC-007 | Input validation | 📋 Ready | Noor |
| PHASE1-C-1.8 | SEC-008 | Query validation | 📋 Ready | Noor |
| PHASE1-C-1.9 | Testing | Security testing & code review | 📋 Blocked | Noor + Jodha |

---

## Subtasks

### PHASE1-C-1.1: SEC-002 - Telegram Webhook Signature Verification

**Objective:** Verify Telegram webhook requests are authentic

**Implementation:**
- [ ] Add header validation in `src/routes/webhook.py`
  ```python
  @router.post("/webhook")
  async def telegram_webhook(request: Request):
      secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
      if not secret_token or secret_token != settings.telegram_secret_token:
          raise HTTPException(status_code=401, detail="Invalid webhook token")
      # ... process update
  ```

- [ ] Get Telegram secret token from BotFather
- [ ] Store in `TELEGRAM_SECRET_TOKEN` environment variable
- [ ] Never hardcode token

**Testing:**
- [ ] `curl -X POST /webhook` (no header) → 401 Unauthorized
- [ ] `curl -X POST /webhook -H "X-Telegram-Bot-Api-Secret-Token: wrong"` → 401
- [ ] `curl -X POST /webhook -H "X-Telegram-Bot-Api-Secret-Token: correct"` → 200

**Success Criteria:**
- ✅ Spoofed webhook requests rejected (401)
- ✅ Valid requests accepted
- ✅ No token in logs
- ✅ Error message doesn't reveal token format

---

### PHASE1-C-1.2: SEC-001 - CORS Hardening

**Objective:** Restrict CORS to specific domains (not *)

**Implementation:**
- [ ] Update `src/main.py` CORS middleware
  ```python
  from fastapi.middleware.cors import CORSMiddleware

  app.add_middleware(
      CORSMiddleware,
      allow_origins=[
          "https://dars.railway.app",
          "http://localhost:3000"
      ],
      allow_credentials=True,
      allow_methods=["GET", "POST", "PATCH"],
      allow_headers=[
          "Content-Type",
          "Authorization",
          "X-Student-ID",
          "X-Admin-ID"
      ],
  )
  ```

- [ ] Document rationale for each origin
- [ ] Add comment about how to configure for different deployment

**Testing:**
- [ ] `curl -H "Origin: https://dars.railway.app" http://localhost:8000/health` → Includes CORS headers
- [ ] `curl -H "Origin: https://evil.com" http://localhost:8000/health` → No CORS headers
- [ ] Test with localhost:3000 for development

**Success Criteria:**
- ✅ CORS headers only for allowed origins
- ✅ Wildcard * is removed
- ✅ Requests from evil.com rejected
- ✅ Requests from dars.railway.app accepted

---

### PHASE1-C-1.3: SEC-003 - Student Database Verification [CRITICAL - BLOCKS PHASE 3]

**Objective:** Prevent IDOR attacks by verifying student exists in database

**Implementation (Applied to all student endpoints):**
- [ ] Create `verify_student_exists()` dependency in `src/auth/student.py`
  ```python
  async def verify_student_exists(
      student_id: int = Header(..., alias="X-Student-ID"),
      session: AsyncSession = Depends(get_db_session)
  ) -> Student:
      result = await session.execute(
          select(Student).where(Student.student_id == student_id)
      )
      student = result.scalar_one_or_none()
      if not student:
          raise HTTPException(status_code=404, detail="Student not found")
      return student
  ```

- [ ] Add to endpoints:
  - `GET /practice`
  - `POST /practice/{problem_id}/answer`
  - `POST /practice/{problem_id}/hint`
  - `GET /streak`
  - `PATCH /student/profile`

**Testing:**
- [ ] `curl http://localhost:8000/practice -H "X-Student-ID: 99999"` → 404
- [ ] Valid student ID → 200 with data

**Success Criteria:**
- ✅ Non-existent students get 404 (not 200)
- ✅ No data leakage about which IDs exist
- ✅ Valid students can access their data
- ✅ Students cannot access other students' data

**IMPORTANT:** This is the critical blocker for Phase 3. Must be 100% complete.

---

### PHASE1-C-1.4: SEC-004 - Admin Authentication Enforcement

**Objective:** Verify admin requests come from authorized IDs

**Implementation:**
- [ ] Create `verify_admin()` dependency in `src/auth/admin.py`
  ```python
  async def verify_admin(
      admin_id: int = Header(..., alias="X-Admin-ID")
  ) -> int:
      if admin_id not in settings.admin_ids:  # e.g., [123456, 789012]
          raise HTTPException(status_code=403, detail="Unauthorized")
      return admin_id
  ```

- [ ] Add `ADMIN_IDS` to environment config (comma-separated list)
- [ ] Add to endpoints:
  - `GET /admin/stats`
  - `GET /admin/students`
  - `GET /admin/cost`

**Testing:**
- [ ] `curl http://localhost:8000/admin/stats -H "X-Admin-ID: invalid"` → 403
- [ ] `curl http://localhost:8000/admin/stats -H "X-Admin-ID: 123456"` → 200

**Success Criteria:**
- ✅ Unauthorized admin IDs get 403
- ✅ Valid admin IDs can access stats
- ✅ No admin IDs hardcoded in code (use env vars)

---

### PHASE1-C-1.5: SEC-005 - Rate Limiting

**Objective:** Prevent DOS attacks with rate limiting

**Implementation:**
- [ ] Install slowapi: `pip install slowapi`
- [ ] Add to FastAPI app in `src/main.py`
  ```python
  from slowapi import Limiter
  from slowapi.util import get_remote_address

  limiter = Limiter(key_func=get_remote_address)
  app.state.limiter = limiter
  ```

- [ ] Global limit: 100 requests/minute per IP
  ```python
  @app.get("/")
  @limiter.limit("100/minute")
  def root(request: Request):
      return {"name": "Dars"}
  ```

- [ ] Per-endpoint limit: `/hint` max 10/day per student
  ```python
  @router.post("/practice/{problem_id}/hint")
  @limiter.limit("10/day")
  async def request_hint(request: Request, ...):
      ...
  ```

**Testing:**
- [ ] Send 15 rapid requests to `/hint` → 15th returns 429
- [ ] 429 response includes `Retry-After` header
- [ ] After 1 minute, can send another request

**Success Criteria:**
- ✅ Rate limits enforced
- ✅ Returns 429 Too Many Requests when limit exceeded
- ✅ Limits per IP and per student
- ✅ No bypass for admin users (configure separately if needed)

---

### PHASE1-C-1.6: SEC-006 - Sensitive Data Sanitization in Logs

**Objective:** Mask API keys, tokens, and admin IDs in logs

**Implementation:**
- [ ] Create `sanitize_log_data()` function in `src/logging.py`
  ```python
  def sanitize_log_data(data: dict) -> dict:
      """Mask sensitive fields in log data."""
      sensitive_fields = ["api_key", "token", "admin_id", "password"]
      sanitized = data.copy()
      for field in sensitive_fields:
          if field in sanitized:
              sanitized[field] = "***MASKED***"
      return sanitized
  ```

- [ ] Apply to all logging statements
  ```python
  logger.info("User action", extra=sanitize_log_data({
      "admin_id": request.headers.get("X-Admin-ID"),
      "action": "view_stats"
  }))
  ```

- [ ] Add JSON log formatter that sanitizes
- [ ] Review all error messages (no secrets in exceptions)

**Testing:**
- [ ] `grep -i "api_key\|token\|admin_id" logs/` → No plain values
- [ ] Check application logs → All sensitive data masked

**Success Criteria:**
- ✅ No API keys in logs
- ✅ No tokens in logs
- ✅ No admin IDs in logs
- ✅ Error messages sanitized

**Depends on:** PHASE1-B-1 (complete API needed for testing)

---

### PHASE1-C-1.7: SEC-007 - Input Length Validation

**Objective:** Prevent DOS attacks via huge payloads

**Implementation:**
- [ ] Add `max_length` to all string Pydantic fields
  ```python
  class StudentAnswer(BaseModel):
      student_answer: str = Field(..., max_length=500)
      problem_id: int
  ```

- [ ] Applied to all request schemas:
  - Student answers (max 500 chars)
  - Student names (max 100 chars)
  - Feedback messages (max 1000 chars)
  - Any user-provided string

**Testing:**
- [ ] Submit 10MB payload → 413 Payload Too Large
- [ ] Submit 500-char answer → 200 OK
- [ ] Submit 501-char answer → 422 Validation Error

**Success Criteria:**
- ✅ All string inputs have max_length
- ✅ Oversized payloads rejected with 413
- ✅ Valid sizes accepted

---

### PHASE1-C-1.8: SEC-008 - Query Parameter Validation

**Objective:** Validate and bound query parameters

**Implementation:**
- [ ] Add bounds to all query parameters
  ```python
  @router.get("/admin/students")
  async def list_students(
      page: int = Query(1, ge=1, le=1000),
      limit: int = Query(10, ge=1, le=100)
  ):
      ...
  ```

- [ ] Validate grade parameter (6-8 only)
  ```python
  @router.get("/practice")
  async def get_practice(
      grade: int = Query(..., ge=6, le=8)
  ):
      ...
  ```

- [ ] Validate all numeric parameters have reasonable bounds

**Testing:**
- [ ] `curl http://localhost:8000/admin/students?page=999999` → Works (bounded to 1000)
- [ ] `curl http://localhost:8000/admin/students?page=0` → 422 (must be ≥1)
- [ ] `curl http://localhost:8000/practice?grade=9` → 422 (must be 6-8)

**Success Criteria:**
- ✅ All query params have bounds (ge, le)
- ✅ Invalid values return 422
- ✅ Out-of-bounds values are capped or rejected

---

### PHASE1-C-1.9: Security Testing & Code Review

**Objective:** Verify all 8 security requirements working correctly

**Security Test Plan:**

✅ **CORS Testing**
```bash
# Should reject evil.com
curl -H "Origin: https://evil.com" http://localhost:8000/health
# Should accept dars.railway.app
curl -H "Origin: https://dars.railway.app" http://localhost:8000/health
```

✅ **Telegram Verification Testing**
```bash
# Should reject no header
curl -X POST http://localhost:8000/webhook
# Should accept valid token
curl -X POST http://localhost:8000/webhook \
  -H "X-Telegram-Bot-Api-Secret-Token: $TOKEN"
```

✅ **Student Verification Testing**
```bash
# Should reject invalid student
curl http://localhost:8000/practice -H "X-Student-ID: 99999"
# Should accept valid student
curl http://localhost:8000/practice -H "X-Student-ID: 1"
```

✅ **Admin Auth Testing**
```bash
# Should reject invalid admin
curl http://localhost:8000/admin/stats -H "X-Admin-ID: invalid"
# Should accept valid admin
curl http://localhost:8000/admin/stats -H "X-Admin-ID: 123456"
```

✅ **Rate Limiting Testing**
```bash
# Send 15 requests rapidly to /hint
for i in {1..15}; do curl http://localhost:8000/practice/1/hint; done
# 15th should return 429
```

✅ **Log Sanitization Testing**
```bash
# Check logs contain no secrets
grep -i "api_key\|token\|admin_id" logs/
# Should find NO plain values
```

✅ **Input Validation Testing**
```bash
# Submit oversized payload
curl -X POST http://localhost:8000/practice/1/answer \
  -H "Content-Type: application/json" \
  -d '{"student_answer": "'$(python -c 'print("a"*1000))''"}'
# Should return 422 or 413
```

✅ **Query Validation Testing**
```bash
# Test page bounds
curl http://localhost:8000/admin/students?page=999999
# Should work but bounded
curl http://localhost:8000/admin/students?page=0
# Should return 422
```

**Code Review with Jodha:**
- [ ] Review all security implementations
- [ ] Verify no breaking changes to API
- [ ] Run full test suite
- [ ] Check for performance regressions
- [ ] Verify error responses don't leak info
- [ ] Sign off on all 8 requirements

**Documentation:**
- [ ] Document all security headers required
- [ ] Document rate limit values
- [ ] Document admin ID configuration
- [ ] Update CLAUDE.md with security patterns

---

## Success Criteria (Whole Task)

- ✅ SEC-001: CORS restricted to specific domains (no wildcard)
- ✅ SEC-002: Telegram webhook verifies signature header
- ✅ SEC-003: All student endpoints verify in database
- ✅ SEC-004: All admin endpoints require authentication
- ✅ SEC-005: Rate limiting enforced (100 req/min global, 10 hints/day)
- ✅ SEC-006: No secrets in logs (all masked)
- ✅ SEC-007: All string inputs have max_length
- ✅ SEC-008: Query parameters have bounds
- ✅ No stack traces in error responses
- ✅ All unit + integration tests pass
- ✅ Code reviewed by Jodha
- ✅ Security test plan passes
- ✅ 100% complete (BLOCKS Phase 3)

---

## Code Review Checklist (Self-Review)

- [ ] No hardcoded secrets (API keys, tokens, admin IDs)
- [ ] All security functions have type hints
- [ ] Error messages don't expose sensitive info
- [ ] CORS configuration is restrictive (not `*`)
- [ ] Database verification prevents IDOR
- [ ] Admin auth on all admin endpoints
- [ ] Rate limiting doesn't break legitimate usage
- [ ] Logs contain no plain secrets
- [ ] Input validation prevents DOS
- [ ] Query bounds prevent overflow
- [ ] Error responses consistent format
- [ ] All tests passing
- [ ] No performance degradation
- [ ] Clear comments on security decisions

---

## References

- **PHASE1_TASKS.md** - Section 3 (Agent C: Security) for detailed specs
- **SECURITY_ROADMAP_INTEGRATION.md** - Security audit findings & mappings
- **AGENT_CHECKLIST.md** - Phase 1 Security Work checklist
- **CLAUDE.md** - Critical Implementation Details → Telegram Integration, Claude Cost Control
- **slowapi Docs** - Rate limiting library
- **OWASP Top 10** - Security best practices

---

## Dependencies

- ✅ **No upstream blocking** (can start immediately)
- ⏳ **Depends on:** PHASE1-B-1 (needs complete API for SEC-006 logging and testing)
- ✅ **Blocks:** Phase 3 - MUST be 100% complete before practice endpoints go live

---

## Critical Path Note

This task is on the **critical path**. Phase 3 (Week 2-3) cannot begin until:
1. All 8 security requirements implemented
2. Code reviewed by Jodha
3. All tests passing
4. Security test plan passes
5. SEC-003 (student verification) explicitly verified

---

## Timeline

| Day | Subtask | Deliverable |
|-----|---------|------------|
| 1 | PHASE1-C-1.1, PHASE1-C-1.2 | Telegram verification + CORS hardening |
| 1 | PHASE1-C-1.7, PHASE1-C-1.8 | Input/query validation |
| 2 | PHASE1-C-1.3, PHASE1-C-1.4, PHASE1-C-1.5 | Student/admin auth + rate limiting |
| 2 | PHASE1-C-1.6 | Log sanitization (needs complete API) |
| 3 | PHASE1-C-1.9 | Security testing & code review |

**Total Duration:** ~2-3 days

---

**Status:** 📋 Ready to start (independent)
**Last Updated:** 2026-01-30
**GitHub Issue:** #7
**BLOCKING:** Phase 3 (CRITICAL - must be 100% complete before practice endpoints go live)
