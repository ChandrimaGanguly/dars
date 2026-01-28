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
- Check: `tasks/` (see what needs to be done)
- Review: `.github/workflows/validation.yml` (CI/CD pipeline)
