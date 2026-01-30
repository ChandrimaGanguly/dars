# Autonomous Agent Development Checklist

This checklist is for autonomous agents working on the Dars codebase. Follow it to ensure your code passes all quality gates.

## Pre-Development Setup (One-Time)

- [ ] **Clone repo and navigate to project:**
  ```bash
  cd /home/gangucham/whatsappAItutor
  ```

- [ ] **Install dependencies:**
  ```bash
  pip install -e ".[dev]"
  ```

- [ ] **Install Git hooks:**
  ```bash
  bash scripts/install-git-hooks.sh
  ```

- [ ] **Verify setup:**
  ```bash
  bash scripts/validate.sh
  ```
  Expected: All 7 stages pass (or show as "skipped" if src/ doesn't exist yet)

---

## Per-Task Workflow

### 1. Start New Task

- [ ] **Read task description:**
  ```bash
  # From tasks/ directory files
  cat tasks/backend.md | grep "TASK-XXX" -A 5
  ```

- [ ] **Check task dependencies:**
  - Is it blocked by another task?
  - If yes, don't start yet
  - If no, proceed

- [ ] **Create feature branch:**
  ```bash
  git checkout -b feature/TASK-XXX-description
  ```

---

### 2. While Coding

- [ ] **Write code with type hints:**
  ```python
  # GOOD: Type hints on all parameters and return
  def calculate_streak(student_id: int, sessions: list[Session]) -> int:
      """Calculate current streak."""
      return len(sessions)

  # BAD: No type hints
  def calculate_streak(student_id, sessions):
      return len(sessions)
  ```

- [ ] **Write tests as you code:**
  ```python
  # tests/unit/test_streaks.py
  def test_streak_increments() -> None:
      """Should increment on consecutive days."""
      assert True  # Implement real test
  ```

- [ ] **Keep functions small:**
  - Aim for <20 lines per function
  - One responsibility per function
  - Easier to test

- [ ] **Run validation frequently:**
  ```bash
  bash scripts/validate.sh --skip-slow
  ```

- [ ] **Auto-fix formatting/linting issues:**
  ```bash
  bash scripts/validate.sh --fix
  ```

---

### 3. Before Committing

- [ ] **Run full validation:**
  ```bash
  bash scripts/validate.sh
  ```

- [ ] **Verify all stages pass:**
  - ✓ Code formatting (Black)
  - ✓ Linting (Ruff)
  - ✓ Type checking (MyPy)
  - ✓ Unit tests
  - ✓ Integration tests (if applicable)
  - ✓ Coverage ≥70%
  - ✓ Git status clean

- [ ] **Security Code Quality (For Phase 1 Security Work):**
  If you're working on security requirements (SEC-001 through SEC-008):
  - [ ] No hardcoded secrets (API keys, tokens, passwords)
  - [ ] No sensitive data logged (use `sanitize_log_data()`)
  - [ ] All inputs validated (max_length on strings, bounds on numbers)
  - [ ] All security functions have type hints
  - [ ] CORS, auth, rate limiting not using wildcards/permissive defaults
  - [ ] Error responses don't expose stack traces
  - [ ] Database queries use parameterized statements
  - [ ] See: `/home/gangucham/whatsappAItutor/SECURITY_ROADMAP_INTEGRATION.md` for checklist

- [ ] **If validation fails:**
  ```bash
  # Auto-fix what we can
  bash scripts/validate.sh --fix

  # Fix type errors manually
  mypy src

  # Fix test failures
  pytest tests/unit -v

  # Re-run validation
  bash scripts/validate.sh
  ```

- [ ] **Stage all changes:**
  ```bash
  git add .
  ```

- [ ] **Commit with descriptive message:**
  ```bash
  git commit -m "feat: add streak tracking system"
  # or
  git commit -m "fix: handle edge case in problem selector"
  ```

- [ ] **Let pre-commit hook run:**
  - It automatically runs all checks
  - Should pass (since you just ran validation)
  - Commit succeeds

---

### 4. After Committing

- [ ] **Push to feature branch:**
  ```bash
  git push origin feature/TASK-XXX-description
  ```

- [ ] **Create pull request:**
  - Link to task/issue
  - Describe what changed
  - Note any design decisions

- [ ] **Wait for CI/CD to pass:**
  - GitHub Actions runs validation
  - Must pass all checks
  - Coverage report updates

- [ ] **Merge to main when approved:**
  ```bash
  # Via GitHub UI (recommended)
  # All checks must pass first
  ```

---

## Phase 1 Security Work (Agent C - Noor)

**CRITICAL: These 8 security requirements MUST be completed before Phase 3 begins.**

See: `AGENT_ROADMAP.md` → "PHASE 1: Backend & Integration Foundation" → "Critical Subtasks for Agent C"

### SEC-001: CORS Hardening

- [ ] **Before:** `allow_origins=["*"]` (allows all)
- [ ] **After:** `allow_origins=["https://dars.railway.app", "http://localhost:3000"]`
- [ ] **Test:** `curl -H "Origin: https://evil.com" http://localhost:8000/health` → No CORS header

### SEC-002: Telegram Webhook Verification

- [ ] **Add header check:** Verify `X-Telegram-Bot-Api-Secret-Token` matches configured token
- [ ] **Reject unsigned:** Return 401 Unauthorized if header missing or invalid
- [ ] **Test:** Send webhook without header → 401 response

### SEC-003: Student Database Verification

- [ ] **Query database:** Check student exists before returning data
- [ ] **Return 404 if not found:** Don't expose whether ID is valid
- [ ] **Applied to:** `GET /practice`, `POST /answer`, `POST /hint`, `GET /streak`, `PATCH /profile`
- [ ] **Test:** `curl http://localhost:8000/practice -H "X-Student-ID: 99999"` → 404

### SEC-004: Admin Authentication Enforcement

- [ ] **Use Depends():** `admin_id: int = Depends(verify_admin)` on all `/admin/*` endpoints
- [ ] **All admin routes protected:** `/admin/stats`, `/admin/students`, `/admin/cost`
- [ ] **Return 403 if unauthorized:** Reject invalid admin IDs
- [ ] **Test:** `curl http://localhost:8000/admin/stats -H "X-Admin-ID: invalid"` → 403

### SEC-005: Rate Limiting

- [ ] **Install slowapi:** `pip install slowapi`
- [ ] **Global limit:** 100 requests/minute per IP
- [ ] **Per-endpoint limit:** `/hint` max 10/day per student
- [ ] **Return 429:** Too Many Requests when limit exceeded
- [ ] **Test:** Send 15 hint requests rapidly → 15th returns 429

### SEC-006: Sensitive Data Sanitization in Logs

- [ ] **Mask API keys:** Replace with `***MASKED***`
- [ ] **Mask tokens:** Replace with `***MASKED***`
- [ ] **Mask admin IDs:** Replace with `***MASKED***`
- [ ] **Apply to all logs:** Use `sanitize_log_data()` function
- [ ] **Test:** `grep -i "api_key\|token\|admin_id" logs/` → No plain values found

### SEC-007: Input Length Validation

- [ ] **Add max_length to strings:** `student_answer: str = Field(..., max_length=500)`
- [ ] **Applied to:** All string inputs (answer, feedback, messages)
- [ ] **Prevent DOS:** Reject huge payloads
- [ ] **Test:** Submit 10MB payload → 413 Payload Too Large

### SEC-008: Query Parameter Validation

- [ ] **Add bounds:** `page: int = Query(1, ge=1, le=1000)`
- [ ] **Validate grade:** `ge=6, le=8`
- [ ] **Validate limit:** `ge=1, le=100`
- [ ] **Test:** `curl http://localhost:8000/admin/students?page=999999` → Works but bounded

### Security Code Review Checklist

Before merging your security work, verify:

- [ ] No `allow_origins=["*"]` (must be specific domains)
- [ ] All student endpoints call database verification
- [ ] All admin endpoints use `Depends(verify_admin)`
- [ ] Telegram webhook verifies signature header
- [ ] Rate limiting middleware installed and tested
- [ ] No API keys/tokens/IDs in JSON logs
- [ ] All string inputs have `max_length` (prevent DOS)
- [ ] Query parameters have reasonable bounds
- [ ] Error responses never show stack traces
- [ ] All unit + integration tests pass
- [ ] Security code review completed by Jodha

---

## Agent Role Checklists

### For Jodha (FastAPI Backend Expert)

**Phase 1 Work:**
- [ ] Build FastAPI app structure with all endpoints
- [ ] Implement core error handling framework
- [ ] Set up CORS middleware (will be hardened by Noor)
- [ ] Implement core authentication dependencies (will be enhanced by Noor)
- [ ] Code review all security work from Noor before merge

**Validation:**
- [ ] All endpoints have type hints
- [ ] All responses use Pydantic schemas
- [ ] Error handling doesn't crash app
- [ ] All tests pass with 70%+ coverage

### For Noor (Security & Logging Expert)

**Phase 1 Work (BLOCKING FOR PHASE 3):**
- [ ] Implement SEC-001 through SEC-008 security requirements
- [ ] Add rate limiting middleware
- [ ] Add log sanitization
- [ ] Implement security error handling
- [ ] Write security test plan
- [ ] Get code review from Jodha

**Phase 7 Work:**
- [ ] Enhance log sanitization with monitoring
- [ ] Test with real API keys to verify masking
- [ ] Document sensitive fields list

**Phase 8 Work:**
- [ ] Add security response headers (CSP, HSTS, etc.)
- [ ] Implement error response filtering

### For Maryam (Database & ORM Expert)

**Phase 1 Work:**
- [ ] Design database schema with indexes
- [ ] Create Alembic migrations
- [ ] Implement base models and relationships
- [ ] Seed initial data

**Security Considerations:**
- [ ] Verify student existence queries are indexed (`idx_students_telegram_id`)
- [ ] Verify all queries use SQLAlchemy ORM (no raw SQL)
- [ ] Connection pooling configured (`pool_pre_ping=True`)

### For any Agent working on Learning Features (Phases 3+)

**Must Wait For:**
- [ ] Phase 1 security to be 100% complete
- [ ] SEC-003 (student database verification) verified
- [ ] Practice endpoints can only be called by verified students

---

## Validation Commands Cheatsheet

### Before You Code

```bash
# Verify pipeline is working
bash scripts/validate.sh
```

### While Coding (Frequent)

```bash
# Fast validation (skip slow integration tests)
bash scripts/validate.sh --skip-slow
```

### Before Committing (Every Time)

```bash
# Full validation
bash scripts/validate.sh

# Auto-fix formatting and linting
bash scripts/validate.sh --fix

# See what's broken
bash scripts/validate.sh -v
```

### If Something Fails

```bash
# See detailed type errors
mypy src

# See failing tests with details
pytest tests/unit -v

# See coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Run specific test
pytest tests/unit/test_streaks.py::TestStreakCalculation::test_increment -v
```

---

## Code Quality Standards

### Type Hints (REQUIRED)

❌ **BAD:**
```python
def process_answer(student_id, answer, problem):
    result = evaluate(answer)
    return result
```

✅ **GOOD:**
```python
def process_answer(
    student_id: int,
    answer: str,
    problem: Problem
) -> bool:
    """Check if answer is correct."""
    result = evaluate(answer)
    return result
```

### Tests (REQUIRED)

❌ **BAD:**
```python
# No tests for new function
def calculate_streak(sessions):
    ...
```

✅ **GOOD:**
```python
# tests/unit/test_streaks.py
@pytest.mark.unit
class TestStreakCalculation:
    def test_increments_on_consecutive_days(self) -> None:
        """Should increment when student practices daily."""
        streak = Streak(user_id=1)
        streak.record_practice(date(2024, 1, 1))
        streak.record_practice(date(2024, 1, 2))
        assert streak.current == 2

    def test_resets_on_missed_day(self) -> None:
        """Should reset when student misses a day."""
        ...
```

### Code Style (ENFORCED)

- Line length: ≤100 chars
- Quotes: Double quotes for strings
- Imports: Sorted alphabetically
- Spacing: PEP 8 standard

These are auto-fixed by:
```bash
bash scripts/validate.sh --fix
```

### Test Coverage (ENFORCED)

- Overall: ≥70%
- Core modules: ≥80%
- Every public function should have at least one test

Check coverage:
```bash
pytest --cov=src --cov-report=html
```

---

## Git Workflow

### Feature Branch Naming

```
feature/TASK-001-description    ← New feature
fix/TASK-002-description        ← Bug fix
docs/TASK-003-description       ← Documentation
refactor/TASK-004-description   ← Code refactoring
test/TASK-005-description       ← Tests only
```

### Commit Message Format

```
<type>: <description>

<optional body>

<optional footer>
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Code style (formatting)
- `refactor:` Code refactoring
- `test:` Tests
- `chore:` Build, dependencies, etc.

**Examples:**
```bash
git commit -m "feat: implement streak tracking system"
git commit -m "fix: handle edge case in problem selector"
git commit -m "test: add unit tests for streak calculation"
git commit -m "docs: update API documentation"
```

---

## Troubleshooting

### "validation.sh: Permission denied"

```bash
chmod +x scripts/validate.sh
bash scripts/validate.sh
```

### "ModuleNotFoundError: No module named 'src'"

This is expected if `src/` doesn't exist yet (Phase 1 hasn't been implemented).
The validation script will skip checks that depend on it.

### "MyPy: error: [import]: Cannot find implementation"

This means a module isn't installed. Run:
```bash
pip install -e ".[dev]"
```

### "Pre-commit hook blocks my commit"

```bash
# Check what failed
bash scripts/validate.sh -v

# Fix issues
bash scripts/validate.sh --fix
mypy src
pytest tests/unit -v

# Stage and retry
git add .
git commit
```

### "I need to bypass validation (EMERGENCY ONLY)"

```bash
git commit --no-verify

# But you MUST run validation afterwards:
bash scripts/validate.sh --verbose
```

---

## Quick Reference

| Goal | Command |
|------|---------|
| Validate before committing | `bash scripts/validate.sh` |
| Auto-fix formatting/linting | `bash scripts/validate.sh --fix` |
| Fast validation (no slow tests) | `bash scripts/validate.sh --skip-slow` |
| See what's broken | `bash scripts/validate.sh -v` |
| Check type errors | `mypy src` |
| Run unit tests | `pytest tests/unit -v` |
| Check coverage | `pytest --cov=src --cov-report=html` |
| Run specific test | `pytest tests/unit/test_file.py::TestClass::test_method -v` |

---

## Summary

**The E2E Validation Pipeline protects you by:**

1. ✅ **Preventing bad code:** Catches bugs before they become problems
2. ✅ **Enforcing standards:** Consistent style across the codebase
3. ✅ **Ensuring tests:** Minimum coverage requirement
4. ✅ **Type safety:** Catches type errors before runtime
5. ✅ **Safe commits:** No sensitive files accidentally committed

**Your job as an agent:**

1. Write code with type hints
2. Write tests as you code
3. Run `bash scripts/validate.sh` before committing
4. Fix any issues it reports
5. Commit when green

**That's it.** The validation pipeline does the rest.

---

## Need Help?

- Read: `VALIDATION_PIPELINE.md` (detailed documentation)
- Read: `TESTING.md` (testing guide)
- Read: `AGENT_ROADMAP.md` (8-week implementation plan)
- Read: `SECURITY_ROADMAP_INTEGRATION.md` (security audit findings and roadmap)
- Read: `openspec/agents/noor.md` (Noor's security guidelines)
- Check: `tasks/` (see what needs to be done)
- Review: `.github/workflows/validation.yml` (CI/CD pipeline)

**For Security Questions:**
- See: `SECURITY_ROADMAP_INTEGRATION.md` (complete security roadmap)
- See: `AGENT_ROADMAP.md` → "PHASE 1" → "Critical Subtasks for Agent C"
- See: Security Code Review Checklist (this document)
